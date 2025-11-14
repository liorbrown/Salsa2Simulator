# PowerShell script to backup Salsa2 database from Linux VM to Windows OneDrive
# Save this as: backup_salsa2_from_vm.ps1

# Configuration
$VM_USER = "lior"
$VM_HOST = "192.168.10.52"
$VM_DB_PATH = "/home/lior/Salsa2Simulator/salsa2.db"
$ONEDRIVE_BACKUP_PATH = "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup"

# Generate timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFileName = "salsa2_$timestamp.db"

# Create backup directory if it doesn't exist
if (-not (Test-Path $ONEDRIVE_BACKUP_PATH)) {
    New-Item -ItemType Directory -Path $ONEDRIVE_BACKUP_PATH -Force | Out-Null
    Write-Host "✓ Created backup directory: $ONEDRIVE_BACKUP_PATH"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Salsa2 Database Backup from VM" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VM: $VM_USER@$VM_HOST"
Write-Host "Source: $VM_DB_PATH"
Write-Host "Destination: $ONEDRIVE_BACKUP_PATH\$backupFileName"
Write-Host ""

# Use SCP to copy the database file
Write-Host "Copying database from VM..." -ForegroundColor Yellow
$scpCommand = "scp ${VM_USER}@${VM_HOST}:${VM_DB_PATH} `"$ONEDRIVE_BACKUP_PATH\$backupFileName`""

try {
    # Execute SCP command
    $result = scp "${VM_USER}@${VM_HOST}:${VM_DB_PATH}" "$ONEDRIVE_BACKUP_PATH\$backupFileName" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Backup completed successfully!" -ForegroundColor Green
        Write-Host "✓ File: $backupFileName" -ForegroundColor Green
        
        # Get file size
        $fileSize = (Get-Item "$ONEDRIVE_BACKUP_PATH\$backupFileName").Length / 1MB
        Write-Host "✓ Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
        
        # Keep only last 10 backups (delete older ones)
        Write-Host ""
        Write-Host "Cleaning up old backups (keeping last 10)..." -ForegroundColor Yellow
        Get-ChildItem -Path $ONEDRIVE_BACKUP_PATH -Filter "salsa2_*.db" | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -Skip 10 | 
            Remove-Item -Force
        
        # List current backups
        $backupCount = (Get-ChildItem -Path $ONEDRIVE_BACKUP_PATH -Filter "salsa2_*.db").Count
        Write-Host "✓ Total backups: $backupCount" -ForegroundColor Green
        
        # Show recent backups
        Write-Host ""
        Write-Host "Recent backups:" -ForegroundColor Cyan
        Get-ChildItem -Path $ONEDRIVE_BACKUP_PATH -Filter "salsa2_*.db" | 
            Sort-Object LastWriteTime -Descending | 
            Select-Object -First 5 | 
            ForEach-Object {
                $size = [math]::Round($_.Length / 1MB, 2)
                Write-Host "  $($_.Name) - $size MB - $($_.LastWriteTime)" -ForegroundColor Gray
            }
    } else {
        Write-Host "✗ Backup failed!" -ForegroundColor Red
        Write-Host "Error: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Error during backup: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backup completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
