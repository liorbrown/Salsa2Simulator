"""Passive packet-capture based Inter-Node Traffic measurement.

Rather than instrumenting Squid or adding custom response headers, this
module measures proxy-to-parent traffic (ICP queries/replies + the HTTP
"datum" fetch to the winning parent) by passively capturing the wire
traffic with tcpdump and attributing it back to individual requests.

Requests execute strictly sequentially (see simulation/trace_runner.py),
so a single long-lived tcpdump process per run - rotating output files
periodically - is enough: each request's [t_start, t_end] wall-clock
window never overlaps another request's, so packets can be attributed by
window membership. Within a window, only traffic that positively matches
that request's URL is counted (ICP messages and HTTP request lines both
carry the URL in plaintext) - this is a whitelist, not a blacklist, so it
naturally excludes background cache-digest fetches and any unrelated
traffic from another process sharing the same proxy, without needing to
enumerate everything that isn't wanted.
"""
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import dpkt

from config.config import MyConfig
from database.db_access import DBAccess
from cache.registry import get_all_caches, get_icp_port

ROTATE_SECONDS = 30
LISTEN_TIMEOUT_SEC = 5
STOP_TIMEOUT_SEC = 5

# ICP_QUERY opcode value, per squid's icp_opcode enum (src/icp_opcode.h):
# ICP_INVALID=0, ICP_QUERY=1, ICP_HIT=2, ICP_MISS=3, ... - it's the first
# byte of every ICP message's payload.
ICP_OPCODE_QUERY = 1


class CaptureError(Exception):
    """Raised when the capture session can't be trusted to keep measuring:
    tcpdump couldn't start, or died unexpectedly mid-run."""


def get_parent_targets() -> Tuple[List[str], int, int]:
    """Return (parent_ips, http_port, icp_port) needed to scope a capture.

    All peers in this deployment share one http port; if the configured
    caches don't carry one (e.g. squid.conf is unusually formatted), fall
    back to this proxy's own squid_port. icp_port defaults to Squid's
    standard 3130 if squid.conf doesn't specify it.
    """
    caches = get_all_caches()
    parent_ips = [details['ip'] for details in caches.values() if details.get('ip')]

    http_ports = {details['http_port'] for details in caches.values() if details.get('http_port')}
    if http_ports:
        http_port = next(iter(http_ports))
    else:
        http_port = int(MyConfig().get_key('squid_port') or 3128)

    icp_port = get_icp_port() or 3130

    return parent_ips, http_port, icp_port


def _default_interface() -> str:
    """Best-effort detection of the outbound network interface, so we don't
    hardcode e.g. 'eth0'. Falls back to 'any' (Linux cooked capture) if
    detection fails - handled transparently by the datalink-aware parser
    below."""
    try:
        out = subprocess.check_output(
            ['ip', 'route', 'show', 'default'], text=True, stderr=subprocess.DEVNULL)
        match = re.search(r'\bdev\s+(\S+)', out)
        if match:
            return match.group(1)
    except Exception:
        pass
    return 'any'


def _build_filter(parent_ips: List[str], http_port: int, icp_port: int) -> str:
    if not parent_ips:
        return f'udp port {icp_port}'
    hosts = ' or '.join(f'host {ip}' for ip in parent_ips)
    return f'udp port {icp_port} or (tcp port {http_port} and ({hosts}))'


class _PendingRequest:
    """Accumulates traffic totals for one request while its capture window
    is still open (i.e. not all relevant pcap chunks have been drained)."""

    __slots__ = ('request_id', 'url', 't_start', 't_end', 'bytes_total', 'queries')

    def __init__(self, request_id: int, url: str, t_start: float, t_end: float):
        self.request_id = request_id
        self.url = url
        self.t_start = t_start
        self.t_end = t_end
        self.bytes_total = 0
        self.queries = 0


def _normalize_url(url: str) -> bytes:
    # Squid rewrites https:// to http:// for its own routing (see
    # request_executor.py's X-Originally-HTTPS trick), so compare on the
    # scheme-agnostic remainder to avoid false negatives.
    stripped = url.split('://', 1)[-1]
    return stripped.encode('utf-8', 'ignore')


def _flow_key(ip_pkt, tcp_pkt) -> tuple:
    """Canonical (direction-independent) identifier for a TCP flow."""
    a = (bytes(ip_pkt.src), tcp_pkt.sport)
    b = (bytes(ip_pkt.dst), tcp_pkt.dport)
    return tuple(sorted((a, b)))


class CaptureSession:
    """Brackets a whole run (or a single ad hoc request) with one long-lived
    tcpdump process, and attributes captured bytes back to individual
    requests via a wall-clock window + URL whitelist match."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._chunk_dir: Optional[str] = None
        self._chunk_prefix: Optional[str] = None
        self._icp_port: Optional[int] = None
        self._http_port: Optional[int] = None
        self._pending: List[_PendingRequest] = []
        self._seen_chunks = set()
        # Which pending request currently "owns" a given TCP flow, keyed by
        # _flow_key(); None means the flow was matched to a request line
        # that didn't belong to any pending request (e.g. a digest fetch,
        # or another process's traffic) and its bytes should be ignored.
        self._flow_owner: Dict[tuple, Optional[_PendingRequest]] = {}

    def start(self) -> None:
        parent_ips, http_port, icp_port = get_parent_targets()
        self._http_port = http_port
        self._icp_port = icp_port

        if shutil.which('tcpdump') is None:
            raise CaptureError("tcpdump not found on PATH - can't measure Inter-Node Traffic")

        iface = _default_interface()
        bpf_filter = _build_filter(parent_ips, http_port, icp_port)

        self._chunk_dir = tempfile.mkdtemp(prefix='salsa2_cap_')
        self._chunk_prefix = os.path.join(self._chunk_dir, 'chunk')

        cmd = [
            'tcpdump', '-i', iface, '-U', '--immediate-mode',
            '-w', f'{self._chunk_prefix}_%Y%m%d%H%M%S.pcap',
            '-G', str(ROTATE_SECONDS),
            bpf_filter,
        ]

        try:
            self._proc = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
        except OSError as e:
            raise CaptureError(f"Failed to start tcpdump: {e}")

        # Block until tcpdump confirms its capture socket is actually open,
        # so we don't race the very first packet of the first request.
        deadline = time.monotonic() + LISTEN_TIMEOUT_SEC
        listening = False
        while time.monotonic() < deadline:
            line = self._proc.stderr.readline()
            if not line:
                break
            if 'listening on' in line:
                listening = True
                break

        if not listening:
            self._kill_proc()
            raise CaptureError(
                "tcpdump did not start capturing (permissions? run once: "
                "sudo setcap cap_net_raw,cap_net_admin+eip $(which tcpdump))")

    def record_window(self, request_id: int, url: str, t_start: float, t_end: float) -> None:
        """Register a completed request's time window for later attribution."""
        self._pending.append(_PendingRequest(request_id, url, t_start, t_end))

    def _kill_proc(self) -> None:
        if not self._proc:
            return
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=STOP_TIMEOUT_SEC)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=STOP_TIMEOUT_SEC)

    def _closed_chunks(self, include_latest: bool) -> List[str]:
        """Chunk files tcpdump has finished writing. The newest one may
        still be open for writing, so it's skipped unless the capture
        process has already exited (include_latest=True, used by stop())."""
        if not self._chunk_dir or not os.path.isdir(self._chunk_dir):
            return []
        files = sorted(f for f in os.listdir(self._chunk_dir) if f.endswith('.pcap'))
        if include_latest:
            return files
        # Always withhold the newest file, even if it's the only one: for a
        # capture shorter than ROTATE_SECONDS (the common case - a single
        # request, or a short trace), that lone file is still actively being
        # written by tcpdump, and reading+deleting it out from under the
        # still-running process would silently lose whatever it hasn't
        # flushed yet. Nothing gets processed until either rotation produces
        # a second (now-closed) file, or stop() drains everything after
        # killing the process.
        return files[:-1]

    def _active_chunk_boundary(self) -> Optional[float]:
        """Wall-clock time the currently-active (still being written, not
        yet drained) chunk started. A safe lower bound: once a pending
        request's window ended before this, a rotation has definitely
        happened since, so anything relevant to it must already be in a
        chunk that's been (or is about to be) drained - it can never still
        be waiting in the untouched active chunk.

        This is deliberately chunk-granularity rather than comparing
        against the latest packet timestamp actually seen: a request's own
        t_end (captured in Python right after its HTTP call returns) can
        land a fraction of a millisecond after the last packet tcpdump had
        time to flush, even though nothing is actually missing - using the
        much coarser rotation boundary avoids that false negative.
        """
        if not self._chunk_dir or not os.path.isdir(self._chunk_dir):
            return None
        files = sorted(f for f in os.listdir(self._chunk_dir) if f.endswith('.pcap'))
        if not files:
            return None
        return self._parse_chunk_timestamp(files[-1])

    @staticmethod
    def _parse_chunk_timestamp(fname: str) -> Optional[float]:
        match = re.search(r'_(\d{14})\.pcap$', fname)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), '%Y%m%d%H%M%S').timestamp()
        except ValueError:
            return None

    def drain(self, include_latest: bool = False) -> None:
        """Process any pcap chunks that have finished rotating (or all of
        them, if include_latest=True, once the capture has stopped)."""
        if self._proc is not None and self._proc.poll() is not None and not include_latest:
            raise CaptureError("tcpdump exited unexpectedly during the run")

        for fname in self._closed_chunks(include_latest):
            if fname in self._seen_chunks:
                continue
            self._seen_chunks.add(fname)
            path = os.path.join(self._chunk_dir, fname)
            try:
                self._consume_chunk(path)
            except Exception as e:
                print(f"Warning: failed to parse capture chunk {fname}: {e}")
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _consume_chunk(self, path: str) -> None:
        with open(path, 'rb') as f:
            reader = dpkt.pcap.Reader(f)
            datalink = reader.datalink()
            for ts, buf in reader:
                self._attribute_packet(ts, buf, datalink)

    def _find_pending(self, ts: float) -> Optional[_PendingRequest]:
        for pending in self._pending:
            if pending.t_start <= ts <= pending.t_end:
                return pending
        return None

    def _attribute_packet(self, ts: float, buf: bytes, datalink: int) -> None:
        try:
            if datalink == dpkt.pcap.DLT_EN10MB:
                ip_pkt = dpkt.ethernet.Ethernet(buf).data
            elif datalink == dpkt.pcap.DLT_LINUX_SLL:
                ip_pkt = dpkt.sll.SLL(buf).data
            else:
                return
            if not isinstance(ip_pkt, dpkt.ip.IP):
                return
        except Exception:
            return

        proto = ip_pkt.data
        length = len(buf)

        if isinstance(proto, dpkt.udp.UDP):
            self._attribute_udp(ts, proto, length)
        elif isinstance(proto, dpkt.tcp.TCP):
            self._attribute_tcp(ts, ip_pkt, proto, length)

    def _attribute_udp(self, ts: float, udp: 'dpkt.udp.UDP', length: int) -> None:
        # Squid's ICP socket sends and receives on the same port (confirmed
        # against live traffic: every ICP packet, query or reply, shows
        # sport == dport == icp_port), so direction can't be told from ports
        # alone - only the opcode byte (first byte of the payload) tells a
        # query (ICP_QUERY, see squid's icp_opcode.h) from a reply.
        if udp.sport != self._icp_port and udp.dport != self._icp_port:
            return

        pending = self._find_pending(ts)
        if pending is None:
            return

        # ICP replies echo the same URL back, so both directions can be
        # matched directly against the payload.
        if _normalize_url(pending.url) not in udp.data:
            return

        pending.bytes_total += length
        if udp.data and udp.data[0] == ICP_OPCODE_QUERY:
            pending.queries += 1

    def _attribute_tcp(self, ts: float, ip_pkt, tcp: 'dpkt.tcp.TCP', length: int) -> None:
        if tcp.sport != self._http_port and tcp.dport != self._http_port:
            return

        flow_key = _flow_key(ip_pkt, tcp)
        payload = tcp.data

        # A fresh HTTP request line re-establishes (or re-assigns, on a
        # reused keep-alive connection) which request - if any - this flow
        # currently belongs to.
        if payload[:4] == b'GET ':
            pending = self._find_pending(ts)
            owner = None
            if pending is not None and _normalize_url(pending.url) in payload:
                owner = pending
            self._flow_owner[flow_key] = owner

        owner = self._flow_owner.get(flow_key)
        if owner is not None:
            owner.bytes_total += length

    def flush_resolved(self, final: bool = False) -> None:
        """Write back results for pending requests that are safe to
        finalize, and forget them.

        final=True (used by stop(), after a last drain(include_latest=True)
        with the capture process already dead) flushes every remaining
        pending request unconditionally - nothing more will ever be
        captured. Otherwise, only requests whose window ended before the
        currently-active chunk started are flushed (see
        _active_chunk_boundary()) - anything more recent might still have
        data waiting in that not-yet-drained chunk.
        """
        if not self._pending:
            return

        if final:
            resolved = list(self._pending)
        else:
            boundary = self._active_chunk_boundary()
            if boundary is None:
                return
            resolved = [p for p in self._pending if p.t_end < boundary]
            if not resolved:
                return

        DBAccess.cursor.executemany(
            "UPDATE Requests SET parents_bytes = ?, parents_queries = ? WHERE id = ?",
            [(p.bytes_total, p.queries, p.request_id) for p in resolved])
        DBAccess.conn.commit()

        resolved_ids = {p.request_id for p in resolved}
        self._pending = [p for p in self._pending if p.request_id not in resolved_ids]
        self._flow_owner = {k: v for k, v in self._flow_owner.items() if v not in resolved}

    def stop(self) -> None:
        """Stop capturing and make sure every recorded window gets a final
        answer written back, including whatever was still in the actively-
        written chunk at the moment we stopped."""
        try:
            self.drain()
        except CaptureError:
            pass  # already dying/dead; still try to salvage what we can below
        self._kill_proc()
        self.drain(include_latest=True)
        self.flush_resolved(final=True)

        if self._chunk_dir and os.path.isdir(self._chunk_dir):
            try:
                shutil.rmtree(self._chunk_dir)
            except OSError:
                pass
