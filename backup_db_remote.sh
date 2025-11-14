#!/bin/bash
# Remote backup script - choose one method below

# Option A: SCP to another server
# scp ~/Salsa2Simulator/salsa2.db user@backup-server:/path/to/backups/salsa2_$(date +%Y%m%d).db

# Option B: Rsync to remote server (more efficient)
# rsync -avz ~/Salsa2Simulator/salsa2.db user@backup-server:/path/to/backups/

# Option C: Cloud storage (rclone - supports Google Drive, Dropbox, etc.)
# Install: sudo apt install rclone
# Configure: rclone config
# Then use:
# rclone copy ~/Salsa2Simulator/salsa2.db remote:Salsa2_backups/

echo "Choose and uncomment one backup method above"
