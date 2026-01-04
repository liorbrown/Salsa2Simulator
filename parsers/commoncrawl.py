import requests
import json
import time
import sqlite3

# ================= CONFIGURATION =================
DB_FILE = "salsa2.db"
MAX_URLS_TO_COLLECT = 1000000
SEARCH_PATTERN = "*.net"
# =================================================

def setup_database():
    """Drops the old table and creates a fresh one."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. DROP the table to clear all data and reset the ID counter
    cursor.execute("DROP TABLE IF EXISTS URLs")
    
    # 2. CREATE the table fresh
    cursor.execute("""
        CREATE TABLE URLs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            URL TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn

def get_urls():
    # Connect and clean DB
    conn = setup_database()
    cursor = conn.cursor()
    
    index_url = "http://index.commoncrawl.org/CC-MAIN-2024-51-index"
    current_page = 0
    collected_count = 0
    
    print(f"--- Starting New Run (Table Cleared) ---")
    print(f"Target: {MAX_URLS_TO_COLLECT} URLs")
    print(f"Saving to SQLite DB: {DB_FILE}")
    
    try:
        while collected_count < MAX_URLS_TO_COLLECT:
            print(f"Fetching Page {current_page}...", end=" ", flush=True)
            
            params = {
                'url': SEARCH_PATTERN,
                'output': 'json',
                'filter': 'status:200',
                'page': current_page
            }

            try:
                response = requests.get(index_url, params=params, timeout=30)
                
                if response.status_code != 200:
                    print(f"\n[!] Server Error {response.status_code}. Retrying in 5s...")
                    time.sleep(5)
                    continue

                lines = response.text.strip().splitlines()
                if not lines:
                    print("\n[!] No more results found.")
                    break

                batch_data = [] 
                
                for line in lines:
                    if collected_count >= MAX_URLS_TO_COLLECT:
                        break
                    
                    try:
                        data = json.loads(line)
                        url = data.get('url')
                        
                        if url:
                            batch_data.append((url,))
                            collected_count += 1
                    except ValueError:
                        continue
                
                # Bulk insert
                if batch_data:
                    cursor.executemany("INSERT INTO URLs (URL) VALUES (?)", batch_data)
                    conn.commit()
                
                print(f"Inserted {len(batch_data)} URLs. (Total: {collected_count}/{MAX_URLS_TO_COLLECT})")
                
                if collected_count >= MAX_URLS_TO_COLLECT:
                    print("--- Limit Reached. Stopping. ---")
                    break

                current_page += 1
                time.sleep(0.5)

            except Exception as e:
                print(f"\n[!] Error: {e}")
                time.sleep(2)
                
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    get_urls()