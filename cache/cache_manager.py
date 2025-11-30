"""Cache management logic for Salsa2 Simulator."""
import os
import re
import requests

DEBUG_MODE = False

def log_msg(msg : str) -> None:
    if DEBUG_MODE:
        print(msg)

from config.config import MyConfig
from database.db_access import DBAccess
from cache.registry import (
    load_caches as load_caches_to_registry, 
    set_miss_cost, 
    get_miss_cost,
    set_salsa2_v)

def clear_cache(remote_ip):
    """
    Clear all cache data from the given remote cache IP.
    
    Args:
        remote_ip: IP address of the remote cache server
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Import paramiko lazily so the module is not required for code paths
    # that don't use SSH functionality. If paramiko is missing, return
    # False and explain the dependency to the caller.
    try:
        import paramiko
    except ImportError:
        log_msg("paramiko is not installed; `clear_cache` requires paramiko to run.")
        return False

    # Create an SSH client instance
    ssh_client = paramiko.SSHClient()

    # Automatically add the host key if not already known
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Get password to others caches users
    password = os.getenv('SQUID_PASS')

    try:
        # Connect to the remote machine
        config = MyConfig()
        ssh_client.connect(remote_ip, username=config.get_key('user'), password=password)

        # Command to delete the Squid cache directory
        command = f"sudo find {config.get_key('cache_dir')} -type f ! -name 'swap.state' -delete"

        # Execute the command to delete the directory
        stdin, stdout, stderr = ssh_client.exec_command(command, get_pty=True)

        # Provide sudo password for the command (if needed)
        if password:
            stdin.write(password + '\n')
            stdin.flush()

        # Wait for the command to complete
        exit_status = stdout.channel.recv_exit_status()

        # If exit_status is 0, operation succeeded
        if not exit_status:
            return True
        else:
            log_msg(f"Error deleting {remote_ip} cache: {stderr.read().decode()}")
            return False

    except Exception as e:
        log_msg(f"Error: {e}")
        return False
    finally:
        # Close the SSH connection
        try:
            ssh_client.close()
        except Exception:
            pass

def is_squid_up():
    """
    Check if squid is up on all servers by checking request to google site from each.
    
    Returns:
        bool: True if all squids are up, False otherwise
    """
    from http_requests.request_executor import get_proxies_for_cache  # Import here to avoid circular dependency
    from cache.registry import get_all_caches

    caches_data = get_all_caches()
    caches = [(info['ip'],) for name, info in caches_data.items()]

    URL = "http://www.google.com"
    config = MyConfig()
    ca_bundle = config.get_key('ca_bundle')
    

    try:
        # Use the standard mapping: HTTP -> local proxy, HTTPS -> Fiddler
        proxy = get_proxies_for_cache()
        response = requests.get(URL, proxies=proxy, timeout=10, verify=ca_bundle)

        # Check if proxy OK
        if response.ok:
            # Runs on all parents to check if they also OK
            for cache in caches:
                # For parent checks we use the parent's HTTP address for http
                # and still route HTTPS to the Fiddler proxy.
                proxy = get_proxies_for_cache(http_host=cache[0])
                try:
                    response = requests.get(URL, proxies=proxy, timeout=10, verify=ca_bundle)

                    if response.ok:
                        return True
                except Exception as e:
                    log_msg(f"Server {cache[0]} error: {e}")
            return True
        else:
            log_msg(f"proxy request failed")
            return False
    except Exception as e:
        log_msg(f"proxy request failed: {e}")
        return False


def get_cost(run_id: int):
    """
    Calculate the total cost and request count for a run.
    
    Args:
        run_id: The ID of the run
        
    Returns:
        list: [total_cost, request_count]
    """
    # Select all requests that accessed
    DBAccess.cursor.execute("""SELECT DISTINCT R.id
                      FROM Requests R JOIN CacheReq CR
                      ON R.id = CR.req_id
                      WHERE R.run_id = ? AND CR.accessed = 1""", [run_id])
    
    requests = DBAccess.cursor.fetchall()
    req_count = len(requests)
    total_cost = 0

    for request, in requests:
        # Select sum of cost and resolution of all accessed caches
        DBAccess.cursor.execute(
            """SELECT SUM(CR.resolution), SUM(C.Access_Cost)
            FROM CacheReq CR JOIN Caches C
            ON CR.cache_name = C.Name
            WHERE CR.req_id = ? AND CR.accessed = 1 AND C.run_id=?""", [request, run_id])
        
        resolutions, cost = DBAccess.cursor.fetchone()

        if resolutions is None:
            return None, None
            
        # Total cost is costs sum + miss cost if no resolution found for accessed caches
        total_cost += cost + (1 - min(1, resolutions)) * get_miss_cost()
        
    return [total_cost, req_count]


def show_caches():
    """
    Displays all cache peer details from the volatile registry.
    """
    from cache.registry import get_all_caches
    
    caches_data = get_all_caches()
    
    # Build rows for all real caches
    rows = []
    for cache_name, cache_info in caches_data.items():
        rows.append((cache_name, cache_info['ip'], cache_info['access_cost']))
    
    column_names = ['Name', 'IP', 'Access_Cost']
      
    from prettytable import PrettyTable 

    table = PrettyTable()
    table.field_names = column_names  # Set column headers

    for row in rows:
        table.add_row(row)

    print(table)

# NOTE: Interactive/CLI helpers (`new_cache`, `update_cache`, `delete_cache`,
# `manage_caches`) removed from this module. If you need interactive cache
# management, consider implementing a small `cache/cli.py` module that
# imports `DBAccess` and provides these utilities separately.


def fill_caches():
    """
    Loads cache configurations from Squid configuration file into the volatile registry.
    Called at program startup to populate the in-memory cache registry.
    """
    config = MyConfig()
    try:
        caches_data = []

        with open(config.get_key('conf_file'), 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith("miss_penalty"):
                    parts = line.split()
                    if len(parts) < 2:
                        continue  # Skip malformed lines
                    # Store miss penalty separately, do not create a fake 'miss' cache entry
                    try:
                        set_miss_cost(int(parts[1]))
                    except Exception:
                        # ignore invalid value and keep default
                        pass
                
                elif line.startswith("salsa2"):
                    parts = line.split()
                    if len(parts) < 2:
                        continue  # Skip malformed lines
                    # Store miss penalty separately, do not create a fake 'miss' cache entry
                    try:
                        set_salsa2_v(int(parts[1]))
                    except Exception:
                        # ignore invalid value and keep default
                        pass

                elif line.startswith("cache_peer "):
                    parts = line.split()
                    if len(parts) < 2:
                        continue  # Skip malformed lines

                    ip = parts[1]
                    name = None
                    access_cost : int = None

                    # Use regex to find name= and access-cost= as they might not be in fixed positions
                    name_match = re.search(r'name=(\S+)', line)
                    if name_match:
                        name = name_match.group(1)

                    access_cost_match = re.search(r'access-cost=(\S+)', line)
                    if access_cost_match:
                        try:
                            access_cost = float(access_cost_match.group(1))
                        except ValueError:
                            log_msg(f"Warning: Could not parse access-cost for line: {line}")
                            access_cost = 1  # Default to 1 if parsing fails
                    else:
                        # Default to 1 if access-cost is missing from squid.conf
                        access_cost = 1
                        log_msg(f"Info: No access-cost specified in line, using default value of 1: {line}")

                    if ip and name and access_cost is not None:
                        caches_data.append((name, ip, access_cost))
                    else:
                        log_msg(f"Warning: Missing IP or Name in line: {line}")

        # Load all parsed data into the volatile registry
        load_caches_to_registry(caches_data)
        log_msg(f"Successfully loaded {len(caches_data)} caches from {config.get_key('conf_file')}")

    except FileNotFoundError:
        log_msg(f"Error: Configuration file not found at {config.get_key('conf_file')}")
    except Exception as e:
        log_msg(f"An unexpected error occurred: {e}")
