"""Simulation orchestration for running traces."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from prettytable import PrettyTable
from typing import Tuple, Optional

from config.config import MyConfig
from database.db_access import DBAccess
from cache.cache_manager import is_squid_up
from http_requests.request_executor import execute_req
from ui.display import show_runs


def _get_run_details() -> Optional[Tuple[str, int, int]]:
    """Get run details from user input.
    
    Returns:
        Tuple of (run_name, trace_id, limit) or None if validation fails.
    """
    name = input("Insert run name: ").strip()
    if not name:
        print("Error: Run name cannot be empty. Please try again.")
        return None
    
    # Fetch all rows from the "Traces" table, with their keys count
    DBAccess.cursor.execute("""SELECT T.id ID, T.Name Name, 
                            COUNT(K.id) Keys, T.Last_Update Last_Update 
                    FROM Traces T, Trace_Entry K
                    WHERE T.id = K.Trace_ID
                    GROUP BY T.id""")
    rows = DBAccess.cursor.fetchall()
    
    if not rows:
        print("No traces found in the database. Please create a trace first.")
        return None
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    try:
        trace_id = int(input("Choose trace ID: "))
        # Validate trace_id exists
        valid_ids = [row[0] for row in rows]
        if trace_id not in valid_ids:
            print(f"Error: Trace ID {trace_id} not found. Please choose from available IDs.")
            return None
    except ValueError:
        print("Error: Please enter a valid number for trace ID.")
        return None
    
    try:
        limit = int(input("Insert limit of requests to execute, or 0 to not limit: "))
        if limit < 0:
            print("Error: Limit cannot be negative. Using no limit instead.")
            limit = 0
    except ValueError:
        print("Error: Please enter a valid number for limit.")
        return None
    
    return (name, trace_id, limit)


def _create_run_entry(name: str, trace_id: int) -> Optional[int]:
    """Create a new run entry in the Runs table.
    
    Args:
        name: Name of the run
        trace_id: ID of the trace to run
        
    Returns:
        run_id if successful, None otherwise.
    """
    jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    config = MyConfig()
    salsa2_v = config.get_key('salsa2_v')
    miss_penalty = config.get_key('miss_penalty')

    try:
        # Create entry for the run, for generate and gets run id 
        # for insert in requests entries.
        # init End_time and total cost with dummies because they can't accept nulls
        DBAccess.cursor.execute(
            """INSERT INTO Runs
                ('Name',
                'Start_Time',
                'End_time',
                'Trace_ID',
                'salsa_v',
                'miss_penalty',
                'Total_Cost')
                VALUES(?,?,?,?,?,?,0)""", 
                [name, jerusalem_time, jerusalem_time, trace_id, salsa2_v,miss_penalty])
        
        # Get current run id
        DBAccess.cursor.execute("SELECT MAX(id) from Runs")

        row = DBAccess.cursor.fetchone()

        if not row:
            return None
        
        run_id = row[0]
        caches = config.get_key('caches')

        # Update Caches table for current run
        for name, details in caches.items():
            cost = details.get('access_cost')
            
            if cost is not None:
                DBAccess.cursor.execute(
                    """INSERT INTO Caches('Run_ID', 'Name', 'Access_Cost')
                        VALUES(?,?,?)""", [run_id, name, cost])
        
        # Insert cahces data for current run
        return run_id
        
    except sqlite3.DatabaseError as e:
        print(f"Failed to create run entry: {e}")
        return None


def _execute_requests(run_id: int, trace_id: int, limit: int) -> bool:
    """Execute all requests for the trace.
    
    Args:
        run_id: ID of the current run
        trace_id: ID of the trace to execute
        limit: Maximum number of requests to execute (0 = no limit)
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Get all trace's URLs
        DBAccess.cursor.execute("SELECT URL FROM Trace_Entry WHERE Trace_ID = ?", [trace_id])
        rows = DBAccess.cursor.fetchall()

        # Run on all trace URLs
        for row in rows:
            # If requests succeed and there is limit, 
            # decrease limit and check if reach it
            req_id = execute_req(row[0], run_id)

            if req_id and limit > 0:
                limit -= 1
                if not limit:
                    break

        jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

        # Update run entry with end time
        DBAccess.cursor.execute("""UPDATE Runs
        SET End_Time = ?
        WHERE id = ?""", [jerusalem_time, run_id])

        DBAccess.conn.commit()
        return True
        
    except sqlite3.DatabaseError as e:
        print(f"Failed to execute requests: {e}")
        return False

def _print_results(run_id: int):
    """Print the results of the run.
    
    Args:
        run_id: ID of the completed run
    """
    print("Trace run successfully!")
    
    show_runs(run_id)

    # Import here to avoid circular dependency
    from ui.display import show_run
    
    show_run(run_id)

def run_trace():
    """Executes all requests for a specified trace and logs the results into the 'Runs' table."""
    # Check if squid works properly on all servers
    if not is_squid_up():
        print("Error: Squid Down")
        return
    
    # Get run details from user
    result = _get_run_details()
    if not result:
        return
    
    name, trace_id, limit = result
    
    try:
        # Create run entry in database
        run_id = _create_run_entry(name, trace_id)
        if not run_id:
            return
        
        # Execute all requests
        if not _execute_requests(run_id, trace_id, limit):
            return
        
        # Display results
        _print_results(run_id)
        
    except sqlite3.DatabaseError as e:
        print(f"Trace failed: {e}")
