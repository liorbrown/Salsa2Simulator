"""
This script inserts trace data into a SQLite database.
It processes a user-provided CSV file, constructs URLs, and updates the database with trace metadata and keys.
Ensure the database schema and `MyConfig` settings are correctly configured before running.
"""

from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig

# Establish a connection to the SQLite database
conn = sqlite3.connect(MyConfig.db_file)
cursor = conn.cursor()

# Get user inputs for file path and trace name
path = "httpSites"
name = "httpTrace"

# Insert a new trace record into the Traces table
cursor.execute("INSERT INTO Traces(Name) VALUES (?)",[name])

 # Get the ID of the newly created trace
cursor.execute("SELECT MAX(id) FROM Traces")
trace_id = cursor.fetchone()[0]

# Read and process the provided file
with open(path, 'r') as file:
    for line in file:

        # Insert each URL and the associated trace ID into the Keys table
        cursor.execute("INSERT INTO Trace_Entry(URL, Trace_ID) VALUES (?,?)",[line.strip(),trace_id])

# Update the Last_Update field of the trace with the current time in Jerusalem timezone
jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
cursor.execute("""UPDATE Traces SET Last_Update=? WHERE id=?""",
                   [jerusalem_time, trace_id])

# Commit the changes to the database
conn.commit()
