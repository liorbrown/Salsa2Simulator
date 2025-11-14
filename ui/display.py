"""Display and UI functions for Salsa2 Simulator."""
from typing import Dict, List, Iterable, Tuple
from prettytable import PrettyTable

from cache.cache_manager import get_cost, get_miss_cost
from ui.repository import UIRepository
from metrics.calculator import create_caches_dict, classification_metrics, analyze_request_caches


def show_run(run_id: int):
    """Display details of a specific run."""
    if run_id:
        rows = UIRepository.get_run_requests(run_id)
        show_requests_details(rows)


def show_runs():
    """Fetches and displays all entries in the 'Runs' table."""
    runs = UIRepository.get_all_runs()
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = ['ID', 'Name', 'Start Time', 'End Time', 'Trace Name', 'Requests', 'Total Cost', 'Average Cost']
    
    # Process each run
    for run in runs:
        cost, reqNum = get_cost(run[0])
        if reqNum:
            avg_cost = round(cost / reqNum, 3)
        else:
            avg_cost = 0.0
        row = [run[0], run[1], run[2], run[3], run[4], reqNum, cost, avg_cost]
        table.add_row(row)
    
    print(table)

    try:
        run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))
        if run_id < 0:
            print("Error: Run ID cannot be negative.")
            return
    except ValueError:
        print("Error: Please enter a valid number for run ID.")
        return

    show_run(run_id)


def show_keys(trace_id):    
    """
    Fetches and displays URLs associated with a specific Trace ID.
    
    Args:
        trace_id: The ID of the trace to fetch URLs for
    """
    group_by = input("Group by URLs? (y/n)")
    rows = UIRepository.get_trace_entries(trace_id, group_by_url=group_by.upper() == 'Y')
    
    # Determine column names based on group_by preference
    if group_by.upper() == 'Y':
        column_names = ['URL', 'Count']
    else:
        column_names = ['URL']

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names
    
    for row in rows:
        table.add_row(row)
    
    print(table)


def show_traces():
    """
    Fetches and displays trace details, including the number of keys and last update time.
    Allows the user to view details of a specific trace.
    """
    rows = UIRepository.get_all_traces()
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = ['ID', 'Name', 'Keys', 'Last Update']
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    # Get from user trace id to show its content
    try:
        trace_id = int(input("""Select trace ID to show its content, or 0 to go back to main menu: """))
        if trace_id < 0:
            print("Error: Trace ID cannot be negative.")
            return
    except ValueError:
        print("Error: Please enter a valid number for trace ID.")
        return

    if trace_id:
        show_keys(trace_id)


def print_accuracy(cachesDict: Dict[str, List[int]]) -> None:
    """Print accuracy metrics table."""
    column_names = ['Name', 'Accuracy', 'Recall', 'Precision', 'F1 Score']

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers

    table.add_rows(classification_metrics(cachesDict))

    print(table)


def show_requests_details(requests: Iterable[Tuple]) -> None:
    """Display detailed information about requests with classification metrics."""
    table = PrettyTable()
    table.field_names = ['Time', 'URL', 'Indications', 'Accessed', 'Resolution', 'Hit?', 'Cost']

    cachesDict: Dict[str, List[int]] = create_caches_dict()

    for req in requests:
        req_id, req_time, req_url = req[0], req[1], req[2]

        # Analyze request caches and get metrics + details
        req_caches_dict, details = analyze_request_caches(req_id)
        
        # Merge metrics from this request into overall dictionary
        for cache_name in req_caches_dict:
            for i in range(4):
                cachesDict[cache_name][i] += req_caches_dict[cache_name][i]
        
        # Handle miss cost
        cost = details['cost']
        if not details['hit']:
            cost += get_miss_cost()

        def fmt(names: List[str]) -> str:
            return f"[{','.join(names)}]"

        table.add_row([
            req_time, 
            req_url, 
            fmt(details['indicated']), 
            fmt(details['accessed']),
            fmt(details['resolved']), 
            details['hit'], 
            cost
        ])

    print(table)
    print_accuracy(cachesDict)


def show_requests():
    """
    Fetches and displays a specified number of the most recent requests,
    including cache details.
    """
    try:
        count = int(input("How many requests you want to show?: "))
        if count <= 0:
            print("Error: Please enter a positive number.")
            return
    except ValueError:
        print("Error: Please enter a valid number.")
        return
     
    # Fetch recent requests from the database
    req_ids = UIRepository.get_recent_requests(count)

    show_requests_details(req_ids)
