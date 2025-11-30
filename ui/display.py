"""Display and UI functions for Salsa2 Simulator."""
from typing import List, Iterable, Tuple
from prettytable import PrettyTable

from cache.cache_manager import get_cost, get_miss_cost
from ui.repository import UIRepository
from metrics.calculator import create_caches_dict, classification_metrics, analyze_request_caches


def show_run(run_id: int):
    """Display details of a specific run."""
    if run_id:
        rows = UIRepository.get_run_requests(run_id)
        show_requests_details(rows, run_id)

def show_all_runs():
    show_runs()

    try:
        run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))
        if run_id < 0:
            print("Error: Run ID cannot be negative.")
            return
    except ValueError:
        print("Error: Please enter a valid number for run ID.")
        return

    show_run(run_id)


def show_runs(run_id = None):
    """Fetches and displays all entries in the 'Runs' table."""
    runs = UIRepository.get_runs(run_id)
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = [
        'ID',
        'Name',
        'Salsa V',
        'Miss Cost',
        'nCaches',
        'Trace',
        'Requests',
        'Total Cost',
        'Average Cost']
    
    # Process each run
    for run_id, name, start_time, end_time, salsa_v, miss_penalty, caches_count, trace_name in runs:
        cost, reqNum = get_cost(run_id)
        if reqNum:
            avg_cost = round(cost / reqNum, 3)
        else:
            avg_cost = None

        row = run_id, name, salsa_v, miss_penalty, caches_count, trace_name, reqNum, cost, avg_cost

        table.add_row(row)
    
    print(table)

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


def print_accuracy(cachesDict) -> None:
    """Print accuracy metrics table."""
    column_names = ['Name', 'Accuracy', 'Recall', 'Precision', 'F1 Score', 'Cost']

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers

    table.add_rows(classification_metrics(cachesDict))

    print(table)


def show_requests_details(requests: Iterable[Tuple], run_id = None) -> None:
    """Display detailed information about requests with classification metrics."""
    table = PrettyTable()
    table.field_names = ['ReqID', 'URL', 'Indications', 'Accessed', 'Resolution', 'Hit?', 'Cost']

    if run_id:
        cachesDict = create_caches_dict(run_id)

    for req in requests:
        req_id, req_url = req[0], req[2]

        # Analyze request caches and get metrics + details
        req_caches_dict, details = analyze_request_caches(req_id, run_id)
        
        if run_id:
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
            req_id,
            req_url, 
            fmt(details['indicated']), 
            fmt(details['accessed']),
            fmt(details['resolved']), 
            details['hit'], 
            cost
        ])

    print(table)

    if run_id:
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

    # After displaying recent requests, offer to re-request a URL.
    try:
        choice = int(input("Enter request ID to re-request its URL, or 0 to skip: "))
    except ValueError:
        print("Invalid input. Skipping re-request.")
        return

    if choice == 0:
        return

    # Validate choice is among displayed requests
    displayed_ids = {r[0] for r in req_ids}
    if choice not in displayed_ids:
        print("The entered request ID was not in the displayed list.")
        return

    # Use the URL already displayed in `req_ids` instead of querying the DB again.
    try:
        # find the selected row in the displayed results
        selected = next((r for r in req_ids if r[0] == choice), None)
        if not selected:
            print("The entered request ID was not found in the displayed list.")
            return

        # req_ids rows are (id, time, url)
        url = selected[2]

        from http_requests.request_executor import execute_req, get_request_result

        print(f"Re-requesting URL from request {choice}: {url}")
        # We don't have the original Run_ID in the displayed rows; pass 0.
        new_req = execute_req(url, 0)
        if not new_req:
            print("Re-request failed or no cache recorded for the URL.")
            return

        # Use centralized helper to obtain the request result
        name, cost = get_request_result(new_req)
        if name is None:
            print("Re-request completed but no accessed cache row was recorded.")
            return

        print(f"Request fetched successfully from {name} at cost of {cost}")

    except Exception as e:
        print(f"Failed to re-request: {e}")
