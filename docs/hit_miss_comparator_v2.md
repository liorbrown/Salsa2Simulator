# HIT/MISS comparator - V2

## General
This file will describe the functionality of current script
, This script code will use all the existing code it can from the existed simulator code

## Goal
The goal of this script is to estimate how much the cache improves the time efficiency of requests

## Algorithm
1. clear all parents cache data

2. Give user to choose trace from the traces list

3. run this trace once

4. for each request, calculate requst's elapsed time (ms)

5. during running print for each entry: (DONE/ TOTAL), URL, HIT or MISS, elapsed time

6. in the end print the sum of time of all MISSes

7. repeat steps 2 - 4 (same trace!)

8. in the end print the sum of time of all HITs that in privous run was MISS,
so the two runs prints the time of exact same set of requests

9. print the headline metric prominently: the MISS/HIT ratio of time
   (e.g. "MISS is 8.00x slower than HIT")

10. export the run to an Excel file, containing:
   - the run's timestamp
   - the chosen trace ID
   - the MISS/HIT time ratio, highlighted
   - the final output table (avg per HIT/MISS)

## Excel export
Each run creates a new `.xlsx` file in the `hit_miss_reports/` folder
(created at the project root if it doesn't already exist).

- File name: `hit_miss_<trace_id>_<YYYYmmdd_HHMMSS>.xlsx`
- Sheet `Summary` contains:
  - `Timestamp`, `Trace ID` and `Compared requests` (the shared MISS/HIT count) rows
  - A highlighted headline cell with the MISS/HIT time ratio
  - The final output table: Status, Avg elapsed (ms)

These generated report files are not committed to git.

