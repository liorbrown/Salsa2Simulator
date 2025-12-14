"""Data access layer for UI display functions.

This module handles all database queries for the UI layer,
following the separation of concerns principle.
"""
from typing import List, Tuple
from database.db_access import DBAccess
# cache registry functions are imported locally in methods to avoid name shadowing

class UIRepository:
    """Repository pattern for UI data access."""
    
    @staticmethod
    def get_runs_by_id(run_id) -> List[Tuple]:
        """Get all runs with trace information.
        
        Args:
            run_id: The run ID

        Returns:
            List of tuples: (run_id, name, start_time, end_time, salsa_v, miss_penalty, trace_name)
        """

        DBAccess.cursor.execute(f"""
            SELECT 
                RUN.id, 
                RUN.Name, 
                RUN.Start_Time, 
                RUN.End_Time, 
                RUN.salsa_v, 
                RUN.miss_penalty, 
                caches.count,
                caches.cost,
                COUNT(*),
                AVG(REQ.elapsed_ms),
                AVG(REQ.download_bytes),
                T.Name
            FROM Runs RUN JOIN Traces T ON RUN.Trace_ID = T.id
            JOIN Requests REQ
            LEFT JOIN (
                SELECT COUNT(*) count, COUNT(DISTINCT Access_Cost) cost
                FROM Caches
                WHERE Run_ID = ?
            ) caches
            WHERE RUN.id = ? AND REQ.run_id = ?""", [run_id, run_id, run_id])

        return DBAccess.cursor.fetchall()
    
    @staticmethod
    def get_runs(limit) -> List[Tuple]:
        """Get all runs with trace information.
        
        Args:
            limit: Maximum number of runs to return
        
        Returns:
            List of tuples: (run_id, name, start_time, end_time, salsa_v, miss_penalty,
                           cache_count, request_count, total_elapsed_ms, trace_name)
        """

        DBAccess.cursor.execute(f"""
            SELECT 
                RUN.id, 
                RUN.Name, 
                RUN.Start_Time, 
                RUN.End_Time, 
                RUN.salsa_v,
                RUN.miss_penalty, 
                caches.count,
                caches.cost,
                COUNT(*),
                AVG(REQ.elapsed_ms),
                AVG(REQ.download_bytes),
                T.Name
            FROM Runs RUN JOIN Traces T ON RUN.Trace_ID = T.id
            JOIN Requests REQ ON REQ.run_id = RUN.id
            LEFT JOIN (
                SELECT Run_ID, COUNT(*) count, COUNT(DISTINCT Access_Cost) cost
                FROM Caches
                GROUP BY Run_ID
            ) caches ON caches.Run_ID = RUN.id
            GROUP BY RUN.id
            ORDER BY RUN.id DESC
            LIMIT ?""", [limit])

        result = DBAccess.cursor.fetchall()

        if result:
            result.reverse()
        
        return result
    
    @staticmethod
    def get_run_requests(run_id: int) -> List[Tuple]:
        """Get all requests for a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            List of tuples: (request_id, time, url)
        """
        
        DBAccess.cursor.execute("""
            SELECT id, URL, elapsed_ms, download_bytes
            FROM Requests
            WHERE run_id = ?
            ORDER BY id ASC""", [run_id])

        return DBAccess.cursor.fetchall()
    
    @staticmethod
    def get_all_traces() -> List[Tuple]:
        """Get all traces with entry counts.
        
        Returns:
            List of tuples: (trace_id, name, key_count, last_update)
        """
        DBAccess.cursor.execute("""
            SELECT T.id, T.Name, COUNT(K.id), T.Last_Update
            FROM Traces T
            JOIN Trace_Entry K ON T.id = K.Trace_ID
            GROUP BY T.id
        """)
        return DBAccess.cursor.fetchall()
    
    @staticmethod
    def get_trace_entries(trace_id: int, group_by_url: bool = False) -> List[Tuple]:
        """Get entries for a specific trace.
        
        Args:
            trace_id: The trace ID
            group_by_url: If True, group by URL and show count; else show individual entries
            
        Returns:
            List of tuples with URL data
        """
        if group_by_url:
            DBAccess.cursor.execute("""
                SELECT URL, COUNT(id) as count
                FROM Trace_Entry
                WHERE Trace_ID = ?
                GROUP BY URL
                ORDER BY COUNT(id) DESC
            """, [trace_id])
        else:
            DBAccess.cursor.execute("""
                SELECT URL
                FROM Trace_Entry
                WHERE Trace_ID = ?
            """, [trace_id])
        return DBAccess.cursor.fetchall()

    
    @staticmethod
    def get_recent_requests(count: int) -> List[Tuple]:
        """Get the most recent requests with cache data.
        
        Args:
            count: Number of recent requests to fetch
            
        Returns:
            List of tuples: (url, elapsed_ms)
        """
        DBAccess.cursor.execute("""
            SELECT id, URL, elapsed_ms, download_bytes
            FROM Requests
            ORDER BY id DESC
            LIMIT ?
        """, [count])
        rows = DBAccess.cursor.fetchall()
        rows.reverse()  # Reverse to get chronological order

        return rows

    @staticmethod
    def get_caches(run_id):
        DBAccess.cursor.execute(
            """SELECT Name, Access_Cost
            FROM Caches
            WHERE Run_ID = ?""", [run_id]
        )

        results = DBAccess.cursor.fetchall()

        return results