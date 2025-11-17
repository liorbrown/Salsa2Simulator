#!/usr/bin/env python3
"""Shodan search parser for discovering hosts and services."""

import shodan
import sys
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Get API key from environment variable - NEVER hardcode secrets!
API_KEY = os.getenv('SHODAN_API_KEY')
if not API_KEY:
    raise ValueError("SHODAN_API_KEY environment variable not set. Please configure it before running.")

shodan_client = shodan.Shodan(API_KEY)
shodan_client._session.verify = False  # Disable SSL verification


def search_shodan(query: str, limit: int = 50) -> list:
    """
    Search Shodan for hosts matching the query.
    
    Args:
        query: Shodan search query
        limit: Maximum number of results to return
        
    Returns:
        List of matching hosts
    """
    try:
        results = shodan_client.search(query)
        hosts = []
        
        for i, site in enumerate(results.get('matches', [])):
            if i >= limit:
                break
            hosts.append(site.get('ip_str'))
        
        return hosts
    except Exception as e:
        print(f"Error searching Shodan: {e}", file=sys.stderr)
        return []


if __name__ == '__main__':
    # Example: Search for HTTP-only websites
    results = search_shodan('port:80 -ssl', limit=50)
    for host in results:
        print(host)
