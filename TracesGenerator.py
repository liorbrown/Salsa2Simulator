from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig
import random

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
traces_name = input("Insert traces name: ")
traces = int(input("Insert number of traces to create: "))

conn = sqlite3.connect(MyConfig.db_file)
cursor = conn.cursor()

# Retrieve the maximum ID from the Keys table to determine available key range
cursor.execute("SELECT MAX(id) FROM Keys")
keys = cursor.fetchone()[0]

entries = int(input("Insert number of entries to create in each trace: "))

# Check if the requested number of entries exceeds the available keys
if entries > keys:
    print(f"There are only {keys} URLs avialible")
    exit

# Loop to create the specified number of traces
for trace_index in range(traces):
    # Insert a new trace with a unique name
    cursor.execute("INSERT INTO Traces(Name) VALUES (?)", 
                   [traces_name + str(trace_index + 1)])
    
    # Get the ID of the newly created trace
    cursor.execute("SELECT MAX(id) FROM Traces")
    trace_id = cursor.fetchone()[0]

    # Randomly select a starting key ID for the entries
    start_id = random.randint(1, keys - entries + 1)

    # Loop to insert the entries for the current trace
    for entry_index in range(entries):
        # Randomly select a key ID for the current entry
        key_id = random.randint(start_id, start_id + entries)

        # Insert the URL corresponding to the key_id into the Trace_Entry table
        cursor.execute("""INSERT INTO Trace_Entry(URL, Trace_ID)                     
                          SELECT URL, ? FROM Keys WHERE id=?""",[trace_id ,key_id])

    # Update the Last_Update field for the current trace with the current time
    jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
    cursor.execute("""UPDATE Traces SET Last_Update=? WHERE id=?""",
                   [jerusalem_time, trace_id])

conn.commit()

