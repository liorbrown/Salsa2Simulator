from datetime import datetime
import sys
import sqlite3
from zoneinfo import ZoneInfo
from MyConfig import MyConfig

def getCacheID(cursor : sqlite3.Cursor, name : str):
    cursor.execute("""SELECT id FROM Caches WHERE Name = ?""", [str])
    return cursor.fetchone()

if __name__ == "__main__":
    args = sys.argv[1:]
    n = len(args)

    if (n < 5 or n % 4 != 1):
        print("Invalid number of arguments")
    else:
        try:
            conn = sqlite3.connect(MyConfig.db_file)
            cursor = conn.cursor()
            jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

            cursor.execute("""SELECT MAX(id) FROM Requests 
                            WHERE URL = ? AND
                            ? - Time < 60""", [args[0], jerusalem_time])
            
            req_id = cursor.fetchone()

            if (not req_id):
                raise SystemExit(f"Request {args[0]} not found!")
            else:
                for c in range(1, n, 4):
                    cache_id = getCacheID(cursor, args[c])

                    if (not cache_id):
                        print(f"Cache {args[c]} not found!")
                        exit

                    cursor.execute("""INSERT INTO ChaceReq 
                                (req_id, cache_id, indicator, accessed, resolution)
                                VALUES (?,?,?,?,?)""",
                                [req_id, cache_id, args[c+1], args[c+2], args[c+3]])
                
                conn.commit()
        except:
            print(sys.exc_info()[0])
        
        finally:
            conn.close()


