"""Database access layer for Salsa2 Simulator."""
import sqlite3
from config.config import MyConfig


class DBAccess:
    """Manages database connections and cursor for SQLite database."""
    
    conn: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None

    @staticmethod
    def open():
        """Open a database connection if not already open."""
        if not DBAccess.conn:
            config = MyConfig()
            DBAccess.conn = sqlite3.connect(config.get_key('db_file'))
            DBAccess.cursor = DBAccess.conn.cursor()

    @staticmethod
    def close():
        """Close the database connection if open."""
        if DBAccess.conn:
            DBAccess.conn.close()
            DBAccess.conn = None
            DBAccess.cursor = None
