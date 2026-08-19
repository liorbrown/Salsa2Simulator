#!/usr/bin/env python3
"""
HIT/MISS comparator V2 - Salsa2 Simulator

Estimates how much the cache improves the time efficiency of requests.
Clears every parent cache, runs a chosen trace twice, and compares the
elapsed time of requests that were a cache MISS on the first (cold) run
against the elapsed time of those very same requests once they are a
cache HIT on the second (warm) run.
"""
import os
from datetime import datetime
from typing import Optional

import xlsxwriter
from prettytable import PrettyTable

from database.db_access import DBAccess
from cache.cache_manager import fill_caches, is_squid_up, reset_all_caches
from cache.registry import get_all_caches
from ui.repository import UIRepository
from http_requests.request_executor import send_proxied_request, is_hit

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hit_miss_reports')

BOLD = '\033[1m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def _clear_parent_caches() -> bool:
    """Clear all parent caches so the first run starts cold. Returns True on success."""
    caches = get_all_caches()
    if not caches:
        print("No parent caches found in squid.conf - nothing to reset.")
        return True

    print("Clearing parent caches before running the trace:")
    for name, info in caches.items():
        print(f"  - {name} ({info['ip']})")

    answer = input("Continue? [y/N]: ").strip().lower()
    if answer != 'y':
        print("Aborted.")
        return False

    results = reset_all_caches()

    table = PrettyTable()
    table.field_names = ['Name', 'IP', 'Status']
    for name, ip, status in results:
        table.add_row([name, ip, status])
    print(table)

    if any(status != 'ok' for _, _, status in results):
        print("Error: failed to clear one or more parent caches.")
        return False

    return True


def _select_trace() -> Optional[int]:
    """Display all traces and let the user pick one by ID."""
    traces = UIRepository.get_all_traces()

    if not traces:
        print("No traces found in the database.")
        return None

    table = PrettyTable()
    table.field_names = ['ID', 'Name', 'Keys', 'Last Update']
    for row in traces:
        table.add_row(list(row))
    print(table)

    try:
        trace_id = int(input("Choose trace ID: "))
    except ValueError:
        print("Error: Please enter a valid number for trace ID.")
        return None

    valid_ids = [row[0] for row in traces]
    if trace_id not in valid_ids:
        print(f"Error: Trace ID {trace_id} not found. Please choose from available IDs.")
        return None

    return trace_id


def _run_trace_once(urls: list, run_label: str) -> list:
    """Run every URL in the trace once, in order, printing progress as it goes.

    Returns a list the same length as `urls`: each entry is (hit, elapsed_ms),
    or None where the request errored - the position is kept so run 1 and
    run 2 can be paired up by index afterwards.
    """
    total = len(urls)
    results = []

    for done, url in enumerate(urls, start=1):
        progress = f"[{run_label} {done}/{total}]"

        try:
            response = send_proxied_request(url)
        except Exception as e:
            print(f"{progress} {url} | error - {e}")
            results.append(None)
            continue

        if response.status_code >= 300:
            print(f"{progress} {url} | error - {response.status_code}")
            results.append(None)
            continue

        hit = is_hit(response)
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        status = "HIT" if hit else "MISS"
        print(f"{progress} {url} | {status} | {elapsed_ms} ms")

        results.append((hit, elapsed_ms))

    return results


def _match_previously_missed(run1: list, run2: list):
    """Pair up requests that were a MISS on run 1 with their run 2 outcome.

    Returns (matched_miss, matched_hit, unresolved):
      - matched_miss: run 1 elapsed ms for requests that were MISS on run 1
        and came back as a HIT on run 2
      - matched_hit: run 2 elapsed ms for that same set of requests, in the
        same order as matched_miss (so index i is the same request in both)
      - unresolved: count of requests that were MISS on run 1 but did not
        come back as a HIT on run 2 (still MISS, or one of the two errored)
    """
    matched_miss = []
    matched_hit = []
    unresolved = 0

    for entry1, entry2 in zip(run1, run2):
        if entry1 is None or entry1[0]:
            continue  # not a MISS on run 1, irrelevant to this comparison

        if entry2 is not None and entry2[0]:
            matched_miss.append(entry1[1])
            matched_hit.append(entry2[1])
        else:
            unresolved += 1

    return matched_miss, matched_hit, unresolved


def _build_summary_rows(matched_miss: list, matched_hit: list) -> list:
    """Average elapsed time per status, over the matched population (requests
    that were MISS on run 1 and HIT on run 2). Both sides share the same
    count - it's one datum for the pair, not a per-row value - so it's
    reported separately rather than repeated on the MISS and HIT rows."""
    rows = []
    if matched_miss:
        rows.append(['MISS', sum(matched_miss) / len(matched_miss)])
    if matched_hit:
        rows.append(['HIT', sum(matched_hit) / len(matched_hit)])
    return rows


def _print_summary(summary_rows: list, count: int):
    print(f"Compared {count} request(s) (MISS on run 1 -> HIT on run 2)")

    table = PrettyTable()
    table.field_names = ['Status', 'Avg elapsed (ms)']

    for status, avg_elapsed in summary_rows:
        table.add_row([status, f"{avg_elapsed:.2f}"])

    print(table)


def _compute_miss_hit_ratio(matched_miss: list, matched_hit: list) -> Optional[float]:
    """How many times slower a cache MISS is compared to a HIT, over the
    matched population (same requests, cold vs warm).

    Returns None when either side has no data, or the HIT total is 0
    (can't divide by it).
    """
    if not matched_miss or not matched_hit:
        return None

    hit_total = sum(matched_hit)
    if not hit_total:
        return None

    return sum(matched_miss) / hit_total


def _format_miss_hit_ratio(miss_hit_ratio: Optional[float]) -> str:
    if miss_hit_ratio is None:
        return "MISS/HIT time ratio: N/A (no matched HIT/MISS pair found)"
    return f"MISS is {miss_hit_ratio:.2f}x slower than HIT"


def _print_miss_hit_ratio(miss_hit_ratio: Optional[float]):
    text = _format_miss_hit_ratio(miss_hit_ratio)
    border = "=" * (len(text) + 4)
    print(f"\n{BOLD}{YELLOW}{border}\n  {text}\n{border}{RESET}\n")


def _export_to_excel(timestamp: datetime, trace_id: int, summary_rows: list,
                      count: int, miss_hit_ratio: Optional[float]) -> str:
    """Export the run's timestamp, trace ID, the MISS/HIT time ratio (the
    headline metric) and the final summary table to an Excel file."""
    os.makedirs(REPORTS_DIR, exist_ok=True)

    file_name = f"hit_miss_{trace_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(REPORTS_DIR, file_name)

    workbook = xlsxwriter.Workbook(file_path)
    sheet = workbook.add_worksheet('Summary')

    bold = workbook.add_format({'bold': True})
    highlight = workbook.add_format({
        'bold': True,
        'font_size': 18,
        'font_color': '#9C5700',
        'bg_color': '#FFEB9C',
        'border': 2,
        'align': 'center',
        'valign': 'vcenter',
    })

    sheet.write(0, 0, 'Timestamp', bold)
    sheet.write(0, 1, timestamp.strftime('%Y-%m-%d %H:%M:%S'))

    sheet.write(1, 0, 'Trace ID', bold)
    sheet.write(1, 1, trace_id)

    sheet.write(2, 0, 'Compared requests', bold)
    sheet.write(2, 1, count)

    sheet.merge_range(3, 0, 4, 1, _format_miss_hit_ratio(miss_hit_ratio), highlight)
    sheet.set_row(3, 30)
    sheet.set_row(4, 30)

    header_row = 6
    headers = ['Status', 'Avg elapsed (ms)']
    for col, header in enumerate(headers):
        sheet.write(header_row, col, header, bold)

    for row_offset, (status, avg_elapsed) in enumerate(summary_rows, start=1):
        row = header_row + row_offset
        sheet.write(row, 0, status)
        sheet.write(row, 1, round(avg_elapsed, 2))

    sheet.autofit()
    workbook.close()

    return file_path


def run_hit_miss_comparator():
    """Clear all parent caches, run a user-chosen trace twice, and compare
    the elapsed time of requests that were a MISS on the first (cold) run
    against the same requests once they are a HIT on the second (warm) run.
    """
    if not is_squid_up():
        print("Error: Squid Down")
        return

    if not _clear_parent_caches():
        return

    timestamp = datetime.now()

    trace_id = _select_trace()
    if not trace_id:
        return

    urls = [url for (url,) in UIRepository.get_trace_entries(trace_id)]
    if not urls:
        print("Selected trace has no requests.")
        return

    print("\n--- Run 1 (cold) ---")
    run1 = _run_trace_once(urls, "Run 1")

    run1_miss_total = sum(e[1] for e in run1 if e is not None and not e[0])
    print(f"\nSum of MISS elapsed time (run 1): {run1_miss_total} ms")

    print("\n--- Run 2 (warm) ---")
    run2 = _run_trace_once(urls, "Run 2")

    matched_miss, matched_hit, unresolved = _match_previously_missed(run1, run2)

    print(f"\nSum of elapsed time for requests that were MISS in run 1 and are now HIT in run 2: "
          f"{sum(matched_hit)} ms")
    if unresolved:
        print(f"Warning: {unresolved} request(s) were MISS in run 1 but not a HIT in run 2 "
              f"- excluded from the ratio below.")

    print()
    count = len(matched_miss)
    summary_rows = _build_summary_rows(matched_miss, matched_hit)
    _print_summary(summary_rows, count)

    miss_hit_ratio = _compute_miss_hit_ratio(matched_miss, matched_hit)
    _print_miss_hit_ratio(miss_hit_ratio)

    file_path = _export_to_excel(timestamp, trace_id, summary_rows, count, miss_hit_ratio)
    print(f"Report exported to {file_path}")


def main():
    try:
        DBAccess.open()
        fill_caches()
        run_hit_miss_comparator()
    finally:
        DBAccess.close()


if __name__ == "__main__":
    main()
