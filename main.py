import sqlite3
import random
from prettytable import PrettyTable

def show_runs(cursor):
    """
    Fetches and displays all entries in the 'Runs' table
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Runs" table
    #cursor.execute("SELECT * FROM Runs")
    cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                             T.Name trace_name, SUM(C.Access_Cost) total_cost
                      FROM Runs RUN, Requests REQ, Caches C, Traces T   
                      WHERE REQ.Run_ID = RUN.id AND 
                            C.id = REQ.Cache_id AND 
                            RUN.Trace_ID = T.id
                      GROUP BY RUN.id""")
    rows = cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))

    if run_id:
        # Fetch rows from the "Requests" table
        cursor.execute("""SELECT R.Time Time, R.URL URL, C.Name Cache, C.Access_cost Cost
                          FROM Requests R, Caches C 
                          WHERE R.Cache_ID = C.id AND R.Run_ID = ?""",[run_id])
        rows = cursor.fetchall()

        # Fetch column names for the table
        column_names = [description[0] for description in cursor.description]
        
        # Display the data in a table format using PrettyTable
        table = PrettyTable()
        table.field_names = column_names  # Set column headers
        
        for row in rows:
            table.add_row(row)
        
        print(table)
    
def show_keys(cursor, trace_id):    
    """
    Fetches and displays URLs associated with a specific Trace ID from the 'Keys' table.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        trace_id (int): The ID of the trace to fetch URLs for.
    """

    # Fetch all URLs from keys table, that belong to trace_id 
    cursor.execute("""SELECT URL 
                      FROM Keys 
                      WHERE Trace_ID = ?""",[trace_id])
    rows = cursor.fetchall()
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = ['URL']  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def show_traces(cursur):
    """
    Fetches and displays trace details, 
    including the number of keys and last update time.
    Allows the user to view details of a specific trace.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Traces" table
    cursor.execute("""SELECT T.id ID, T.Name Name, 
                             COUNT(K.id) Keys, T.Last_Update Last_Update 
                      FROM Traces T, Keys K
                      WHERE T.id = K.Trace_ID
                      GROUP BY T.id""")
    rows = cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    # Get from user trace id to show it's content
    trace_id = int(input("""Select trace ID to show it content, or 0 to go back to main menu: """))

    if trace_id:
        show_keys(cursor, trace_id)
    

def show_requsts(cursor):
    """
    Fetches and displays a specified number of the most recent requests, 
    including cache details.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    count = int(input("How match requsts you want to show?: "))
     
    # Fetch rows from the "Requests" table, limiting last {count}
    cursor.execute("""SELECT R.Time Time, R.URL URL, C.Name Cache, C.Access_cost Cost 
                      FROM Requests R, Caches C 
                      WHERE R.Cache_ID = C.id
                      ORDER BY R.Time DESC LIMIT ?""", [count])
    rows = cursor.fetchall()
    rows.reverse()

    # Fetch column names for the table
    column_names = [description[0] for description in cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def exectue_single_req(conn, cursor):
    """
    Executes a single request for a given URL and logs it into the 'Requests' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    url = input("Enter URL: ")

    try:
        # Execute request without run id
        cache_data = exectue_req(cursor, url, 0)
        conn.commit()

        print(f"""Requst Fetched successfully from 
                  {cache_data[0]} at cost of {cache_data[1]}""")

    except sqlite3.DatabaseError as e:
        # If request fails, print the exact error message from SQLite
        print(f"Request failed: {e}")


def exectue_req(cursor, url, run_id):
    """
    Simulates the execution of a request by selecting a random cache 
    and logging the request.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        url (str): The URL for the request.
        run_id (int): The ID of the run associated with the request.
    
    Returns:
        tuple: The cache name and its access cost.
    """

    # Get all caches and pick randomly one's ID
    cursor.execute("Select * from Caches")
    rows = cursor.fetchall()
    row_num = random.randint(0, len(rows) - 1)
    row = rows[row_num]
    cache_id = row[0]

    cursor.execute("""INSERT INTO Requests('URL','Cache_ID','Run_ID') 
                      VALUES (?,?,?)""",[url,cache_id,run_id])

    # Return cache name and cache access cost
    return (row[2], row[3])

def run_trace(conn, cursor):
    """
    Executes all requests for a specified trace 
    and logs the results into the 'Runs' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    name = input("Insert run name: ")
    
    # Fetch all rows from the "Traces" table, with their keys count
    cursor.execute("""SELECT T.id ID, T.Name Name, 
                             COUNT(K.id) Keys, T.Last_Update Last_Update 
                      FROM Traces T, Keys K
                      WHERE T.id = K.Trace_ID
                      GROUP BY T.id""")
    rows = cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    trace_id = int(input("Choose trace ID: "))
    
    try:
        # Create entry for the run, for generate and gets run id 
        # for insert in requests entries.
        # init End_time and total cost with dummies because they can't accept nulls
        cursor.execute("""INSERT INTO Runs('Name','Start_Time','End_time','Trace_ID', 'Total_Cost')
                          VALUES(?,current_timestamp,current_timestamp,?,0)""", [name, trace_id])
        
        # Get current run id
        cursor.execute("SELECT MAX(id) from Runs")
        rows = cursor.fetchall()
        run_id = rows[0][0] 

        # Get all trace's URLs
        cursor.execute("SELECT URL FROM Keys WHERE Trace_ID = ?", [trace_id])
        rows = cursor.fetchall()

        # Run on all trace URLs
        for row in rows:
            result = exectue_req(cursor, row[0], run_id)
        
        # Update run entry with end time
        cursor.execute("""UPDATE Runs
        SET End_Time = current_timestamp
        WHERE id = ?""",[run_id])

        conn.commit()

        print("Trace run successfully!")
        
        # Fetch current run from the "Runs" table, for show the result
        cursor.execute("""SELECT RUN.id ID, RUN.Name, 
                                 RUN.Start_Time start, RUN.End_Time end, 
                                 T.Name trace_name, SUM(C.Access_Cost) total_cost
                          FROM Runs RUN, Requests REQ, Caches C, Traces T  
                          WHERE REQ.Run_ID = RUN.id AND 
                          C.id = REQ.Cache_id AND 
                          RUN.Trace_ID = T.id AND 
                          RUN.id = ?""",[run_id])
        rows = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description]

        # Display the data in a table format using PrettyTable
        table = PrettyTable()
        table.field_names = column_names  # Set column headers

        # Add selected row  
        table.add_row(rows[0])
        
        print(table)

    except sqlite3.DatabaseError as e:
        # If insertion fails, print the exact error message from SQLite
        print(f"Trace failed: {e}")  

def show_caches(cursor):
    """
    Fetches and displays all cache details from the 'Caches' table.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Caches" table
    cursor.execute("SELECT * FROM Caches")
    rows = cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def new_cache(conn, cursor):
    """
    Inserts a new cache entry into the 'Caches' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    ip = input("Insert cache IP: ")
    name = input("Insert cache name: ")
    cost = int(input("Insert cache access cost: "))

    try:
        cursor.execute("""INSERT INTO Caches('IP','NAME','Access_Cost') 
                          VALUES (?,?,?)""",[ip,name,cost])
        conn.commit()
        print("Cache added successfully!")
        show_caches(cursor)
    except sqlite3.DatabaseError as e:
        # If insertion fails, print the exact error message from SQLite
        print(f"Insertion failed: {e}")
    
def update_cache(conn, cursor, cache_id):
    """
    Updates the specified fields of a cache entry in the 'Caches' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        cache_id (int): The ID of the cache to update.
    """

    opp_code = 1
    while opp_code:
        opp_code = int(input("""Witch field you want to change:
1: IP
2: Name
3: Access cost
0: Back to previous menu
"""))
        try:
            if opp_code == 1:
                ip = input("Insert cache IP: ")
                cursor.execute("""UPDATE Caches 
                                  SET IP = ? 
                                  WHERE id = ?""",[ip, cache_id])
            elif opp_code == 2:
                name = input("Insert cache name: ")
                cursor.execute("""UPDATE Caches 
                                  SET Name = ? 
                                  WHERE id = ?""",[name, cache_id])
            elif opp_code == 3:
                cost = int(input("Insert cache access cost: "))
                cursor.execute("""UPDATE Caches 
                                  SET Access_Cost = ? 
                                  WHERE id = ?""",[cost, cache_id])
            elif opp_code != 0:
                # In case of invalid input
                print("Invalid option, please choose a valid number.")        

            conn.commit()
            print("Cache updated successfully!")
            show_caches(cursor)

        except sqlite3.DatabaseError as e:
            # If insertion fails, print the exact error message from SQLite
            print(f"Update failed: {e}")

def manage_caches(conn, cursor):
    """
    Provides a menu-driven interface to manage cache entries in the database.    
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    opp_code = 1
    while opp_code:
        opp_code = int(input("""Choose option:
1: Show caches
2: Insert new cache
3: Update cache data
0: Back to main menu
"""))    
        if opp_code == 1:
            show_caches(cursor)
        elif opp_code == 2:
            new_cache(conn, cursor)
        elif opp_code == 3:
            show_caches(cursor)
            cache_id = int(input("Choose cache ID to update: "))
            update_cache(conn, cursor, cache_id)
        elif opp_code != 0:
            # In case of invalid input
            print("Invalid option, please choose a valid number.")

# Start of program
conn = sqlite3.connect('/home/lior/salsa2.db')
cursor = conn.cursor()

print("################# Welcome to Salsa2 simulator ####################")

opp_code = 1
while opp_code:
    opp_code = int(input("""Choose your destiny:
1: Show previous runs
2: Show Traces
3: Show last requsts
4: Execute single requst
5: Run entire trace
6: Manage caches
0: Exit
"""))
    if opp_code == 1:
        show_runs(cursor)
    elif opp_code == 2:
        show_traces(cursor)
    elif opp_code == 3:
        show_requsts(cursor)
    elif opp_code == 4:
        exectue_single_req(conn, cursor)
    elif opp_code == 5:
        run_trace(conn, cursor)
    elif opp_code == 6:
        manage_caches(conn, cursor)
    elif opp_code != 0:
        print("Invalid option, please choose a valid number.")

print("ByeBye")

