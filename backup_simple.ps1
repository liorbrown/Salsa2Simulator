# Simple PowerShell backup script - Working Version
# Run this from: C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\
# Configuration
$VM_USER = "lior"
$VM_HOST = "192.168.10.52"
$VM_DB_PATH = "/home/lior/Salsa2Simulator/salsa2.db"

# Create timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "salsa2_backup_$timestamp.db"

Write-Host "Backing up database from VM..." -ForegroundColor Yellow
Write-Host "Source: $VM_USER@$VM_HOST`:$VM_DB_PATH"
Write-Host "Target: .\$backupFile (current directory)"
Write-Host ""

# Use relative path (.) to avoid Hebrew character encoding issues with SCP
scp "${VM_USER}@${VM_HOST}:${VM_DB_PATH}" ".\$backupFile"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "SUCCESS! Backup completed." -ForegroundColor Green
    $size = [math]::Round((Get-Item ".\$backupFile").Length / 1MB, 2)
    Write-Host "File: $backupFile ($size MB)" -ForegroundColor Green
    
    # Cleanup old backups (keep last 10)
    Get-ChildItem -Path . -Filter "salsa2_backup_*.db" | 
        Sort-Object LastWriteTime -Descending | 
        Select-Object -Skip 10 | 
        Remove-Item -Force
    
    $count = (Get-ChildItem -Path . -Filter "salsa2_backup_*.db").Count
    Write-Host "Total backups: $count" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "FAILED! Backup did not complete." -ForegroundColor Red
    exit 1
}
