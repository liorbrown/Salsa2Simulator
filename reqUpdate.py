from datetime import datetime, timedelta
import sys
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig

def getReqID(cursor : sqlite3.Cursor, URL : str):
    
    cursor.execute("""SELECT MAX(id), Time 
                       FROM Requests
                       WHERE URL = ?""",[URL])
            
    req_data = cursor.fetchone()

    if (not req_data):
        return None
    else:
        israel_timezone = ZoneInfo("Asia/Jerusalem")
        req_time_naive = datetime.strptime(req_data[1], '%Y-%m-%d %H:%M:%S')
        req_time = req_time_naive.replace(tzinfo=israel_timezone)
        now_time = datetime.now(israel_timezone)

        if ((now_time - req_time).seconds > 60):
            return None
        else:
            return req_data[0]

def getCacheID(cursor : sqlite3.Cursor, name : str):
    cursor.execute("""SELECT id FROM Caches WHERE Name = ?""", [name])
    return cursor.fetchone()[0]

if __name__ == "__main__":
    args = sys.argv[1:]
    n = len(args)

    if (n < 5 or n % 4 != 1):
        print("Invalid number of arguments")
    else:
        try:
            conn = sqlite3.connect(MyConfig.db_file)
            cursor = conn.cursor()
            URL = args[0]
            req_id = getReqID(cursor, URL)

            if (not req_id):
                raise SystemExit(f"Request {URL} not found!")
            else:
                for c in range(1, n, 4):
                    cache_id = getCacheID(cursor, args[c])

                    if (not cache_id):
                        print(f"Cache {args[c]} not found!")
                        exit

                    cursor.execute("""INSERT INTO CacheReq 
                                (req_id, cache_id, indication, accessed, resolution)
                                VALUES (?,?,?,?,?)""",
                                [req_id, cache_id, args[c+1], args[c+2], args[c+3]])
                
                conn.commit()
        except sqlite3.DatabaseError as e:
            print(e)
        
        finally:
            conn.close()


