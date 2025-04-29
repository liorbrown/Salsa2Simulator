from datetime import datetime
import sys
import sqlite3
from zoneinfo import ZoneInfo
from DBAccess import DBAccess

def getReqID(URL : str):
    """
    Retrieves the most recent request ID from the 'Requests' table for a given URL,
    only if the request was made within the last 60 seconds.

    Args:
        URL (str): The URL to search for in the 'Requests' table.

    Returns:
        int: The maximum request ID if a recent request matching the URL is found,
             otherwise None.
    """
    # Execute a SQL query to find the maximum ID and timestamp for entries where the URL matches the input.
    DBAccess.cursor.execute("""SELECT MAX(id), Time
                        FROM Requests
                        WHERE URL LIKE ?""", [f"%{URL}%"])

    # Fetch the first row of the result.
    req_data = DBAccess.cursor.fetchone()

    # Check if any data was returned or if the maximum ID is None.
    if (not req_data or not req_data[0]):
        return None
    else:
        # Define the timezone for Israel.
        israel_timezone = ZoneInfo("Asia/Jerusalem")
        # Parse the timestamp from the database into a datetime object (initially naive).
        req_time_naive = datetime.strptime(req_data[1], '%Y-%m-%d %H:%M:%S')
        # Make the datetime object timezone-aware by associating it with the Israeli timezone.
        req_time = req_time_naive.replace(tzinfo=israel_timezone)
        # Get the current time, also timezone-aware in the Israeli timezone.
        now_time = datetime.now(israel_timezone)

        # Check if the time difference between the current time and the request time is greater than 60 seconds.
        if ((now_time - req_time).seconds > 60):
            return None # Return None if the request is older than 60 seconds.
        else:
            return req_data[0] # Return the request ID if it's within the last 60 seconds.

def getCacheID(name : str):
    """
    Retrieves the ID of a cache from the 'Caches' table based on its name.

    Args:
        name (str): The name of the cache to search for.

    Returns:
        int: The ID of the cache.
    """
    # Execute a SQL query to select the ID of the cache with the given name.
    DBAccess.cursor.execute("""SELECT id FROM Caches WHERE Name = ?""", [name])

    result = DBAccess.cursor.fetchone()

    if result:
        # Fetch the first row and return the first element (the ID).
        return result[0]

if __name__ == "__main__":
    # Get the command-line arguments, excluding the script name.
    args = sys.argv[1:]
    # Get the number of arguments.
    n = len(args)

    # Print a message indicating the start of the script execution with the provided arguments.
    print(f"Start executing req update for: {args}")

    # Check if the number of arguments is less than 5 or if the number of arguments (excluding the first) is not a multiple of 4.
    if (n < 5 or n % 4 != 1):
        print("Invalid number of arguments")
        # Expected arguments: URL, then groups of (cache_name, indication, accessed, resolution)
    else:
        try:
            # Connect to the SQLite database specified in the MyConfig file.
            DBAccess.open()
            
            # The first argument is expected to be the URL.
            URL = args[0]
            # Retrieve the request ID using the getReqID function.
            req_id = getReqID(URL)

            # Check if a valid request ID was found.
            if (not req_id):
                print(f"Request {URL} not found!")
            else:
                # Iterate through the remaining arguments in steps of 4, starting from the second argument (index 1).
                for c in range(1, n, 4):
                    # The current argument is expected to be the cache name.
                    cache_name = args[c]
                    # Retrieve the cache ID using the getCacheID function.
                    cache_id = getCacheID(cache_name)

                    # Check if a valid cache ID was found.
                    if (not cache_id):
                        print(f"Cache {cache_name} not found!")
                        exit # Exit the script if a cache is not found.

                    # Execute an SQL INSERT statement to add a new entry into the 'CacheReq' table.
                    DBAccess.cursor.execute("""INSERT INTO CacheReq
                                        (req_id, cache_id, indication, accessed, resolution)
                                        VALUES (?,?,?,?,?)""",
                                    [req_id, cache_id, args[c+1], args[c+2], args[c+3]])
                # Commit the changes made to the database.
                DBAccess.conn.commit()

                # Print a success message indicating that the request was updated successfully.
                print(f"Request {args} updated successfuly!")

        except sqlite3.DatabaseError as e:
            # Catch any database-related errors and print the error message.
            print(e)

        finally:
            DBAccess.close()