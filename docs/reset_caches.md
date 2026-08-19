# Reset Caches Script

## Goal
This script will clean all caches data

## Architecture
My squid cache system assamble from 3 nodes:
192.168.10.52 (current) - Includes this simulator and squid proxy
this squid proxy configure to hold no data, it only forward to the 2 parents:
192.168.10.50, 192.168.10.51

## Algo
This script will access 192.168.10.50, 192.168.10.51 via SSH and foreach:
1. Delete all caches data on their storage
2. Restart squid for ensure there will be no data holds in its memory

## Note
The structure of the squid and its data directories is equal to the squid of current node,
so u can use this node to explore and ensure squid configuration if needed