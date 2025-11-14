"""Request execution logic for Salsa2 Simulator."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from config.config import MyConfig, get_ca_bundle
from database.db_access import DBAccess


def get_proxies_for_cache(http_host: str | None = None) -> dict:
    """Return proxies mapping used throughout the app.

    If http_host is provided it will be used for the "http" entry (useful
    when checking individual cache parents); otherwise the value from
    MyConfig or DEFAULT_HTTP_PROXY is used.
    
    Args:
        http_host: Optional HTTP host to use for HTTP proxy
        
    Returns:
        dict: Proxies mapping with 'http' and 'https' keys
    """
    http_proxy = (f'http://{http_host}:{MyConfig.squid_port}' if http_host
                  else (MyConfig.http_proxy if getattr(MyConfig, 'http_proxy', None) 
                        else 'http://127.0.0.1:3128'))

    https_proxy = (MyConfig.https_proxy if getattr(MyConfig, 'https_proxy', None) 
                   else 'http://192.168.10.1:8888')

    return {
        'http': http_proxy,
        'https': https_proxy,
    }


def execute_req(url: str, run_id: int):
    """
    Execute request to squid proxy.
    
    Args:
        url: The URL for the request
        run_id: The ID of the run associated with the request
    
    Returns:
        int: The request ID if successful, None otherwise
    """
    # Build proxies mapping from configuration (or sensible defaults)
    PROXIES = get_proxies_for_cache()

    try:
        jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

        # Insert request's data into requests table
        DBAccess.cursor.execute("""INSERT INTO Requests('Time', 'URL', 'Run_ID') 
                        VALUES (?,?,?)""", [jerusalem_time, url, run_id])
        
        # Need to close connection before continuing because squid needs to update DB
        DBAccess.conn.commit()
        DBAccess.close()

        # Execute requests through the configured proxies.
        # For HTTPS we enable verification using the configured CA bundle so Fiddler's root is trusted.
        # NOTE: requests will ignore the `verify` argument for plain HTTP URLs.
        # Disable automatic redirect following to maintain full control over what gets sent
        # and prevent duplicate requests in Squid logs
        response = requests.get(url, proxies=PROXIES, timeout=10, 
                              verify=get_ca_bundle(), allow_redirects=False)

        # Reopen DB 
        DBAccess.open()       

        # Check if request failed (treat 3xx redirects as successful responses)
        if response.status_code >= 400:
            print(f"Request {url} error - {response.status_code}")

            # Delete URL from traces entries and from Keys list (commented out)
            # DBAccess.cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
            # DBAccess.cursor.execute("DELETE FROM Keys WHERE URL=?",[url])

            DBAccess.conn.commit()
            
            return None
        else:    
            DBAccess.cursor.execute("SELECT MAX(id) FROM Requests")
            reqID = DBAccess.cursor.fetchone()[0]

            # Return reqID
            return reqID
        
    except Exception as e:
        print(f"Request {url} error - {e}")

        DBAccess.open()
        
        # Delete URL from traces entries and from Keys list (commented out)
        # DBAccess.cursor.execute("DELETE FROM Trace_Entry WHERE URL=?",[url])
        # DBAccess.cursor.execute("DELETE FROM Keys WHERE URL=?",[url])
        
        return None


def execute_single_req():
    """
    Executes a single request for a given URL and logs it into the 'Requests' table.
    Prompts the user for a URL and displays the result.
    """
    from cache.cache_manager import get_miss_cost  # Import here to avoid circular dependency

    url = input("Enter URL: ").strip()
    
    # Validate URL format
    if not url:
        print("Error: URL cannot be empty.")
        return
    
    if not (url.startswith('http://') or url.startswith('https://')):
        print("Error: URL must start with 'http://' or 'https://'")
        return

    try:
        # Execute request without run id
        reqID = execute_req(url, 0)

        if reqID:
            DBAccess.cursor.execute("""SELECT Caches.Name, Caches.Access_Cost, CacheReq.resolution
                              FROM CacheReq, Caches
                              WHERE CacheReq.cache_id = Caches.id AND
                                    CacheReq.req_id = ? AND
                                    CacheReq.accessed = 1""", [reqID])
            
            result = DBAccess.cursor.fetchone()

            if result:
                if result[2]:
                    name = result[0]
                    cost = result[1]
                else:
                    name = "miss"
                    cost = get_miss_cost()

                print(f"""Request fetched successfully from {name} at cost of {cost}""")

    except sqlite3.DatabaseError as e:
        # If request fails, print the exact error message from SQLite
        print(f"Request failed: {e}")
