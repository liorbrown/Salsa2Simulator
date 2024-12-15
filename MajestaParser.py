from datetime import datetime
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig

conn = sqlite3.connect(MyConfig.db_file)
cursor = conn.cursor()

path = input("Insert file path: ")
name = input("Insert trace name: ")
cursor.execute("INSERT INTO Traces(Name, Last_Update) VALUES (?, current_timestamp)", [name])
cursor.execute("SELECT MAX(id) FROM Traces")
id = cursor.fetchone()[0]

with open(path, 'r') as file:
    for line in file:
        row = line.split(',')
        url = "https://www." + row[2]

        cursor.execute("INSERT INTO Keys(URL, Trace_ID) VALUES (?,?)",[url, id])

jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))
cursor.execute("""UPDATE Traces SET Last_Update=? WHERE id=?""",[jerusalem_time, id])
conn.commit()