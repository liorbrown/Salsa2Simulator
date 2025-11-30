#!/usr/bin/env python3
"""
Salsa2 Simulator - Main Entry Point

A simulator for testing and analyzing cache performance with Squid proxy servers.
This refactored version organizes code into clear modules for maintainability.
"""

import sqlite3
import urllib3
import warnings
from datetime import datetime

from database.db_access import DBAccess
from cache.cache_manager import fill_caches, show_caches
from ui.display import show_all_runs, show_runs, show_traces, show_requests
from http_requests.request_executor import execute_single_req
from simulation.simulator import run_trace


def adapt_datetime(dt):
    """Adapter for datetime objects to store them as strings in SQLite."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main entry point for the Salsa2 Simulator."""
    try:
        # Register the adapter for datetime
        sqlite3.register_adapter(datetime, adapt_datetime)

        # Open database connection
        DBAccess.open()
        
        # Populate caches table from configuration
        fill_caches()
        
        # Suppress SSL warnings
        warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

        print("################# Welcome to Salsa2 simulator ####################")

        opp_code = 1
        while opp_code:
            try:
                user_input = input("""Choose your destiny:
    1: Show previous runs
    2: Show Traces
    3: Show last requests
    4: Execute single request
    5: Run entire trace
    6: Show caches
    0: Exit
    """)
                # Take last character to handle multi-digit inputs gracefully
                opp_code = int(user_input[-1]) if user_input else -1
            except (ValueError, IndexError):
                print("Invalid input. Please enter a number between 0-6.")
                continue
            
            if opp_code == 1:
                show_all_runs()
            elif opp_code == 2:
                show_traces()
            elif opp_code == 3:
                show_requests()
            elif opp_code == 4:
                execute_single_req()
            elif opp_code == 5:
                run_trace()
            elif opp_code == 6:
                show_caches()
            elif opp_code:
                print("Invalid option, please choose a valid number.")

        print("ByeBye")
        
    finally:
        # Always close database connection
        DBAccess.close()


if __name__ == "__main__":
    main()
