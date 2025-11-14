# Windows Automatic Backup Setup Guide

## Overview
This guide helps you set up automatic database backups from your Linux VM to Windows OneDrive using your existing SSHFS connection.

---

## Prerequisites

✅ You already have:
- SSH access to your VM (lior@proxy)
- SSHFS or similar SSH-based file access set up

✅ You'll need:
- SCP command available on Windows (comes with OpenSSH client)
- PowerShell

---

## Quick Setup (5 minutes)

### Step 1: Copy Scripts to Windows

Copy these two files from your VM to Windows OneDrive:
```
backup_salsa2_from_vm.ps1
setup_scheduled_backup.ps1
```

**Destination on Windows:**
```
C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\
```

**Copy using your SSHFS mount** or run from VM:
```bash
# If you have SSHFS mounted on Windows, just copy the files
# Or use SCP from Windows PowerShell:
# scp lior@proxy:/home/lior/Salsa2Simulator/backup_salsa2_from_vm.ps1 "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\"
# scp lior@proxy:/home/lior/Salsa2Simulator/setup_scheduled_backup.ps1 "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\"
```

### Step 2: Edit Configuration (if needed)

Open `backup_salsa2_from_vm.ps1` in Notepad and verify these settings:
```powershell
$VM_USER = "lior"
$VM_HOST = "proxy"  # Change to VM's IP if "proxy" doesn't resolve
$VM_DB_PATH = "/home/lior/Salsa2Simulator/salsa2.db"
$ONEDRIVE_BACKUP_PATH = "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup"
```

### Step 3: Test Manual Backup

Open PowerShell and run:
```powershell
cd "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2"
.\backup_salsa2_from_vm.ps1
```

You should see:
```
✓ Backup completed successfully!
✓ File: salsa2_20251114_123456.db
✓ Size: 51 MB
```

### Step 4: Setup Automatic Daily Backups

**Run PowerShell as Administrator**, then:
```powershell
cd "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2"

# Update the script path in setup_scheduled_backup.ps1 if needed
.\setup_scheduled_backup.ps1
```

This creates a Windows Task Scheduler task that runs daily at 2:00 AM.

---

## Verify Automatic Backup is Set Up

### Check Task Scheduler:
```powershell
Get-ScheduledTask -TaskName "Salsa2 Database Backup from VM"
```

### Test the scheduled task:
```powershell
Start-ScheduledTask -TaskName "Salsa2 Database Backup from VM"
```

### View task history:
```powershell
Get-ScheduledTask -TaskName "Salsa2 Database Backup from VM" | Get-ScheduledTaskInfo
```

---

## Backup Schedule

**Default**: Daily at 2:00 AM
**Retention**: Keeps last 10 backups automatically

To change the schedule:
1. Open Task Scheduler (taskschd.msc)
2. Find "Salsa2 Database Backup from VM"
3. Edit the trigger

---

## Backup Location

All backups are stored in:
```
C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup\
```

Files are named:
```
salsa2_20251114_020000.db  (YearMonthDay_HourMinuteSecond)
```

---

## Manual Backup Anytime

Just run from PowerShell:
```powershell
cd "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2"
.\backup_salsa2_from_vm.ps1
```

---

## Troubleshooting

### "SCP not found"
Install OpenSSH Client on Windows:
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### "Host key verification failed"
Connect to VM manually once:
```powershell
ssh lior@proxy
# Accept the host key, then exit
```

### "Permission denied"
Make sure your SSH keys are set up for passwordless login:
```bash
# On Linux VM, add your Windows public key to authorized_keys
cat ~/.ssh/id_rsa.pub  # Copy this
# Then add to ~/.ssh/authorized_keys
```

### "Network path not found"
Check if VM is reachable:
```powershell
ping proxy
# or
ping <VM_IP_ADDRESS>
```

If "proxy" doesn't resolve, edit the script to use IP address instead:
```powershell
$VM_HOST = "192.168.1.100"  # Use your actual VM IP
```

---

## Advanced: Run Backup on Multiple Events

To backup on other events (not just daily), edit the task in Task Scheduler:
- On system startup
- On user logon
- On network connection
- Every X hours

---

## Monitoring

The script creates a log in PowerShell output. To save logs:
```powershell
.\backup_salsa2_from_vm.ps1 > "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\backup_log.txt" 2>&1
```

Or modify the scheduled task to log output:
1. Task Scheduler → Your Task → Actions → Edit
2. Add arguments: `>> "C:\path\to\log.txt" 2>&1`

---

## Benefits

✅ **Automatic**: Runs daily without manual intervention
✅ **OneDrive Sync**: Automatically backed up to cloud via OneDrive
✅ **Retention**: Keeps last 10 versions
✅ **Timestamped**: Easy to identify and restore specific versions
✅ **Low Impact**: Runs at 2 AM when you're likely not using the VM
✅ **Safe**: Uses existing SSH connection (no new security holes)

---

## Quick Commands Reference

```powershell
# Test backup now
Start-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# Check task status
Get-ScheduledTaskInfo -TaskName "Salsa2 Database Backup from VM"

# Disable automatic backups
Disable-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# Enable automatic backups
Enable-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# Remove automatic backups
Unregister-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# List all backups
Get-ChildItem "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup" -Filter "salsa2_*.db" | Sort-Object LastWriteTime -Descending
```
