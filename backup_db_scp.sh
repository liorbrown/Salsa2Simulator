#!/bin/bash
# Backup to Windows machine via SCP (requires OpenSSH Server on Windows)

# Windows machine details
WINDOWS_HOST="YOUR_WINDOWS_IP_OR_HOSTNAME"  # e.g., 192.168.1.100 or DESKTOP-ABC123
WINDOWS_USER="חייםליאורבראון"

# Note: VM IP is 192.168.10.52 if you need to reference it

# OneDrive path on Windows (use forward slashes or escape backslashes)
WINDOWS_PATH="C:/Users/חייםליאורבראון/OneDrive/ליאור/מחקר/Salsa2/DB Backup"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Backing up to Windows via SCP..."
scp ~/Salsa2Simulator/salsa2.db "${WINDOWS_USER}@${WINDOWS_HOST}:${WINDOWS_PATH}/salsa2_${TIMESTAMP}.db"

if [ $? -eq 0 ]; then
    echo "✓ Database backed up to Windows OneDrive successfully!"
else
    echo "❌ Backup failed. Check Windows SSH server and credentials."
fi
