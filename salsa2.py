import re
import urllib3
import warnings
import paramiko
from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from prettytable import PrettyTable
import requests
from DBAccess import DBAccess
from MyConfig import MyConfig
import os

def show_run(run_id : int):
    if run_id:
        # Fetch rows from the "Requests" table
        DBAccess.cursor.execute("""SELECT R.id, R.Time, R.URL
                          FROM Requests R JOIN CacheReq CR
                          ON R.id = CR.req_id
                          WHERE R.Run_ID = ? AND CR.accessed = 1
                          GROUP BY R.id""",[run_id])
        rows = DBAccess.cursor.fetchall()

        show_requsts_details(rows)

def show_runs():
    """ Fetches and displays all entries in the 'Runs' table"""

    # Fetch all rows from the "Runs" table
    DBAccess.cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                             T.Name trace_name, 0 requests, 
                             0 total_cost, 0 average_cost
                      FROM Runs RUN JOIN Traces T   
                      ON RUN.Trace_ID = T.id""")
    runs = DBAccess.cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    # Runs on run
    for run in runs:
        cost, reqNum = get_cost(run[0])
        if (reqNum):
            avg_cost = round(cost / reqNum, 3)

            row = [run[0], run[1], run[2], run[3], run[4], cost, reqNum, avg_cost]
            
            table.add_row(row)
    
    print(table)

    run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))

    show_run(run_id)
    
def show_keys(trace_id):    
    """
    Fetches and displays URLs associated with a specific Trace ID from the 'Keys' table.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        trace_id (int): The ID of the trace to fetch URLs for.
    """
    group_by = input("Group by URLs? (y/n)")
    if group_by.upper() == 'Y':
        # Fetch all URLs from keys table, that belong to trace_id 
        DBAccess.cursor.execute("""SELECT URL, COUNT(id) count
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?
                        GROUP BY URL
                        ORDER BY COUNT(id) DESC""",[trace_id])
    else:
        # Fetch all URLs from keys table, that belong to trace_id 
        DBAccess.cursor.execute("""SELECT URL
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?""",[trace_id])
    rows = DBAccess.cursor.fetchall()
    column_names = [description[0] for description in DBAccess.cursor.description]

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def show_traces():
    """
    Fetches and displays trace details, 
    including the number of keys and last update time.
    Allows the user to view details of a specific trace.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Traces" table
    DBAccess.cursor.execute("""SELECT T.id ID, T.Name Name, 
                             COUNT(K.id) Keys, T.Last_Update Last_Update 
                      FROM Traces T, Trace_Entry K
                      WHERE T.id = K.Trace_ID
                      GROUP BY T.id""")
    rows = DBAccess.cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    # Get from user trace id to show it's content
    trace_id = int(input("""Select trace ID to show it content, or 0 to go back to main menu: """))

    if trace_id:
        show_keys(trace_id)
    
def show_requsts_details(requests):
    # Fetch column names for the table
    column_names = ['Time', 'URL', 'Indications', 'Accessed', 'Resolution', 'Hit?', 'Cost']
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for request in requests:
        DBAccess.cursor.execute("""SELECT indication, accessed, resolution, Name, Access_Cost
                          FROM CacheReq R JOIN Caches C
                          ON R.cache_id = C.id
                          WHERE R.req_id = ? """, [request[0]])
        
        caches = DBAccess.cursor.fetchall()
        indicators = "["
        accessed = "["
        resolution = "["
        hit = False
        cost = 0

        for cache in caches:
            if cache[0]:
                if len(indicators) > 1:
                    indicators += ","
                indicators += cache[3]
            if cache[1]:
                if len(accessed) > 1:
                    accessed += ","
                accessed += cache[3]
                cost += cache[4]
            if cache[2]:
                if len(resolution) > 1:
                    resolution += ","
                resolution += cache[3]
            
            hit = hit or cache[1] & cache[2]

        cost += (not hit) * get_miss_cost() 
        
        indicators += "]"
        accessed += "]"
        resolution += "]"

        table.add_row([request[1], request[2], indicators, accessed, resolution, hit, cost])
    
    print(table)

def show_requsts():
    """
    Fetches and displays a specified number of the most recent requests, 
    including cache details.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    count = int(input("How match requsts you want to show?: "))
     
    # Fetch rows from the "Requests" table, limiting last {count}
    DBAccess.cursor.execute("""SELECT R.id, R.Time, R.URL
                               FROM Requests R JOIN CacheReq CR
                               ON R.id = CR.req_id
                               WHERE CR.accessed = 1
                               GROUP BY R.id
                               ORDER BY R.Time DESC LIMIT ?""", [count])
    req_ids = DBAccess.cursor.fetchall()
    req_ids.reverse()

    show_requsts_details(req_ids)
    
def get_miss_cost():

    DBAccess.cursor.execute("""SELECT Access_Cost
                      FROM Caches
                      WHERE Name = 'miss'""")
    
    result = DBAccess.cursor.fetchone()[0]

    return result

def exectue_single_req():
    """
    Executes a single request for a given URL and logs it into the 'Requests' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    url = input("Enter URL: ")

    try:
        # Execute request without run id
        reqID = exectue_req(url, 0)

        if reqID:

            DBAccess.cursor.execute("""SELECT Caches.Name, Caches.Access_Cost, CacheReq.resolution
                              FROM CacheReq, Caches
                              WHERE CacheReq.cache_id = Caches.id AND
                                    CacheReq.req_id = ? AND
                                    CacheReq.accessed = 1""",[reqID])
            
            result = DBAccess.cursor.fetchone()

            if (result):
                if (result[2]):
                    name = result[0]
                    cost = result[1]
                else:
                    name = "miss"
                    cost = get_miss_cost()

                print(f"""Requst Fetched successfully from {name} at cost of {cost}""")

    except sqlite3.DatabaseError as e:
        # If request fails, print the exact error message from SQLite
        print(f"Request failed: {e}")

def exectue_req(url : str, run_id : int):
    """
    Execute request to squid 
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        url (str): The URL for the request.
        run_id (int): The ID of the run associated with the request.
    
    Returns:
        tuple: The cache name and its access cost.
    """
    PROXIES = {
            "http": MyConfig.http_proxy
        }

    try:
        jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

        # Insert request's data into requests table
        DBAccess.cursor.execute("""INSERT INTO Requests('Time', 'URL', 'Run_ID') 
                        VALUES (?,?,?)""",[jerusalem_time, url,run_id])
        
        # Need to close connection before continuing because squid need to update DB
        DBAccess.conn.commit()
        DBAccess.close()

        # Execute requsts to squid proxy
        response = requests.get(url, proxies=PROXIES,timeout=10, verify=False)

        # Reopen DB 
        DBAccess.open()       

        # Check if request failed
        if (not response.ok):
            print(f"Request {url} error - {response.status_code}")

            # Delete URL form traces entries and from Keys list
            # DBAccess.cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
            # DBAccess.cursor.execute("DELETE FROM Keys WHERE URL=?",[url])

            DBAccess.conn.commit()
            
            return None
        else:    
            
            DBAccess.cursor.execute("SELECT MAX(id) FROM Requests")
            reqID = DBAccess.cursor.fetchone()[0]

            # Return reqID
            return (reqID)
        
    except Exception as e:
        print(f"Request {url} error - {e}")

        DBAccess.open()
        
        # # Delete URL form traces entries and from Keys list
        # DBAccess.cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
        # DBAccess.cursor.execute("DELETE FROM Keys WHERE URL=?",[url])
        
        return None
    
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

def clear_caches():
    """
    Clear all caches before making new trace
    """

    # Gets caches count for know if success to clear all
    DBAccess.cursor.execute("SELECT COUNT(id) FROM Caches")

    # The -1 is because the table contains also "miss" cache that isn't realy a cache
    caches_num = DBAccess.cursor.fetchone()[0] - 1

    # Gets all caches from caches table
    DBAccess.cursor.execute("SELECT * FROM Caches")
    caches = DBAccess.cursor.fetchall()

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

def is_squid_up():
    """
    Check if squid upon all servers by checking request to google site from each
    """

    DBAccess.cursor.execute("SELECT IP FROM Caches WHERE id != 1")
    caches = DBAccess.cursor.fetchall()    
    proxy = {"http": MyConfig.http_proxy}

    URL = "http://www.google.com" 

    try:
        response = requests.get(URL, proxies=proxy,timeout=10,verify=False)

        # Check if proxy OK    
        if (response.ok):

            # Runs on all parents to check if they also OK
            for cache in caches:
                proxy = {"http": f'http://{cache[0]}:{MyConfig.squid_port}'}
                try:
                    response = requests.get(URL, proxies=proxy,timeout=10,verify=False)

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
    
def get_cost(run_id : int):
    # Select all requests that accessed
    DBAccess.cursor.execute("""SELECT DISTINCT R.id
                      FROM Requests R JOIN CacheReq CR
                      ON R.id = CR.req_id
                      WHERE R.run_id = ? AND CR.accessed = 1""", [run_id])
    
    requests = DBAccess.cursor.fetchall()
    req_count = len(requests)
    total_cost = 0

    for request in requests:

        # Select sun of cost and resolution of all accessed caches
        DBAccess.cursor.execute("""SELECT SUM(CR.resolution), SUM(C.Access_Cost)
                          FROM CacheReq CR JOIN Caches C
                          ON CR.cache_id = C.id                          
                          WHERE CR.req_id = ? AND CR.accessed = 1""", [request[0]])
        
        caches = DBAccess.cursor.fetchone()

        if (len(caches) > 1):
            # Total cost is costs sum + miss cost if no resolution found for accessed caches
            total_cost += caches[1] + (1 - min(1, caches[0])) * get_miss_cost()
        
    return [total_cost, req_count]

    
def run_trace():
    """
    Executes all requests for a specified trace 
    and logs the results into the 'Runs' table.
    
    Args:
        conn (sqlite3.Connection): The database connection for committing changes.
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Check if squid works properly on all servers
    if is_squid_up():
                
        name = input("Insert run name: ")
        
        # Fetch all rows from the "Traces" table, with their keys count
        DBAccess.cursor.execute("""SELECT T.id ID, T.Name Name, 
                                COUNT(K.id) Keys, T.Last_Update Last_Update 
                        FROM Traces T, Trace_Entry K
                        WHERE T.id = K.Trace_ID
                        GROUP BY T.id""")
        rows = DBAccess.cursor.fetchall()
        
        # Fetch column names for the table
        column_names = [description[0] for description in DBAccess.cursor.description]
        
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
        if True: #clear_caches():           
            #print("All caches cleared successfully")
        
            try:    
                # Create entry for the run, for generate and gets run id 
                # for insert in requests entries.
                # init End_time and total cost with dummies because they can't accept nulls
                DBAccess.cursor.execute("""INSERT INTO Runs('Name','Start_Time','End_time','Trace_ID', 'Total_Cost')
                                VALUES(?,?,?,?,0)""", [name,jerusalem_time,jerusalem_time,trace_id])
                
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

                    req_id = exectue_req(row[0], run_id)

                    if req_id and limit > 0:
                        limit -= 1

                        if not limit:
                            break                

                jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

                # Update run entry with end time
                DBAccess.cursor.execute("""UPDATE Runs
                SET End_Time = ?
                WHERE id = ?""",[jerusalem_time, run_id])

                DBAccess.conn.commit()

                print("Trace run successfully!")
                
                cost, reqNum = get_cost(run_id)

                if reqNum:
                    avg_cost = round(cost / reqNum, 3)

                    # Fetch current run from the "Runs" table, for show the result
                    DBAccess.cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                                            T.Name trace_name, ? requests, ? Total_cost, ? Avarege_cost
                                    FROM Runs RUN JOIN Traces T  
                                    ON RUN.Trace_ID = T.id
                                    WHERE RUN.id = ?""",[reqNum, cost, avg_cost, run_id])
                    row = DBAccess.cursor.fetchone()
                    
                    column_names = [description[0] for description in DBAccess.cursor.description]

                    # Display the data in a table format using PrettyTable
                    table = PrettyTable()
                    table.field_names = column_names  # Set column headers

                    # Add selected row  
                    table.add_row(row)
                    
                    print(table)

                    show_run(run_id)

            except sqlite3.DatabaseError as e:
                # If insertion fails, print the exact error message from SQLite
                print(f"Trace failed: {e}")  

def show_caches():
    """
    Fetches and displays all cache details from the 'Caches' table.
    
    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
    """

    # Fetch all rows from the "Caches" table
    DBAccess.cursor.execute("SELECT * FROM Caches")
    rows = DBAccess.cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

def new_cache():
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
        DBAccess.cursor.execute("""INSERT INTO Caches('IP','NAME','Access_Cost') 
                          VALUES (?,?,?)""",[ip,name,cost])
        DBAccess.conn.commit()
        print("Cache added successfully!")
        show_caches()
    except sqlite3.DatabaseError as e:
        # If insertion fails, print the exact error message from SQLite
        print(f"Insertion failed: {e}")
    
def update_cache():
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
                DBAccess.cursor.execute("""UPDATE Caches 
                                  SET IP = ? 
                                  WHERE id = ?""",[ip, cache_id])
            elif opp_code == 2:
                name = input("Insert cache name: ")
                DBAccess.cursor.execute("""UPDATE Caches 
                                  SET Name = ? 
                                  WHERE id = ?""",[name, cache_id])
            elif opp_code == 3:
                cost = int(input("Insert cache access cost: "))
                DBAccess.cursor.execute("""UPDATE Caches 
                                  SET Access_Cost = ? 
                                  WHERE id = ?""",[cost, cache_id])
            elif opp_code != 0:
                # In case of invalid input
                print("Invalid option, please choose a valid number.")        

            DBAccess.conn.commit()
            print("Cache updated successfully!")
            show_caches()

        except sqlite3.DatabaseError as e:
            # If insertion fails, print the exact error message from SQLite
            print(f"Update failed: {e}")

def delete_cache():
    """
    Delete cache form caches table
    """

    cache_id = int(input("Choose cache id to delete: "))
    verify = input(f"Are you sure you want to delete cache number {cache_id} (y/n)? ")

    if verify.upper() == "Y":
        DBAccess.cursor.execute("DELETE FROM Caches WHERE id=?", [cache_id])
        DBAccess.conn.commit()

        print("Cache deleted successfully!")

def manage_caches():
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
            show_caches()
        elif opp_code == 2:
            new_cache()
        elif opp_code == 3:
            show_caches()
            update_cache()
            show_caches()
        elif opp_code == 4:
            show_caches()
            delete_cache()
            show_caches()
        elif opp_code != 0:
            # In case of invalid input
            print("Invalid option, please choose a valid number.")

def fill_caches():
    """
    Fills the 'Caches' table in an SQLite database with data parsed from a Squid
    configuration file.
    """
    try:

        DBAccess.cursor.execute("DELETE FROM Caches")

        with open(MyConfig.conf_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("miss_penalty"):
                    parts = line.split()
                    if len(parts) < 2:
                        continue # Skip malformed lines

                    DBAccess.cursor.execute(
                    "INSERT INTO Caches (IP, Name, Access_Cost) VALUES (?, ?, ?)",
                    ('0', 'miss', parts[1]))

                elif line.startswith("cache_peer "):
                    parts = line.split()
                    if len(parts) < 2:
                        continue # Skip malformed lines

                    ip = parts[1]
                    name = None
                    access_cost = None

                    # Use regex to find name= and access-cost= as they might not be in fixed positions
                    name_match = re.search(r'name=(\S+)', line)
                    if name_match:
                        name = name_match.group(1)

                    access_cost_match = re.search(r'access-cost=(\S+)', line)
                    if access_cost_match:
                        try:
                            access_cost = float(access_cost_match.group(1))
                        except ValueError:
                            print(f"Warning: Could not parse access-cost for line: {line}")
                            continue # Skip this entry if access_cost is invalid

                    if ip and name and access_cost is not None:
                        try:
                            DBAccess.cursor.execute(
                                "INSERT OR IGNORE INTO Caches (IP, Name, Access_Cost) VALUES (?, ?, ?)",
                                (ip, name, access_cost)
                            )
                        except sqlite3.IntegrityError as e:
                            print(f"Error inserting data for IP {ip}, Name {name}: {e}")
                    else:
                        print(f"Warning: Missing IP, Name, or Access_Cost in line: {line}")

        DBAccess.conn.commit()
        print(f"Successfully populated Caches table from {MyConfig.conf_file}")

    except FileNotFoundError:
        print(f"Error: Configuration file not found at {MyConfig.conf_file}")
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Register adapter for datetime objects to store them as strings in SQLite
def adapt_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

try:
    # Register the adapter for datetime
    sqlite3.register_adapter(datetime, adapt_datetime)

    DBAccess.open()
    fill_caches()
    warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

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
            show_runs()
        elif opp_code == 2:
            show_traces()
        elif opp_code == 3:
            show_requsts()
        elif opp_code == 4:
            exectue_single_req()
        elif opp_code == 5:
            run_trace()
        elif opp_code == 6:
            manage_caches()
        elif opp_code != 0:
            print("Invalid option, please choose a valid number.")

    print("ByeBye")
finally:
    DBAccess.close()