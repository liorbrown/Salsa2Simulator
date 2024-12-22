import paramiko
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from prettytable import PrettyTable
import requests
import re

from MyConfig import MyConfig
import os
    
def show_runs(cursor):
    """
    Fetches and displays all entries in the 'Runs' table
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Runs" table
    #cursor.execute("SELECT * FROM Runs")
    cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                             T.Name trace_name, COUNT(C.id) requests, 
                             SUM(C.Access_Cost) total_cost, AVG(C.Access_Cost) average_cost
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
    group_by = input("Group by URLs? (y/n)")
    if group_by.upper() == 'Y':
        # Fetch all URLs from keys table, that belong to trace_id 
        cursor.execute("""SELECT URL, COUNT(id) count
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?
                        GROUP BY URL
                        ORDER BY COUNT(id) DESC""",[trace_id])
    else:
        # Fetch all URLs from keys table, that belong to trace_id 
        cursor.execute("""SELECT URL
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?""",[trace_id])
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def show_traces(cursor):
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
                      FROM Traces T, Trace_Entry K
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

def check_parent_hit():
    """
    Check which cache retrive last request
    """
    def read_last_row(file_path):
        """
        Read last row from given file
        """
        try:
            with open(file_path, "rb") as file:
                file.seek(0, 2)  # Move to the end of the file
                position = file.tell()
                buffer = bytearray()
                
                while position >= 0:
                    file.seek(position)
                    char = file.read(1)
                    if char == b'\n' and buffer:
                        break
                    buffer.extend(char)
                    position -= 1
                
                return buffer[::-1].decode("utf-8").strip()
        except Exception as e:
            return None

    # Read the last row
    last_row = read_last_row(MyConfig.log_file)
    if last_row is None:
        print (f"Error reading log file: {MyConfig.log_file}")
        return False

    # Check for "PARENT_HIT/{ip}" pattern
    match = re.search(r"PARENT_HIT/(\d{1,3}(?:\.\d{1,3}){3})", last_row)
    if match:
        return match.group(1)  # Return the IP address
    else:
        return "0"

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

        if cache_data:
            conn.commit()

            print(f"""Requst Fetched successfully from {cache_data[0]} at cost of {cache_data[1]}""")

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
    PROXIES = {
            "http": MyConfig.http_proxy,
            "https": MyConfig.https_proxy,
        }

    try:
        # Execute requsts to squid proxy
        response = requests.get(url, proxies=PROXIES,timeout=10)

        # Check if request failed
        if (not response.ok):
            print(f"Request {url} error - {response.status_code}")

            # Delete URL form traces entries and from Keys list
            cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
            cursor.execute("DELETE FROM Keys WHERE URL=?",[url])
            return 0
        else:

            # Get IP of parent cache that retrive the request
            cache_ip = check_parent_hit()
            
            if (cache_ip):
                # Gets cache data from caches table
                cursor.execute("Select * from Caches WHERE IP=?", cache_ip)
                row = cursor.fetchone()
                cache_id = row[0]

                # Insert request's data into requests table
                cursor.execute("""INSERT INTO Requests('URL','Cache_ID','Run_ID') 
                                VALUES (?,?,?)""",[url,cache_id,run_id])

                # Return cache name and cache access cost
                return (row[2], row[3])
            
            return 0
    except Exception as e:
        print(f"Request {url} error - {e}")

        # Delete URL form traces entries and from Keys list
        cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
        cursor.execute("DELETE FROM Keys WHERE URL=?",[url])
        
        return 0
    
def clear_cache(remote_ip):
    """
    Clear all cache data from the given remote cache IP
    """

    # Create an SSH client instance
    ssh_client = paramiko.SSHClient()
    
    # Automatically add the host key if not already known
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Get password to others caches users
    password = os.getenv('SQUID_PASS')

    try:
        # Connect to the remote machine
        ssh_client.connect(remote_ip, username=MyConfig.user, password=password)

        # Command to delete the Squid cache directory
        command = f"sudo find {MyConfig.cache_dir} -type f ! -name 'swap.state' -delete"

        # Execute the command to delete the directory
        stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)
        
        # Provide sudo password for the command (if needed)
        stdin.write(password + '\n')
        stdin.flush()

        # Wait for the command to complete
        exit_status = stdout.channel.recv_exit_status()
        
        # If exit_status is 0, its say that operation succeed
        if not exit_status:
            return True
        else:
            print(f"Error deleting {remote_ip} cache: {stderr.read().decode()}")
            return False
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Close the SSH connection
        ssh_client.close()

def clear_caches(cursor):
    """
    Clear all caches before making new trace
    """

    # Gets caches count for know if success to clear all
    cursor.execute("SELECT COUNT(id) FROM Caches")

    # The -1 is because the table contains also "miss" cache that isn't realy a cache
    caches_num = cursor.fetchone()[0] - 1

    # Gets all caches from caches table
    cursor.execute("SELECT * FROM Caches")
    caches = cursor.fetchall()

    # Run on all caches
    for cache in caches:
        if cache[2] != 'miss':
            # Try to clear this cache
            if clear_cache(cache[1]):
                print(f"{cache[2]} cache directory deleted successfully.")
                caches_num -= 1
            
            # If one cache clearing failed, its not continue to others
            else:
                break 

    # Return true only if secceed to clear all caches
    return not caches_num

def is_squid_up(cursor):
    """
    Check if squid upon all servers by checking request to google site from each
    """

    cursor.execute("SELECT IP FROM Caches WHERE id != 1")
    caches = cursor.fetchall()    
    proxy = {"https": MyConfig.https_proxy}

    URL = "https://www.google.com"

    try:
        response = requests.get(URL, proxies=proxy,timeout=10)

        # Check if proxy OK    
        if (response.ok):

            # Runs on all parents to check if they also OK
            for cache in caches:
                proxy = {"https": f'http://{cache[0]}:{MyConfig.squid_port}'}
                try:
                    response = requests.get(URL, proxies=proxy,timeout=10)

                    if (not response.ok):
                        print(f"Server {cache[0]} error: request failed")
                        return False
                except Exception as e:
                    print(f"Server {cache[0]} error: {e}")
                    return False
            return True
        else:
            print(f"proxy request failed")
            return False
    except Exception as e:
        print(f"proxy request failed: {e}")
        return False
    
def run_trace(conn, cursor):
    """
    Executes all requests for a specified trace 
    and logs the results into the 'Runs' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Check if squid works properly on all servers
    if is_squid_up(cursor):
    
        stop_loop = [False]  # Use a mutable object to modify within listener

       
                
        name = input("Insert run name: ")
        
        # Fetch all rows from the "Traces" table, with their keys count
        cursor.execute("""SELECT T.id ID, T.Name Name, 
                                COUNT(K.id) Keys, T.Last_Update Last_Update 
                        FROM Traces T, Trace_Entry K
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
        limit = int(input("Insert limit of requests to execute, or 0 to not limit: "))
        jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

        # Try to clear all caches before running trace
        if clear_caches(cursor):
            
            print("All caches cleared successfully")
        
            try:    
                # Create entry for the run, for generate and gets run id 
                # for insert in requests entries.
                # init End_time and total cost with dummies because they can't accept nulls
                cursor.execute("""INSERT INTO Runs('Name','Start_Time','End_time','Trace_ID', 'Total_Cost')
                                VALUES(?,?,?,?,0)""", [name,jerusalem_time,jerusalem_time,trace_id])
                
                # Get current run id
                cursor.execute("SELECT MAX(id) from Runs")
                row = cursor.fetchone()
                run_id = row[0] 

                # Get all trace's URLs
                cursor.execute("SELECT URL FROM Trace_Entry WHERE Trace_ID = ?", [trace_id])
                rows = cursor.fetchall()

                opp_code = 1

                try:
                    from pynput import keyboard

                    def on_press(key):
                        stop_loop[0] = key == keyboard.Key.esc

                    listener = keyboard.Listener(on_press=on_press)
                    listener.start()
                except Exception as e:
                    print(f"Failed to start keyboard listener: {e}")

                # Run on all trace URLs
                for row in rows:
                    if stop_loop[0]:

                        # Take only last char from input for ignore "Esc" that came before
                        opp_code = int(input("""What to do with this run:
1: Stop and save run
2: Stop without saving
3: Keep running
""")[-1])
                        if opp_code == 1 or opp_code == 2:
                            break
                        else:
                            stop_loop[0] = False 

                    # If requests succeed and there is limit, 
                    # decrease limit and check if reach it
                    if exectue_req(cursor, row[0], run_id) and limit > 0:
                        limit -= 1
                        if not limit:
                            break
                
                if opp_code != 2:

                    jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

                    # Update run entry with end time
                    cursor.execute("""UPDATE Runs
                    SET End_Time = ?
                    WHERE id = ?""",[jerusalem_time, run_id])

                    conn.commit()

                    print("Trace run successfully!")
                    
                    # Fetch current run from the "Runs" table, for show the result
                    cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                                            T.Name trace_name, COUNT(C.id) requests, 
                                            SUM(C.Access_Cost) total_cost, AVG(C.Access_Cost) average_cost
                                    FROM Runs RUN, Requests REQ, Caches C, Traces T  
                                    WHERE REQ.Run_ID = RUN.id AND 
                                    C.id = REQ.Cache_id AND 
                                    RUN.Trace_ID = T.id AND 
                                    RUN.id = ?""",[run_id])
                    row = cursor.fetchone()
                    
                    column_names = [description[0] for description in cursor.description]

                    # Display the data in a table format using PrettyTable
                    table = PrettyTable()
                    table.field_names = column_names  # Set column headers

                    # Add selected row  
                    table.add_row(row)
                    
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
    
def update_cache(conn, cursor):
    """
    Updates the specified fields of a cache entry in the 'Caches' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        cache_id (int): The ID of the cache to update.
    """
    cache_id = int(input("Choose cache ID to update: "))

    opp_code = 1
    while opp_code:
        opp_code = int(input("""Which field you want to change:
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

def delete_cache(conn, cursor):
    """
    Delete cache form caches table
    """

    cache_id = int(input("Choose cache id to delete: "))
    verify = input(f"Are you sure you want to delete cache number {cache_id} (y/n)? ")

    if verify.upper() == "Y":
        cursor.execute("DELETE FROM Caches WHERE id=?", [cache_id])
        conn.commit()

        print("Cache deleted successfully!")

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
4: Delete cache
0: Back to main menu
"""))    
        if opp_code == 1:
            show_caches(cursor)
        elif opp_code == 2:
            new_cache(conn, cursor)
        elif opp_code == 3:
            show_caches(cursor)
            update_cache(conn, cursor)
            show_caches(cursor)
        elif opp_code == 4:
            show_caches(cursor)
            delete_cache(conn, cursor)
            show_caches(cursor)
        elif opp_code != 0:
            # In case of invalid input
            print("Invalid option, please choose a valid number.")

# Register adapter for datetime objects to store them as strings in SQLite
def adapt_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Register the adapter for datetime
sqlite3.register_adapter(datetime, adapt_datetime)

conn = sqlite3.connect(MyConfig.db_file)
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
""")[-1])
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

conn.close()
print("ByeBye")
