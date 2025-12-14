"""Display and UI functions for Salsa2 Simulator."""
from prettytable import PrettyTable
from ui.repository import UIRepository


def show_run(run_id: int):
    """Display details of a specific run."""
    if run_id:
        requests = UIRepository.get_run_requests(run_id)
        print_requests(requests)

def show_all_runs():
    if show_runs():
        try:
            run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))
            if run_id < 0:
                print("Error: Run ID cannot be negative.")
                return
        except ValueError:
            print("Error: Please enter a valid number for run ID.")
            return

        show_run(run_id)


def get_limit():
    """
    Prompt the user to enter a positive integer for the number of runs to display.
    
    Continuously prompts until a valid positive integer is provided.
    
    Returns:
        int: The number of runs the user wants to see (positive integer).
    """
    while True:
        try:
            limit = int(input("How much runs you want to see? "))

            if limit <= 0:
                print("Wrong input🤨, please enter positive integer")
            else:
                return limit

        except Exception as e:
            print(e)
            print("Wrong input🤨, please enter positive integer")


def display_runs_table(runs):
    """
    Display runs data in a formatted PrettyTable.
    
    Creates and prints a table with run details including ID, name, version,
    costs, and performance metrics.
    
    Args:
        runs: Iterable of run tuples from the database containing:
              (run_id, name, start_time, end_time, salsa_v, miss_penalty, 
               caches_count, trace_name)
    """
    table = PrettyTable()
    table.field_names = [
        'ID',
        'Name',
        'Salsa V',
        'Miss Cost',
        'nCaches',
        'Trace',
        'Requests',
        'Avg Req ms']
    
    # Process each run
    for (run_id, 
         name, 
         start_time, 
         end_time, 
         salsa_v, 
         miss_penalty, 
         caches_count,
         requests_count,
         total_time,
         trace_name) in runs:
        
        if requests_count and total_time:
            avg_time = total_time // requests_count
        else:
            avg_time = None

        row = (run_id, 
               name, 
               salsa_v, 
               miss_penalty, 
               caches_count, 
               trace_name, 
               requests_count,
               avg_time)

        table.add_row(row)
    
    print(table)


def show_runs(run_id = None):
    """
    Fetch and display runs in a formatted table.
    
    If run_id is provided, displays details for a specific run.
    Otherwise, prompts the user for the number of runs to display.
    
    Args:
        run_id (int, optional): Specific run ID to display. If None, prompts user for limit.
    
    Returns:
        bool: True if runs were found and displayed, False otherwise.
    """
    if run_id:
        runs = UIRepository.get_runs_by_id(run_id)
    else:
        limit = get_limit()
        runs= UIRepository.get_runs(limit)
    
    if not runs:
        print("No runs found")
        return False
    
    display_runs_table(runs)
    return True

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


def print_requests(requests: list):
    table = PrettyTable()
    table.field_names = ['id', 'URL', 'Elapsed (ms)']
    
    for request in requests:
        table.add_row(request)
    
    print(table)

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
    requests = UIRepository.get_recent_requests(count)

    if not len(requests):
        print("No requsts found")
        return
    
    print_requests(requests)

    # After displaying recent requests, offer to re-request a URL.
    try:
        choice = int(input("Enter request ID to re-request its URL, or 0 to skip: "))
    except ValueError:
        print("Invalid input. Skipping re-request.")
        return

    if not choice:
        return

    # Validate choice is among displayed requests
    displayed_ids = {r[0] for r in requests}
    if choice not in displayed_ids:
        print("The entered request ID was not in the displayed list.")
        return

    # find the selected row in the displayed results
    url = next((r[1] for r in requests if r[0] == choice), None)

    from http_requests.request_executor import execute_req

    print(f"Re-requesting {url}")
    
    if execute_req(url, 0):
        print("Request Successfuly!")
