# HIT/MISS comparator

## General
This file will describe the functionality of current script
, This script code will use all the existing code it can from the existed simulator code

## Goal
The goal of this script is to estimate  how much the cache improves the time efficiency of requests

## Algorithm
1. Give user to choose trace from the traces list

2. run this trace

3. for each request, calculate requst's elapsed time (ms)

4. during running print for each entry: URL, HIT or MISS, elapsed time, response size,  elapsed time / response size

5. in the end print avg of all this entries, group by HIT/MISS

6. print the headline metric prominently: the MISS/HIT ratio of avg ms/KB
   (e.g. "MISS is 8.00x slower than HIT (ms/KB)")

7. export the run to an Excel file, containing:
   - the run's timestamp
   - the chosen trace ID
   - the MISS/HIT ms/KB ratio, highlighted
   - the final output table (avg per HIT/MISS)

## Excel export
Each run creates a new `.xlsx` file in the `hit_miss_reports/` folder
(created at the project root if it doesn't already exist).

- File name: `hit_miss_<trace_id>_<YYYYmmdd_HHMMSS>.xlsx`
- Sheet `Summary` contains:
  - `Timestamp` and `Trace ID` rows
  - A highlighted headline cell with the MISS/HIT ms/KB ratio
  - The final output table: Status, Count, Avg elapsed (ms), Avg size (KB), Avg ms/KB

These generated report files are not committed to git.

