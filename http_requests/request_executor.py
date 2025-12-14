"""Request execution logic for Salsa2 Simulator."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from config.config import MyConfig
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
    config = MyConfig()
    squid_port = config.get_key('squid_port')
    http_proxy_config = config.get_key('http_proxy')
    https_proxy_config = config.get_key('https_proxy')
    
    http_proxy = (f'http://{http_host}:{squid_port}' if http_host
                  else (http_proxy_config if http_proxy_config
                        else 'http://127.0.0.1:3128'))

    https_proxy = (https_proxy_config if https_proxy_config
                   else 'http://192.168.10.1:8888')

    return {
        'http': http_proxy,
        'https': https_proxy,
    }

def is_hit(response):
    cache_status = response.headers.get('Cache-Status')
    print(cache_status)
    return cache_status and 'hit' in cache_status


def calculate_download_bytes(response) -> int:
    """Calculate the download size for a request for comparison purposes.
    
    This function determines the data size associated with a request based on
    whether it was served from cache or fetched from the origin server. The
    measurement is consistent across all requests, making it suitable for
    comparing different caching algorithms.
    
    Args:
        response: The requests.Response object (downloaded normally, not streamed)
    
    Returns:
        int: Download size in bytes:
            - 0 if cache hit (no internet access, served from local cache)
            - headers + body size if cache miss (full download from origin)
    
    How it works:
        Cache HIT:
            - Detected via 'Cache-Status' header containing 'hit'
            - Content served directly from cache
            - No internet traffic, no bytes downloaded
            - Returns: 0
        
        Cache MISS:
            - Content fetched from origin server over internet
            - Downloads both HTTP headers and response body
            - Headers size: approximate based on header key-value pairs
            - Body size: decompressed content length
            - Returns: total of headers + body size
    
    Note:
        Uses decompressed content size (not compressed wire format) for consistency.
        This provides a stable metric for comparing cache algorithm performance,
        though it may not reflect exact network bandwidth usage.
    """
    
    
    # Cache miss: calculate full download size (headers + body)
    # Use response.content for body size (decompressed, but consistent)
    body_size = len(response.content)
    
    # Approximate header size: sum of all header keys and values
    # +4 per header for ": " and "\r\n", +50 for status line
    header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 50
    
    # Check if this was a cache hit
    hit = is_hit(response)

    return (header_size + body_size) * int(not hit)


def execute_req(url: str, run_id: int):
    """
    Execute request to squid proxy.
    
    Args:
        url: The URL for the request
        run_id: The ID of the run associated with the request
    
    Returns:
        bool: Indication for request success
    """
    # Build proxies mapping from configuration (or sensible defaults)
    PROXIES = get_proxies_for_cache()

    try:
        config = MyConfig()
        ca_bundle = config.get_key('ca_bundle')
        
        # Execute requests through the configured proxies.
        # For HTTPS we enable verification using the configured CA bundle so Fiddler's root is trusted.
        # NOTE: requests will ignore the `verify` argument for plain HTTP URLs.
        # Disable automatic redirect following to maintain full control over what gets sent
        # and prevent duplicate requests in Squid logs
        response = requests.get(url, proxies=PROXIES, timeout=10, 
                              verify=ca_bundle, allow_redirects=False)
      
        # Check if request success
        if response.status_code < 300:
            download_bytes = calculate_download_bytes(response)
            elapsed_time_ms = int(response.elapsed.total_seconds() * 1000)
            jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

            # Insert request's data into requests table
            DBAccess.cursor.execute(
                """INSERT INTO Requests(
                    'Time', 
                    'URL', 
                    'Run_ID', 
                    'elapsed_ms', 
                    'download_bytes')
                    VALUES (?,?,?,?,?)""", [
                        jerusalem_time, 
                        url, 
                        run_id, 
                        elapsed_time_ms, 
                        download_bytes])
            
            # Need to close connection before continuing because squid needs to update DB
            DBAccess.conn.commit()

            return True
            
        else:    
            print(f"Request {url} error - {response.status_code}")
            
            return False
        
    except Exception as e:
        print(f"Request {url} error - {e}")             
        
        return False


def execute_single_req():
    """
    Executes a single request for a given URL and logs it into the 'Requests' table.
    Prompts the user for a URL and displays the result.
    """

    url = input("Enter URL: ").strip()
    
    # Validate URL format
    if not url:
        print("Error: URL cannot be empty.")
        return
    
    if not (url.startswith('http://') or url.startswith('https://')):
        print("Error: URL must start with 'http://' or 'https://'")
        return

    if execute_req(url, 0):
        print("Request Successfuly")
