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
        dict: Proxies mapping with 'http' key
    """
    config = MyConfig()
    squid_port = config.get_key('squid_port')
    http_proxy_config = config.get_key('http_proxy')
    
    http_proxy = (f'http://{http_host}:{squid_port}' if http_host
                  else (http_proxy_config if http_proxy_config
                        else 'http://127.0.0.1:3128'))

    return {
        'http': http_proxy,
    }

def is_hit(response):
    cache_status = response.headers.get('Cache-Status')
    print(cache_status)
    return cache_status and 'hit' in cache_status


def calculate_response_size(response) -> int:
    """Calculate the total size of a response (headers + body), in bytes.

    Args:
        response: The requests.Response object (downloaded normally, not streamed)

    Returns:
        int: Approximate total size in bytes of the headers and body combined.

    Note:
        Uses decompressed content size (not compressed wire format) for consistency.
        Header size is approximate: sum of header key/value lengths, +4 per header
        for ": " and "\\r\\n", +50 for the status line.
    """
    # Use response.content for body size (decompressed, but consistent)
    body_size = len(response.content)

    # Approximate header size: sum of all header keys and values
    # +4 per header for ": " and "\r\n", +50 for status line
    header_size = sum(len(k) + len(v) + 4 for k, v in response.headers.items()) + 50

    return header_size + body_size


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
    """
    return calculate_response_size(response) * int(not is_hit(response))


def send_proxied_request(url: str, timeout: int = 10):
    """Send a GET request for the given URL through the configured Squid proxy.

    Converts HTTPS URLs to HTTP and marks them with the 'X-Originally-HTTPS'
    header, so all requests go through Squid as plain HTTP - avoiding CONNECT
    tunnels and enabling connection reuse.

    Args:
        url: The URL for the request (can be HTTP or HTTPS)
        timeout: Request timeout in seconds

    Returns:
        requests.Response: The response from the proxy
    """
    is_https = url.startswith('https://')
    proxied_url = url.replace('https://', 'http://', 1) if is_https else url

    headers = {}
    if is_https:
        headers['X-Originally-HTTPS'] = '1'

    # Disable automatic redirect following to maintain full control over what gets sent
    # and prevent duplicate requests in Squid logs
    PROXIES = get_proxies_for_cache()
    return requests.get(proxied_url, headers=headers, proxies=PROXIES, timeout=timeout, allow_redirects=False)


def execute_req(url: str, run_id: int):
    """
    Execute request to squid proxy.

    Args:
        url: The URL for the request (can be HTTP or HTTPS)
        run_id: The ID of the run associated with the request

    Returns:
        bool: Indication for request success
    """
    try:
        # Store the original URL (with https if it was HTTPS) for logging
        original_url = url
        response = send_proxied_request(url)

        # Check if request success
        if response.status_code < 300:
            download_bytes = calculate_download_bytes(response)
            elapsed_time_ms = int(response.elapsed.total_seconds() * 1000)
            jerusalem_time = datetime.now(ZoneInfo("Asia/Jerusalem"))

            # Insert request's data into requests table
            # Store the original URL (with https if it was HTTPS)
            DBAccess.cursor.execute(
                """INSERT INTO Requests(
                    'Time', 
                    'URL', 
                    'Run_ID', 
                    'elapsed_ms', 
                    'download_bytes')
                    VALUES (?,?,?,?,?)""", [
                        jerusalem_time, 
                        original_url, 
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
