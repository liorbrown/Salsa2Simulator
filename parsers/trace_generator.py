from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
import sys
import os
# Add parent directory to Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_access import DBAccess
import random
import requests

"""
This script generates random trace and its entries in the database. 
It selecting URLs randomly from the 'Keys' table, 
in a way that make some URLs to apear few times
"""

# Register adapter for datetime objects to store them as strings in SQLite
def adapt_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Register the adapter for datetime
sqlite3.register_adapter(datetime, adapt_datetime)

print("################## Welcome to traces generator #####################")

traces_name = input("Insert traces name: ").strip()
if not traces_name:
    print("Error: Trace name cannot be empty.")
    exit()

try:
    traces = int(input("Insert number of traces to create: "))
    if traces <= 0:
        print("Error: Number of traces must be positive.")
        exit()
except ValueError:
    print("Error: Please enter a valid number for traces.")
    exit()

# Open database connection using centralized DBAccess
DBAccess.open()
conn = DBAccess.conn
cursor = DBAccess.cursor

# Retrieve the maximum ID from the Keys table to determine available key range
cursor.execute("SELECT MAX(id) FROM URLs")
keys_result = cursor.fetchone()[0]

if not keys_result:
    print("Error: No URLs found in Keys table. Please add URLs first.")
    DBAccess.close()
    exit()

keys = keys_result

try:
    entries = int(input("Insert number of entries to create in each trace: "))
    if entries <= 0:
        print("Error: Number of entries must be positive.")
        DBAccess.close()
        exit()
except ValueError:
    print("Error: Please enter a valid number for entries.")
    DBAccess.close()
    exit()

# Check if the requested number of entries exceeds the available keys
if entries > keys:
    print(f"There are only {keys} URLs avialible")
    exit

# Loop to create the specified number of traces
for trace_index in range(traces):
    trace_name = traces_name + str(trace_index + 1)
    print(f"Starting create {trace_name}")

    # Insert a new trace with a unique name
    cursor.execute("INSERT INTO Traces(Name) VALUES (?)", [trace_name])
    
    # Get the ID of the newly created trace
    cursor.execute("SELECT MAX(id) FROM Traces")
    trace_id = cursor.fetchone()[0]

    # Randomly select a starting key ID for the entries
    ids_sample = random.sample(range(1, keys + 1), entries)

    ca_bundle = '/etc/ssl/certs/ca-certificates.crt'
    inserted = 0

    # Loop to insert the entries for the current trace
    while inserted < entries:
        # Randomly select a key ID for the current entry
        url_id = ids_sample[random.randint(0, entries - 1)]
        cursor.execute("SELECT URL FROM URLs WHERE id=?", [url_id])
        url = cursor.fetchone()[0]

        try:
            response = requests.get(url, timeout=5, 
                              verify=ca_bundle, allow_redirects=False)

            if response.status_code < 300:
                # Insert the URL corresponding to the key_id into the Trace_Entry table
                cursor.execute("""INSERT INTO Trace_Entry(URL, Trace_ID) VALUES (?,?)""",[url, trace_id])

                inserted += 1
                print(f"Inserted ({inserted}/{entries})")
        except: pass

    # Update the Last_Update field for the current trace with the current time
    jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    cursor.execute("""UPDATE Traces SET Last_Update=? WHERE id=?""",
                   [jerusalem_time, trace_id])
    
    conn.commit()
