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
    def get_all_runs() -> List[Tuple]:
        """Get all runs with trace information.
        
        Returns:
            List of tuples: (run_id, name, start_time, end_time, trace_name)
        """
        DBAccess.cursor.execute("""
            SELECT RUN.id, RUN.Name, RUN.Start_Time, RUN.End_Time, T.Name
            FROM Runs RUN 
            JOIN Traces T ON RUN.Trace_ID = T.id
        """)
        return DBAccess.cursor.fetchall()
    
    @staticmethod
    def get_run_requests(run_id: int) -> List[Tuple]:
        """Get all requests for a specific run.
        
        Args:
            run_id: The run ID
            
        Returns:
            List of tuples: (request_id, time, url)
        """
        DBAccess.cursor.execute("""
            SELECT R.id, R.Time, R.URL
            FROM Requests R 
            JOIN CacheReq CR ON R.id = CR.req_id
            WHERE R.Run_ID = ? AND CR.accessed = 1
            GROUP BY R.id
        """, [run_id])
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
    def get_request_cache_details(req_id: int) -> List[Tuple]:
        """Get cache request details for a specific request.
        
        Args:
            req_id: The request ID
            
        Returns:
            List of tuples: (indication, accessed, resolution, name, access_cost)
        """
        # Query CacheReq rows and map cache_id -> name/access_cost using registry
        DBAccess.cursor.execute("""
            SELECT indication, accessed, resolution, cache_id
            FROM CacheReq
            WHERE req_id = ?
        """, [req_id])

        rows = DBAccess.cursor.fetchall()

        # Map cache_id to registry name and cost for each row
        from cache.registry import get_name_by_index, get_access_cost_by_index, get_miss_cost

        mapped = []
        for indication, accessed, resolution, cache_id in rows:
            # If cache_id is present, map to real cache name; otherwise treat as a miss penalty row
            if cache_id:
                name = get_name_by_index(cache_id) or "unknown"
                access_cost = get_access_cost_by_index(cache_id)
            else:
                # No cache_id indicates a miss/penalty entry in older DBs; keep explicit 'miss'
                name = "miss"
                access_cost = get_miss_cost()

            mapped.append((indication, accessed, resolution, name, access_cost))

        return mapped
    
    @staticmethod
    def get_recent_requests(count: int) -> List[Tuple]:
        """Get the most recent requests with cache data.
        
        Args:
            count: Number of recent requests to fetch
            
        Returns:
            List of tuples: (request_id, time, url)
        """
        DBAccess.cursor.execute("""
            SELECT R.id, R.Time, R.URL
            FROM Requests R 
            JOIN CacheReq CR ON R.id = CR.req_id
            WHERE CR.accessed = 1
            GROUP BY R.id
            ORDER BY R.Time DESC 
            LIMIT ?
        """, [count])
        rows = DBAccess.cursor.fetchall()
        rows.reverse()  # Reverse to get chronological order
        return rows
