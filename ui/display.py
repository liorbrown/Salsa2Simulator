"""Display and UI functions for Salsa2 Simulator."""
from typing import Dict, List, Iterable, Tuple
from prettytable import PrettyTable

from database.db_access import DBAccess
from cache.cache_manager import get_cost, get_miss_cost


def show_run(run_id: int):
    """Display details of a specific run."""
    if run_id:
        # Fetch rows from the "Requests" table
        DBAccess.cursor.execute("""SELECT R.id, R.Time, R.URL
                          FROM Requests R JOIN CacheReq CR
                          ON R.id = CR.req_id
                          WHERE R.Run_ID = ? AND CR.accessed = 1
                          GROUP BY R.id""", [run_id])
        rows = DBAccess.cursor.fetchall()

        show_requests_details(rows)


def show_runs():
    """Fetches and displays all entries in the 'Runs' table."""
    # Fetch all rows from the "Runs" table
    DBAccess.cursor.execute("""SELECT RUN.id ID, RUN.Name, RUN.Start_Time start, RUN.End_Time end,
                             T.Name trace_name, 0 requests, 
                             0 total_cost, 0 average_cost
                      FROM Runs RUN JOIN Traces T   
                      ON RUN.Trace_ID = T.id""")
    runs = DBAccess.cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    # Runs on run
    for run in runs:
        cost, reqNum = get_cost(run[0])
        if reqNum:
            avg_cost = round(cost / reqNum, 3)

            row = [run[0], run[1], run[2], run[3], run[4], cost, reqNum, avg_cost]
            
            table.add_row(row)
    
    print(table)

    try:
        run_id = int(input("""Choose run ID to see his requests, or 0 to go back to main menu: """))
        if run_id < 0:
            print("Error: Run ID cannot be negative.")
            return
    except ValueError:
        print("Error: Please enter a valid number for run ID.")
        return

    show_run(run_id)


def show_keys(trace_id):    
    """
    Fetches and displays URLs associated with a specific Trace ID from the 'Keys' table.
    
    Args:
        trace_id: The ID of the trace to fetch URLs for
    """
    group_by = input("Group by URLs? (y/n)")
    if group_by.upper() == 'Y':
        # Fetch all URLs from keys table, that belong to trace_id 
        DBAccess.cursor.execute("""SELECT URL, COUNT(id) count
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?
                        GROUP BY URL
                        ORDER BY COUNT(id) DESC""", [trace_id])
    else:
        # Fetch all URLs from keys table, that belong to trace_id 
        DBAccess.cursor.execute("""SELECT URL
                        FROM Trace_Entry 
                        WHERE Trace_ID = ?""", [trace_id])
    rows = DBAccess.cursor.fetchall()
    column_names = [description[0] for description in DBAccess.cursor.description]

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)


def show_traces():
    """
    Fetches and displays trace details, including the number of keys and last update time.
    Allows the user to view details of a specific trace.
    """
    # Fetch all rows from the "Traces" table
    DBAccess.cursor.execute("""SELECT T.id ID, T.Name Name, 
                             COUNT(K.id) Keys, T.Last_Update Last_Update 
                      FROM Traces T, Trace_Entry K
                      WHERE T.id = K.Trace_ID
                      GROUP BY T.id""")
    rows = DBAccess.cursor.fetchall()
    
    # Fetch column names for the table
    column_names = [description[0] for description in DBAccess.cursor.description]
    
    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers
    
    for row in rows:
        table.add_row(row)
    
    print(table)

    # Get from user trace id to show its content
    try:
        trace_id = int(input("""Select trace ID to show its content, or 0 to go back to main menu: """))
        if trace_id < 0:
            print("Error: Trace ID cannot be negative.")
            return
    except ValueError:
        print("Error: Please enter a valid number for trace ID.")
        return

    if trace_id:
        show_keys(trace_id)


def create_caches_dict() -> dict[str, list[int]]:
    """Create a dictionary mapping cache names to classification metrics.
    
    Note: 'miss' cache is excluded as it's not a real cache, just a penalty indicator.
    """
    result: dict[str, list[int]] = {}

    # Exclude 'miss' cache - it's only for penalty tracking, not a real cache peer
    DBAccess.cursor.execute("SELECT Name FROM Caches WHERE Name != 'miss'")
    caches = DBAccess.cursor.fetchall()

    for (name,) in caches:
        result[name] = [0] * 4

    result['Sum'] = [0] * 4

    return result


def classification_metrics(data: dict) -> list:
    """
    Calculate classification metrics.
    
    Input:  {name: [TN, FN, FP, TP]}
    Output: [[name, accuracy, recall, precision, f1], ...]
    Metrics are rounded to 3 decimals. Division by zero returns 0.0.
    """
    results = []
    for name, (TN, FP, FN, TP) in data.items():
        # total number of samples
        total = TN + FN + FP + TP

        # Accuracy = (TP + TN) / total
        accuracy  = (TP + TN) / total if total > 0 else 0.0

        # Recall = TP / (TP + FN)
        recall    = TP / (TP + FN) if (TP + FN) > 0 else 0.0

        # Precision = TP / (TP + FP)
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0

        # F1 = harmonic mean of precision and recall
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)

        # append row: [name, accuracy, recall, precision, f1]
        results.append([
            name,
            round(accuracy, 3),
            round(recall, 3),
            round(precision, 3),
            round(f1, 3)
        ])

    return results


def print_accuracy(cachesDict: Dict[str, List[int]]) -> None:
    """Print accuracy metrics table."""
    column_names = ['Name', 'Accuracy', 'Recall', 'Precision', 'F1 Score']

    # Display the data in a table format using PrettyTable
    table = PrettyTable()
    table.field_names = column_names  # Set column headers

    table.add_rows(classification_metrics(cachesDict))

    print(table)


def show_requests_details(requests: Iterable[Tuple]) -> PrettyTable:
    """Display detailed information about requests."""
    # Columns
    table = PrettyTable()
    table.field_names = ['Time', 'URL', 'Indications', 'Accessed', 'Resolution', 'Hit?', 'Cost']

    cachesDict: Dict[str, List[int]] = create_caches_dict()

    for req in requests:
        req_id, req_time, req_url = req[0], req[1], req[2]

        DBAccess.cursor.execute(
            """
            SELECT indication, accessed, resolution, Name, Access_Cost
            FROM CacheReq R
            JOIN Caches C ON R.cache_id = C.id
            WHERE R.req_id = ?
            """,
            [req_id]
        )
        rows = DBAccess.cursor.fetchall()

        indicated_names: List[str] = []
        accessed_names:  List[str] = []
        resolved_names:  List[str] = []

        hit = False
        cost = 0

        for (indication, accessed, resolution, name, access_cost) in rows:
            # Skip 'miss' cache - it's not a real cache peer, just a penalty indicator
            if name == 'miss':
                continue
                
            # resType = 0..3 if indication, resolution are 0/1
            # Accuracy metrics check digest accuracy: did our indication match the actual resolution?
            # resType 0: indication=0, resolution=0 → True Negative (correctly didn't predict)
            # resType 1: indication=1, resolution=0 → False Positive (incorrectly predicted)
            # resType 2: indication=0, resolution=1 → False Negative (missed correct prediction)
            # resType 3: indication=1, resolution=1 → True Positive (correctly predicted)
            resType = int(indication) + 2 * int(resolution)
            if not (0 <= resType < 4):
                raise ValueError(f"Unexpected resType {resType} for ({indication=}, {resolution=})")

            if name not in cachesDict:
                raise KeyError(f"Cache name {name!r} not in cachesDict")

            cachesDict[name][resType] += 1
            cachesDict['Sum'][resType] += 1

            if indication:
                indicated_names.append(name)
            if accessed:
                accessed_names.append(name)
                cost += access_cost or 0  # handle NULL
            if resolution:
                resolved_names.append(name)

            # true "hit" only if accessed AND resolved
            hit = hit or accessed & resolution

        if not hit:
            cost += get_miss_cost()

        def fmt(names: List[str]) -> str:
            return f"[{','.join(names)}]"

        table.add_row([req_time, req_url, fmt(indicated_names), fmt(accessed_names),
                       fmt(resolved_names), hit, cost])

    print(table)
    print_accuracy(cachesDict)


def show_requests():
    """
    Fetches and displays a specified number of the most recent requests,
    including cache details.
    """
    try:
        count = int(input("How many requests you want to show?: "))
        if count <= 0:
            print("Error: Please enter a positive number.")
            return
    except ValueError:
        print("Error: Please enter a valid number.")
        return
     
    # Fetch rows from the "Requests" table, limiting last {count}
    DBAccess.cursor.execute("""SELECT R.id, R.Time, R.URL
                               FROM Requests R JOIN CacheReq CR
                               ON R.id = CR.req_id
                               WHERE CR.accessed = 1
                               GROUP BY R.id
                               ORDER BY R.Time DESC LIMIT ?""", [count])
    req_ids = DBAccess.cursor.fetchall()
    req_ids.reverse()

    show_requests_details(req_ids)
