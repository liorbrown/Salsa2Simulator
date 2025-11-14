#!/bin/bash
# Backup to Windows OneDrive via shared folder or network mount

# OPTION A: If you have a shared folder mounted (VMware/VirtualBox)
# Adjust this path to match your shared folder mount point
ONEDRIVE_PATH="/mnt/hgfs/OneDrive/ליאור/מחקר/Salsa2/DB Backup"

# OPTION B: If using SMB/CIFS network share (uncomment and configure)
# ONEDRIVE_PATH="/mnt/onedrive/ליאור/מחקר/Salsa2/DB Backup"

# OPTION C: If using WSL2 (Windows Subsystem for Linux)
# ONEDRIVE_PATH="/mnt/c/Users/חייםליאורבראון/OneDrive/ליאור/מחקר/Salsa2/DB Backup"

# Check if OneDrive path is accessible
if [ ! -d "$ONEDRIVE_PATH" ]; then
    echo "❌ Error: OneDrive path not accessible: $ONEDRIVE_PATH"
    echo ""
    echo "Please configure the correct path in this script."
    echo "Current mount points:"
    mount | grep -E "mnt|shared"
    exit 1
fi

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create backup directory if it doesn't exist
mkdir -p "$ONEDRIVE_PATH"

# Backup database with timestamp
cp ~/Salsa2Simulator/salsa2.db "$ONEDRIVE_PATH/salsa2_${TIMESTAMP}.db"

if [ $? -eq 0 ]; then
    echo "✓ Database backed up to OneDrive: salsa2_${TIMESTAMP}.db"
    echo "✓ Location: $ONEDRIVE_PATH"
    echo ""
    echo "Backup files in OneDrive:"
    ls -lh "$ONEDRIVE_PATH"/salsa2_*.db 2>/dev/null | tail -5
else
    echo "❌ Backup failed!"
    exit 1
fi
