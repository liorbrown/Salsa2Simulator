import sqlite3
from MyConfig import MyConfig

class DBAccess:
    conn : sqlite3.Connection = None
    cursor : sqlite3.Cursor = None

    @staticmethod
    def open() :
        if (not DBAccess.conn):
            DBAccess.conn = sqlite3.connect(MyConfig.db_file)
            DBAccess.cursor = DBAccess.conn.cursor()

    @staticmethod
    def close():
        if (DBAccess.conn):
            DBAccess.conn.close()
            DBAccess.conn = None
            DBAccess.cursor = None

    

