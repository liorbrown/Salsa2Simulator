"""
This script inserts trace data into a SQLite database.
It processes a user-provided CSV file, constructs URLs, and updates the database with trace metadata and keys.
Ensure the database schema and `MyConfig` settings are correctly configured before running.
"""

from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from database.db_access import DBAccess

# Open database connection using centralized DBAccess
DBAccess.open()
conn = DBAccess.conn
cursor = DBAccess.cursor

# Get user inputs for file path and trace name
path = input("Insert file path: ")
name = input("Insert trace name: ")

# Insert a new trace record into the Traces table
cursor.execute("INSERT INTO URLs_Lists(Name, Last_Update) VALUES (?, current_timestamp)", [name])

# Retrieve the ID of the newly inserted trace
cursor.execute("SELECT MAX(id) FROM URLs_Lists")
id = cursor.fetchone()[0]

# Read and process the provided CSV file
with open(path, 'r') as file:
    for line in file:
        row = line.split(',')
        url = "https://www." + row[2]  # Construct the URL from the third column

        # Insert each URL and the associated trace ID into the Keys table
        cursor.execute("INSERT INTO Keys(URL, Trace_ID) VALUES (?,?)",[url, id])

# Update the Last_Update field of the trace with the current time in Jerusalem timezone
jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
cursor.execute("""UPDATE URLs_Lists SET Last_Update=? WHERE id=?""",[jerusalem_time, id])

# Commit the changes to the database
conn.commit()
