# Windows Automatic Backup - Quick Start

## 🎯 Goal
Automatically backup your Salsa2 database from Linux VM to Windows OneDrive daily

---

## ⚡ Quick Setup (5 minutes)

### 0️⃣ Enable PowerShell Scripts (One-time)

**Open PowerShell as Administrator** and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type `Y` and press Enter.

This allows you to run local PowerShell scripts.

### 1️⃣ Copy files to Windows

Copy these 2 files from VM to your Windows machine:
- `backup_salsa2_from_vm.ps1`
- `setup_scheduled_backup.ps1`

**To this folder:**
```
C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\
```

**How to copy:**
- Use your SSHFS mount, OR
- From Windows PowerShell:
  ```powershell
  scp lior@proxy:/home/lior/Salsa2Simulator/backup_salsa2_from_vm.ps1 "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\"
  scp lior@proxy:/home/lior/Salsa2Simulator/setup_scheduled_backup.ps1 "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\"
  ```

### 2️⃣ Test manual backup

Open **PowerShell** (not as admin) and run:
```powershell
cd "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2"
.\backup_salsa2_from_vm.ps1
```

✅ Should see: "Backup completed successfully!"

### 3️⃣ Setup automatic daily backups

Open **PowerShell as Administrator** and run:
```powershell
cd "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2"
.\setup_scheduled_backup.ps1
```

✅ Should see: "Scheduled task created successfully!"

### 4️⃣ Done! 🎉

Your database will now backup automatically every day at 2:00 AM to:
```
C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup\
```

---

## 🔧 If Something Goes Wrong

### Check if OpenSSH is installed:
```powershell
ssh -V
scp -V
```

If not installed:
```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Test VM connection:
```powershell
ssh lior@proxy
```

If "proxy" doesn't work, try VM's IP address:
```powershell
ssh lior@192.168.1.XXX  # Replace with your VM IP
```

Then update `backup_salsa2_from_vm.ps1` to use the IP instead of "proxy".

---

## 📋 Useful Commands

```powershell
# Run backup now
Start-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# Check if task exists
Get-ScheduledTask -TaskName "Salsa2 Database Backup from VM"

# View recent backups
Get-ChildItem "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup" | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

---

## 📚 Full Documentation

For complete details, see: `WINDOWS_AUTO_BACKUP_GUIDE.md`

---

## 🔄 Alternative: Simple Batch File

Don't like PowerShell? Use `backup_salsa2.bat` instead!

Just double-click it to backup manually.
