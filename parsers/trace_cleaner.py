import sys
from pathlib import Path

import requests

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prettytable import PrettyTable
from ui.repository import UIRepository
from database.db_access import DBAccess

def get_trace_id():
    # Get from user trace id to show its content
    try:
        trace_id = int(input("Select trace ID to clean it: "))
        
        if trace_id <= 0:
            print("Error: Trace ID must be positive.")
            return None
    except ValueError:
        print("Error: Please enter a valid number for trace ID.")
        return None
    
    return trace_id

def print_traces():
    rows = UIRepository.get_all_traces()
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = ['ID', 'Name', 'Keys', 'Last Update']

    for row in rows:
        table.add_row(row)

    print(table)

def get_urls(trace_id):
    DBAccess.cursor.execute("""
        SELECT DISTINCT URL 
        FROM Trace_Entry
        WHERE Trace_ID = ?""", [trace_id])
    
    URLs = DBAccess.cursor.fetchall()

    return(URLs)

def delete_url(URL):
    DBAccess.cursor.execute("""
        DELETE FROM Trace_Entry
        WHERE URL = ?""", [URL])

def clean_trace(URLs):
    ca_bundle = '/etc/ssl/certs/ca-certificates.crt'
    count = 0
    
    for URL, in URLs:
        try:
            response = requests.get(URL, timeout=5, 
                              verify=ca_bundle, allow_redirects=False)

            if response.status_code < 300:
                continue
                
        except Exception as e:
            print(f"{URL} error: {e}")
        

        print(f"Deleting {URL}")
        delete_url(URL)
        count += 1
    
    DBAccess.conn.commit()

    return count


######### Main ########
# Initialize database connection
DBAccess.open()

print_traces()

trace_id = get_trace_id()

URLs = get_urls(trace_id)

count = clean_trace(URLs)

print (f"{count} URLs cleaned successfuly")

DBAccess.close()