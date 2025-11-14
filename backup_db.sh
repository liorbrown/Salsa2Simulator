#!/bin/bash
# Database backup script for Salsa2 Simulator

# Create backups directory if it doesn't exist
mkdir -p ~/Salsa2_backups

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Backup database with timestamp
cp ~/Salsa2Simulator/salsa2.db ~/Salsa2_backups/salsa2_${TIMESTAMP}.db

# Keep only last 10 backups (delete older ones)
cd ~/Salsa2_backups
ls -t salsa2_*.db | tail -n +11 | xargs -r rm

echo "✓ Database backed up to: ~/Salsa2_backups/salsa2_${TIMESTAMP}.db"
echo "Total backups: $(ls -1 salsa2_*.db 2>/dev/null | wc -l)"
