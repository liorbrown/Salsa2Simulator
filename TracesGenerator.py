from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig
import random

print("################## Welcome to traces generator #####################")
traces_name = input("Insert traces name: ")
traces = int(input("Insert number of traces to create: "))

conn = sqlite3.connect(MyConfig.db_file)
cursor = conn.cursor()
cursor.execute("SELECT MAX(id) FROM Keys")
keys = cursor.fetchone()[0]

entries = int(input("Insert number of entries to create in each trace: "))

if entries > keys:
    print(f"There are only {keys} URLs avialible")
    exit

for trace_index in range(traces):
    cursor.execute("INSERT INTO Traces(Name, Last_Update) VALUES (?, current_timestamp)", 
                   [traces_name + str(trace_index + 1)])
    cursor.execute("SELECT MAX(id) FROM Traces")
    trace_id = cursor.fetchone()[0]

    start_id = random.randint(1, keys - entries + 1)

    for entry_index in range(entries):
        key_id = random.randint(start_id, start_id + entries)
        cursor.execute("""INSERT INTO Trace_Entry(URL, Trace_ID)                     
                          SELECT URL, ? FROM Keys WHERE id=?""",[trace_id ,key_id])

conn.commit()

