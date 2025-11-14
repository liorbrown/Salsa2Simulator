# How to Backup Database to Windows OneDrive

## Target Location
```
C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup
```

---

## Method 1: Shared Folder (Easiest)

### Setup (One-time):
1. **In VMware/VirtualBox**: Enable shared folders
   - VMware: VM Settings → Options → Shared Folders
   - VirtualBox: Settings → Shared Folders
   
2. **Share your OneDrive folder** with the VM:
   - Windows Path: `C:\Users\חייםליאורבראון\OneDrive`
   - VM Mount: `/mnt/hgfs/OneDrive` (VMware) or `/media/sf_OneDrive` (VirtualBox)

3. **Update the script** `backup_db_onedrive.sh`:
   ```bash
   # Edit the ONEDRIVE_PATH variable to match your mount point
   nano ~/Salsa2Simulator/backup_db_onedrive.sh
   ```

4. **Run backup**:
   ```bash
   ./backup_db_onedrive.sh
   ```

---

## Method 2: SCP (If Windows has SSH Server)

### Setup (One-time):
1. **Install OpenSSH Server on Windows**:
   - Settings → Apps → Optional Features → Add "OpenSSH Server"
   - Start service: `Start-Service sshd` (PowerShell as Admin)

2. **Update script** `backup_db_scp.sh` with your Windows IP

3. **Run backup**:
   ```bash
   ./backup_db_scp.sh
   ```

---

## Method 3: Manual Transfer (Quick & Simple)

### From Linux VM:
```bash
# Create a timestamped backup
cp ~/Salsa2Simulator/salsa2.db ~/salsa2_$(date +%Y%m%d_%H%M%S).db
```

### From Windows:
1. Open VM's file browser or use WinSCP/FileZilla
2. Download the backup file
3. Move it to: `C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup`

---

## Method 4: OneDrive Sync (Best Long-term)

### Install OneDrive client on Linux:
```bash
# Install rclone
sudo apt install rclone

# Configure OneDrive
rclone config
# Choose: "n" for new remote
# Name: "onedrive"
# Type: "onedrive" (option 31)
# Follow authentication steps

# Backup to OneDrive
rclone copy ~/Salsa2Simulator/salsa2.db "onedrive:/ליאור/מחקר/Salsa2/DB Backup/salsa2_$(date +%Y%m%d).db"
```

---

## Automated Backup to OneDrive

Once configured, add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * ~/Salsa2Simulator/backup_db_onedrive.sh
```

---

## Quick Commands

```bash
# Check current mount points
mount | grep -i "mnt\|shared"

# List shared folders (VMware)
ls /mnt/hgfs/

# List shared folders (VirtualBox)
ls /media/

# Test OneDrive path access
ls "C:\Users\חייםליאורבראון\OneDrive\ליאור\מחקר\Salsa2\DB Backup" 2>/dev/null || echo "Path not accessible from VM"
```
