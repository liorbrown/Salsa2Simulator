#!/usr/bin/env python3
"""
HIT/MISS comparator - Salsa2 Simulator

Estimates how much the cache improves the time efficiency of requests by
running a chosen trace and comparing, per request, elapsed time (ms) per
KB of response - grouped by cache HIT/MISS.
"""
import os
from datetime import datetime
from typing import Optional

import xlsxwriter
from prettytable import PrettyTable

from database.db_access import DBAccess
from cache.cache_manager import fill_caches, is_squid_up
from ui.repository import UIRepository
from http_requests.request_executor import (
    send_proxied_request,
    calculate_response_size,
    is_hit,
)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hit_miss_reports')

BOLD = '\033[1m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def _select_trace() -> Optional[int]:
    """Display all traces and let the user pick one by ID."""
    traces = UIRepository.get_all_traces()

    if not traces:
        print("No traces found in the database.")
        return None

    table = PrettyTable()
    table.field_names = ['ID', 'Name', 'Keys', 'Last Update']
    for row in traces:
        table.add_row(row)
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


def _print_entry(url: str, hit: bool, elapsed_ms: int, size_kb: float, ratio: float):
    status = "HIT" if hit else "MISS"
    print(f"{url} | {status} | {elapsed_ms} ms | {size_kb:.2f} KB | {ratio:.4f} ms/KB")


def _build_summary_rows(stats: dict) -> list:
    """Compute, per HIT/MISS status, count and average elapsed/size/ratio."""
    rows = []
    for status in ('HIT', 'MISS'):
        entries = stats[status]
        if not entries:
            continue

        count = len(entries)
        avg_elapsed = sum(e[0] for e in entries) / count
        avg_size = sum(e[1] for e in entries) / count
        avg_ratio = sum(e[2] for e in entries) / count

        rows.append([status, count, avg_elapsed, avg_size, avg_ratio])

    return rows


def _print_summary(summary_rows: list):
    table = PrettyTable()
    table.field_names = ['Status', 'Count', 'Avg elapsed (ms)', 'Avg size (KB)', 'Avg ms/KB']

    for status, count, avg_elapsed, avg_size, avg_ratio in summary_rows:
        table.add_row([status, count, f"{avg_elapsed:.2f}", f"{avg_size:.2f}", f"{avg_ratio:.4f}"])

    print(table)


def _compute_miss_hit_ratio(summary_rows: list) -> Optional[float]:
    """How many times slower (ms/KB) a cache MISS is compared to a HIT.

    Returns None when either HIT or MISS has no data, or HIT's ratio is 0
    (can't divide by it).
    """
    ratios_by_status = {status: avg_ratio for status, _, _, _, avg_ratio in summary_rows}
    hit_ratio = ratios_by_status.get('HIT')
    miss_ratio = ratios_by_status.get('MISS')

    if not hit_ratio or miss_ratio is None:
        return None

    return miss_ratio / hit_ratio


def _format_miss_hit_ratio(miss_hit_ratio: Optional[float]) -> str:
    if miss_hit_ratio is None:
        return "MISS/HIT ms-per-KB ratio: N/A (need both HIT and MISS data)"
    return f"MISS is {miss_hit_ratio:.2f}x slower than HIT (ms/KB)"


def _print_miss_hit_ratio(miss_hit_ratio: Optional[float]):
    text = _format_miss_hit_ratio(miss_hit_ratio)
    border = "=" * (len(text) + 4)
    print(f"\n{BOLD}{YELLOW}{border}\n  {text}\n{border}{RESET}\n")


def _export_to_excel(timestamp: datetime, trace_id: int, summary_rows: list,
                      miss_hit_ratio: Optional[float]) -> str:
    """Export the run's timestamp, trace ID, the MISS/HIT ms-per-KB ratio
    (the headline metric) and the final summary table to an Excel file."""
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

    sheet.merge_range(3, 0, 4, 4, _format_miss_hit_ratio(miss_hit_ratio), highlight)
    sheet.set_row(3, 30)
    sheet.set_row(4, 30)

    header_row = 6
    headers = ['Status', 'Count', 'Avg elapsed (ms)', 'Avg size (KB)', 'Avg ms/KB']
    for col, header in enumerate(headers):
        sheet.write(header_row, col, header, bold)

    for row_offset, (status, count, avg_elapsed, avg_size, avg_ratio) in enumerate(summary_rows, start=1):
        row = header_row + row_offset
        sheet.write(row, 0, status)
        sheet.write(row, 1, count)
        sheet.write(row, 2, round(avg_elapsed, 2))
        sheet.write(row, 3, round(avg_size, 2))
        sheet.write(row, 4, round(avg_ratio, 4))

    sheet.autofit()
    workbook.close()

    return file_path


def run_hit_miss_comparator():
    """Run a user-chosen trace and, for each request, print elapsed time (ms)
    per response KB - then print averages grouped by cache HIT/MISS.
    """
    if not is_squid_up():
        print("Error: Squid Down")
        return

    timestamp = datetime.now()

    trace_id = _select_trace()
    if not trace_id:
        return

    urls = [url for (url,) in UIRepository.get_trace_entries(trace_id)]
    if not urls:
        print("Selected trace has no requests.")
        return

    stats = {'HIT': [], 'MISS': []}

    for url in urls:
        try:
            response = send_proxied_request(url)
        except Exception as e:
            print(f"Request {url} error - {e}")
            continue

        if response.status_code >= 300:
            print(f"Request {url} error - {response.status_code}")
            continue

        hit = is_hit(response)
        elapsed_ms = int(response.elapsed.total_seconds() * 1000)
        size_bytes = calculate_response_size(response)

        if size_bytes == 0:
            print(f"Request {url} error - empty response, cannot compute ms/KB")
            continue

        size_kb = size_bytes / 1024
        ratio = elapsed_ms / size_kb

        _print_entry(url, hit, elapsed_ms, size_kb, ratio)
        stats['HIT' if hit else 'MISS'].append((elapsed_ms, size_kb, ratio))

    print()
    summary_rows = _build_summary_rows(stats)
    _print_summary(summary_rows)

    miss_hit_ratio = _compute_miss_hit_ratio(summary_rows)
    _print_miss_hit_ratio(miss_hit_ratio)

    file_path = _export_to_excel(timestamp, trace_id, summary_rows, miss_hit_ratio)
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