"""Simulation orchestration for running traces."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from prettytable import PrettyTable

from database.db_access import DBAccess
from cache.cache_manager import is_squid_up, get_cost
from http_requests.request_executor import execute_req


def run_trace():
    """
    Executes all requests for a specified trace and logs the results into the 'Runs' table.
    """
    # Check if squid works properly on all servers
    if is_squid_up():
        
        name = input("Insert run name: ").strip()
        if not name:
            print("Error: Run name cannot be empty. Please try again.")
            return
        
        # Fetch all rows from the "Traces" table, with their keys count
        DBAccess.cursor.execute("""SELECT T.id ID, T.Name Name, 
                                COUNT(K.id) Keys, T.Last_Update Last_Update 
                        FROM Traces T, Trace_Entry K
                        WHERE T.id = K.Trace_ID
                        GROUP BY T.id""")
        rows = DBAccess.cursor.fetchall()
        
        if not rows:
            print("No traces found in the database. Please create a trace first.")
            return
        
        # Fetch column names for the table
        column_names = [description[0] for description in DBAccess.cursor.description]
        
        # Display the data in a table format using PrettyTable
        table = PrettyTable()
        table.field_names = column_names  # Set column headers
        
        for row in rows:
            table.add_row(row)
        
        print(table)

        try:
            trace_id = int(input("Choose trace ID: "))
            # Validate trace_id exists
            valid_ids = [row[0] for row in rows]
            if trace_id not in valid_ids:
                print(f"Error: Trace ID {trace_id} not found. Please choose from available IDs.")
                return
        except ValueError:
            print("Error: Please enter a valid number for trace ID.")
            return
        
        try:
            limit = int(input("Insert limit of requests to execute, or 0 to not limit: "))
            if limit < 0:
                print("Error: Limit cannot be negative. Using no limit instead.")
                limit = 0
        except ValueError:
            print("Error: Please enter a valid number for limit.")
            return
        jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

        # Try to clear all caches before running trace
        if True:  # clear_caches():           
            # print("All caches cleared successfully")
        
            try:    
                # Create entry for the run, for generate and gets run id 
                # for insert in requests entries.
                # init End_time and total cost with dummies because they can't accept nulls
                DBAccess.cursor.execute("""INSERT INTO Runs('Name','Start_Time','End_time','Trace_ID', 'Total_Cost')
                                VALUES(?,?,?,?,0)""", [name, jerusalem_time, jerusalem_time, trace_id])
                
                # Get current run id
                DBAccess.cursor.execute("SELECT MAX(id) from Runs")
                row = DBAccess.cursor.fetchone()
                run_id = row[0] 

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

                print("Trace run successfully!")
                
                cost, reqNum = get_cost(run_id)
                
                # Calculate average cost (avoid division by zero)
                avg_cost = round(cost / reqNum, 3) if reqNum > 0 else 0.0

                # Fetch current run from the "Runs" table, for show the result
                DBAccess.cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                                        T.Name trace_name, ? requests, ? Total_cost, ? Average_cost
                                FROM Runs RUN JOIN Traces T  
                                ON RUN.Trace_ID = T.id
                                WHERE RUN.id = ?""", [reqNum, cost, avg_cost, run_id])
                row = DBAccess.cursor.fetchone()
                
                if row:
                    column_names = [description[0] for description in DBAccess.cursor.description]

                    # Display the data in a table format using PrettyTable
                    table = PrettyTable()
                    table.field_names = column_names  # Set column headers

                    # Add selected row  
                    table.add_row(row)
                    
                    print(table)

                    # Import here to avoid circular dependency
                    from ui.display import show_run
                    show_run(run_id)
                else:
                    print(f"Warning: Could not fetch run details for run_id {run_id}")

            except sqlite3.DatabaseError as e:
                # If insertion fails, print the exact error message from SQLite
                print(f"Trace failed: {e}")
