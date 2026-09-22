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

            # The rest of the schema is still hand-managed (see other tables
            # in the live DB), but this one gets a source-of-truth definition
            # in code since it's the table Inter-Node Traffic writes to.
            # IF NOT EXISTS makes this a no-op against the existing live DB.
            DBAccess.cursor.execute("""
                CREATE TABLE IF NOT EXISTS "Requests" (
                    id INTEGER PRIMARY KEY,
                    Time TIMESTAMP,
                    URL TEXT,
                    Cache_ID INTEGER,
                    Run_ID INTEGER,
                    elapsed_ms INTEGER,
                    download_bytes INTEGER NOT NULL DEFAULT 0,
                    parents_queries INTEGER NOT NULL DEFAULT 0,
                    parents_bytes INTEGER NOT NULL DEFAULT 0
                )
            """)
            DBAccess.conn.commit()

    @staticmethod
    def close():
        """Close the database connection if open."""
        if DBAccess.conn:
            DBAccess.conn.close()
            DBAccess.conn = None
            DBAccess.cursor = None
