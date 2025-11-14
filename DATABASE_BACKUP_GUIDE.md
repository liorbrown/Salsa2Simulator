# Database Backup Guide for Salsa2 Simulator

## Why backup your database?
Your `salsa2.db` contains all your simulation data:
- Requests history
- Trace definitions
- Run results
- Cache configurations
- Performance metrics

**Current risk**: Database only exists in your VM - if VM fails, all data is lost!

## Backup Methods

### 🎯 Method 1: Local Timestamped Backups (EASIEST)

**Created script**: `backup_db.sh`

**Usage**:
```bash
# Run manual backup
./backup_db.sh

# Or setup automatic backups (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * ~/Salsa2Simulator/backup_db.sh") | crontab -
```

**Benefits**:
- ✅ Keeps last 10 versions automatically
- ✅ Timestamped backups
- ✅ Stored in `~/Salsa2_backups/`
- ✅ Can restore any recent version

**Restore**:
```bash
# List available backups
ls -lh ~/Salsa2_backups/

# Restore specific backup
cp ~/Salsa2_backups/salsa2_20251114_143000.db ~/Salsa2Simulator/salsa2.db
```

---

### ☁️ Method 2: Cloud Backup with rclone

**Setup** (one-time):
```bash
# Install rclone
sudo apt install rclone

# Configure your cloud provider (Google Drive, Dropbox, etc.)
rclone config
```

**Backup to cloud**:
```bash
# Manual backup
rclone copy ~/Salsa2Simulator/salsa2.db gdrive:Salsa2_backups/

# Automated (add to crontab)
0 3 * * * rclone copy ~/Salsa2Simulator/salsa2.db gdrive:Salsa2_backups/
```

**Benefits**:
- ✅ Off-site backup (survives VM failure)
- ✅ Free tier available on most cloud providers
- ✅ Access from anywhere

---

### 🖥️ Method 3: Remote Server Backup (SCP/Rsync)

**If you have another Linux server**:

```bash
# One-time SCP
scp ~/Salsa2Simulator/salsa2.db user@backup-server:/backups/salsa2_$(date +%Y%m%d).db

# Or automated rsync (more efficient)
rsync -avz ~/Salsa2Simulator/salsa2.db user@backup-server:/backups/
```

**Add to crontab for automation**:
```bash
0 4 * * * rsync -avz ~/Salsa2Simulator/salsa2.db user@backup-server:/backups/salsa2_$(date +\%Y\%m\%d).db
```

---

### 💾 Method 4: Git LFS (Large File Storage)

**For tracking DB in Git without bloating repo**:

```bash
# Install Git LFS
sudo apt install git-lfs
git lfs install

# Track database files
git lfs track "*.db"
git add .gitattributes

# Now you can commit DB (stored separately)
git add salsa2.db
git commit -m "Backup database snapshot"
git push
```

**Benefits**:
- ✅ Version controlled
- ✅ Doesn't bloat Git repo
- ✅ Can track changes over time

**Drawbacks**:
- ❌ GitHub free tier: 1GB storage, 1GB bandwidth/month
- ❌ Extra setup complexity

---

## Recommended Strategy

**Best approach for your situation**:

1. **Daily local backups**: Use `backup_db.sh` script with cron
2. **Weekly cloud backup**: Use rclone to Google Drive/Dropbox
3. **Before major changes**: Manual backup with descriptive name

**Example cron setup**:
```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily local backup at 2 AM
0 2 * * * ~/Salsa2Simulator/backup_db.sh

# Weekly cloud backup every Sunday at 3 AM
0 3 * * 0 rclone copy ~/Salsa2Simulator/salsa2.db gdrive:Salsa2_backups/salsa2_$(date +\%Y\%m\%d).db
```

---

## Quick Commands

```bash
# Manual backup with description
cp ~/Salsa2Simulator/salsa2.db ~/Salsa2_backups/salsa2_before_experiment.db

# Check backup size
du -h ~/Salsa2Simulator/salsa2.db

# List all backups
ls -lht ~/Salsa2_backups/

# Restore latest backup
cp $(ls -t ~/Salsa2_backups/salsa2_*.db | head -1) ~/Salsa2Simulator/salsa2.db
```

---

## Already Protected

✅ Your `.gitignore` already excludes:
- `*.db`
- `salsa2.db`
- `*.db-journal`

So database will NEVER accidentally get committed to Git.
