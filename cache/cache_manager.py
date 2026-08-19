"""Cache management logic for Salsa2 Simulator."""
import re
import time
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
    set_salsa2_v)

def _ssh_connect(remote_ip):
    """
    Open an SSH connection to a remote cache node.

    Authenticates via SSH key (~/.ssh/id_ed25519, or another key/agent
    discovered by paramiko's default lookup) - no password is transmitted
    or stored. Raises on failure; callers are responsible for closing the
    returned client.

    Args:
        remote_ip: IP address of the remote cache server

    Returns:
        paramiko.SSHClient: A connected SSH client
    """
    import paramiko

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    config = MyConfig()
    ssh_client.connect(remote_ip, username=config.get_key('user'))

    return ssh_client


def clear_cache(remote_ip):
    """
    Clear all cache data from the given remote cache IP.

    Relies on a scoped NOPASSWD sudoers rule on the remote host for the
    cache-clearing command.

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

    try:
        ssh_client = _ssh_connect(remote_ip)
    except Exception as e:
        log_msg(f"Error connecting to {remote_ip}: {e}")
        return False

    try:
        # Command to delete the Squid cache directory (covered by a NOPASSWD
        # sudoers rule on the remote host, so no password prompt occurs)
        config = MyConfig()
        command = f"sudo find {config.get_key('cache_dir')} -type f ! -name 'swap.state' -delete"

        # Execute the command to delete the directory
        stdin, stdout, stderr = ssh_client.exec_command(command)

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


def restart_squid(remote_ip):
    """
    Restart the squid service on the given remote cache IP, via systemd.

    A full restart (not a reconfigure/reload) so that squid's in-memory
    cache is dropped as well as its on-disk data. Relies on a scoped
    NOPASSWD sudoers rule on the remote host for the restart command.

    Args:
        remote_ip: IP address of the remote cache server

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import paramiko
    except ImportError:
        log_msg("paramiko is not installed; `restart_squid` requires paramiko to run.")
        return False

    try:
        ssh_client = _ssh_connect(remote_ip)
    except Exception as e:
        log_msg(f"Error connecting to {remote_ip}: {e}")
        return False

    try:
        stdin, stdout, stderr = ssh_client.exec_command("sudo systemctl restart squid")
        exit_status = stdout.channel.recv_exit_status()

        if not exit_status:
            return True
        else:
            log_msg(f"Error restarting squid on {remote_ip}: {stderr.read().decode()}")
            return False

    except Exception as e:
        log_msg(f"Error: {e}")
        return False
    finally:
        try:
            ssh_client.close()
        except Exception:
            pass

def reset_all_caches():
    """
    Clear cache data and restart squid on every configured parent cache.

    Processes caches one at a time - clear, then restart, then verify the
    cache is reachable again - and stops at the first failure rather than
    continuing on to the next cache, to avoid leaving the hierarchy in a
    mixed state (e.g. one parent wiped, one untouched) when something is
    already going wrong.

    Returns:
        list of (name, ip, status) tuples, one entry per cache attempted.
        status is one of: 'ok', 'clear failed', 'restart failed',
        'unreachable after restart'.
    """
    from http_requests.request_executor import get_proxies_for_cache
    from cache.registry import get_all_caches

    caches = list(get_all_caches().items())
    total = len(caches)
    results = []

    for done, (name, info) in enumerate(caches, start=1):
        ip = info['ip']
        progress = f"[{done}/{total}]"

        print(f"{progress} Clearing cache on {name} ({ip})...")
        if not clear_cache(ip):
            print(f"{progress} FAILED to clear cache on {name} ({ip})")
            results.append((name, ip, 'clear failed'))
            break

        print(f"{progress} Restarting squid on {name} ({ip})...")
        if not restart_squid(ip):
            print(f"{progress} FAILED to restart squid on {name} ({ip})")
            results.append((name, ip, 'restart failed'))
            break

        print(f"{progress} Verifying {name} ({ip}) is reachable...")
        proxy = get_proxies_for_cache(http_host=ip)
        last_error = None
        verified = False
        # Squid takes a moment to accept connections again right after a
        # restart, so retry briefly instead of failing on the first attempt.
        for attempt in range(5):
            if attempt:
                time.sleep(2)
            try:
                response = requests.get(
                    "http://www.google.com",
                    headers={'X-Originally-HTTPS': '1'},
                    proxies=proxy,
                    timeout=10,
                )
                if response.ok:
                    verified = True
                    break
                last_error = f"HTTP {response.status_code}"
            except Exception as e:
                last_error = e

        if not verified:
            print(f"{progress} FAILED to verify {name} ({ip}): {last_error}")
            results.append((name, ip, 'unreachable after restart'))
            break

        print(f"{progress} {name} ({ip}) reset OK")
        results.append((name, ip, 'ok'))

    return results


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
    headers = {'X-Originally-HTTPS': '1'}

    try:
        proxy = get_proxies_for_cache()
        response = requests.get(URL, headers=headers, proxies=proxy, timeout=10)

        # Check if proxy OK
        if response.ok:
            # Runs on all parents to check if they also OK
            for cache in caches:
                # For parent checks we use the parent's HTTP address
                proxy = get_proxies_for_cache(http_host=cache[0])
                try:
                    response = requests.get(URL, headers=headers, proxies=proxy, timeout=10)

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
