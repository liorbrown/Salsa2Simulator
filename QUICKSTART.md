# Quick Start Guide

Get up and running with Salsa2 Simulator in 5 minutes!

## Prerequisites

- Python 3.12 or higher
- Squid proxy server (local or remote)
- Git (for cloning)

## Installation

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/liorbrown/Salsa2Simulator.git
cd Salsa2Simulator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy configuration template
cp salsa2.config.example salsa2.config

# Edit configuration (use your favorite editor)
nano salsa2.config
```

**Minimal configuration** (edit these lines):

```ini
db_file='/home/yourusername/salsa2.db'
conf_file='/etc/squid/squid.conf'
http_proxy='http://127.0.0.1:3128'
```

### 3. Initialize Database

The database will be created automatically on first run, but ensure the path is writable:

```bash
touch ~/salsa2.db  # Or path specified in salsa2.config
```

## First Run

### Start the Simulator

```bash
python3 salsa2.py
```

You'll see:

```
################# Welcome to Salsa2 simulator ####################
Choose your destiny:
  1: Show previous runs
  2: Show Traces
  3: Show last requests
  4: Execute single request
  5: Run entire trace
  6: Manage caches
  0: Exit
```

### Test Single Request

1. Choose option **4** (Execute single request)
2. Enter a test URL: `http://www.google.com`
3. View the result showing:
   - Which cache served it
   - Access cost
   - Hit/miss status

**Example output:**
```
Enter URL: http://www.google.com
Request fetched successfully from P1 at cost of 10
```

## Create Your First Trace

### Generate Random Trace

```bash
# Run trace generator
python3 traces/trace_generator.py
```

Follow the prompts:
```
Insert traces name: TestTrace
Insert number of traces to create: 1
Insert number of entries to create in each trace: 100
```

### Run the Trace

1. Start simulator: `python3 salsa2.py`
2. Choose option **5** (Run entire trace)
3. Enter run name: `FirstRun`
4. Select your trace ID (shown in table)
5. Set limit: `100` (or `0` for unlimited)
6. Watch it execute!

**Expected output:**
```
┌────┬───────────┬─────────────────────┬─────────────────────┬───────────┬──────────┬─────────────┬──────────────┐
│ ID │ Name      │ Start Time          │ End Time            │ Trace     │ Requests │ Total Cost  │ Average Cost │
├────┼───────────┼─────────────────────┼─────────────────────┼───────────┼──────────┼─────────────┼──────────────┤
│ 1  │ FirstRun  │ 2025-11-13 14:30:00 │ 2025-11-13 14:32:15 │ TestTrace │ 100      │ 1250.00     │ 12.50        │
└────┴───────────┴─────────────────────┴─────────────────────┴───────────┴──────────┴─────────────┴──────────────┘
```

## Common Tasks

### View Previous Runs

```bash
# Option 1 from main menu
```

Shows all completed simulation runs with costs and statistics.

### Inspect Traces

```bash
# Option 2 from main menu
```

Lists all available traces and their URL counts.

### Manage Caches

```bash
# Option 6 from main menu
```

Submenu for:
- Viewing configured caches
- Adding new caches
- Updating cache properties
- Deleting caches

## Troubleshooting

### "Module not found" errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database errors

```bash
# Check database path
cat salsa2.config | grep db_file

# Ensure directory exists and is writable
ls -l $(dirname /your/db/path)
```

### Proxy connection errors

```bash
# Test Squid is running
curl -x http://127.0.0.1:3128 http://www.google.com

# Check Squid status
sudo systemctl status squid
```

### SSH/Cache clearing errors

```bash
# Set password environment variable
export SQUID_PASS='your_password'

# Test SSH connection
ssh your_user@cache_server_ip
```

## Next Steps

- Read [README.md](README.md) for comprehensive documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- View [REFACTORING_README.md](REFACTORING_README.md) for technical details
- Explore the modular codebase in organized directories

## Getting Help

- **Documentation**: Check README.md first
- **Issues**: Search [GitHub Issues](https://github.com/liorbrown/Salsa2Simulator/issues)
- **Discussions**: Open a new issue with "question" label

## Tips

1. **Start small**: Test with 10-20 URLs before running large traces
2. **Monitor Squid logs**: `tail -f /var/log/squid/access.log`
3. **Backup database**: Before major runs: `cp salsa2.db salsa2.db.backup`
4. **Use trace limits**: Test with small limits before full runs
5. **Check costs**: Review cache access costs before running expensive traces

---

**Happy Simulating!** 🚀

For detailed information, see the [full README](README.md).
