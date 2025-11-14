# Windows Task Scheduler Setup Instructions
# Save this as: setup_scheduled_backup.ps1
# Run this in PowerShell as Administrator

# Configuration
$SCRIPT_PATH = "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\backup_salsa2_from_vm.ps1"
$TASK_NAME = "Salsa2 Database Backup from VM"
$SCHEDULE_TIME = "02:00"  # 2:00 AM daily

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Scheduled Backup Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task already exists. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false
}

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$SCRIPT_PATH`""

# Create the trigger (daily at specified time)
$trigger = New-ScheduledTaskTrigger -Daily -At $SCHEDULE_TIME

# Create the settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Get current user
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TASK_NAME `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automatically backup Salsa2 database from Linux VM to OneDrive" | Out-Null
    
    Write-Host "✓ Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TASK_NAME" -ForegroundColor Gray
    Write-Host "  Schedule: Daily at $SCHEDULE_TIME" -ForegroundColor Gray
    Write-Host "  Script: $SCRIPT_PATH" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To test the backup now, run:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TASK_NAME'" -ForegroundColor White
    Write-Host ""
    Write-Host "To view task status:" -ForegroundColor Yellow
    Write-Host "  Get-ScheduledTask -TaskName '$TASK_NAME' | Get-ScheduledTaskInfo" -ForegroundColor White
    
} catch {
    Write-Host "✗ Failed to create scheduled task: $_" -ForegroundColor Red
    exit 1
}
