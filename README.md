# Salsa2 Simulator

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive simulator for testing and analyzing cache performance with Squid proxy servers in hierarchical cache architectures. Salsa2 enables cost-based evaluation of cache hit ratios, network access patterns, and cache selection algorithms.

## 🎯 Features

- **Trace-Based Simulation**: Execute predefined URL traces through Squid proxy hierarchies
- **Cost Analysis**: Calculate and compare access costs across different cache configurations
- **Cache Management**: Monitor, configure, and clear cache servers remotely
- **Performance Metrics**: Detailed accuracy, precision, recall, and F1-score analysis
- **Multiple Proxy Support**: Route HTTP and HTTPS through separate proxy servers
- **Real-Time Monitoring**: Track cache hits, misses, and resolution patterns
- **Squid Integration**: Parse Squid configuration files and access Squid logs

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Key Concepts](#key-concepts)
- [Contributing](#contributing)
- [License](#license)

## 🏗️ Architecture

Salsa2 Simulator employs a modular architecture with clear separation of concerns:

```
┌─────────────────┐
│   salsa2.py     │  Main orchestrator
└────────┬────────┘
         │
    ┌────┴────────────────────────┐
    │                             │
┌───▼────┐  ┌──────────┐  ┌──────▼─────┐
│Config  │  │ Database │  │ UI/Display │
└───┬────┘  └────┬─────┘  └──────┬─────┘
    │            │               │
┌───▼────────────▼───────────────▼─────┐
│  Cache Manager  │  Request Executor  │
└────────┬────────┴──────────┬─────────┘
         │                   │
    ┌────▼───────────────────▼────┐
    │  Simulation & Trace Engine  │
    └─────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.12 or higher
- Squid proxy server(s) configured with custom logging
- SQLite3
- SSH access to cache servers (for cache clearing operations)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/liorbrown/Salsa2Simulator.git
   cd Salsa2Simulator
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the simulator**
   - Copy `salsa2.config.example` to `salsa2.config`
   - Edit `salsa2.config` with your settings (see [Configuration](#configuration))

5. **Set up environment variables** (optional)
   ```bash
   export SQUID_PASS='your_squid_password'
   ```

## ⚙️ Configuration

Create a `salsa2.config` file in the project root:

```ini
db_file='/path/to/database.db'
conf_file='/path/to/squid.conf'
log_file='/path/to/squid/access.log'
http_proxy='http://127.0.0.1:3128'
https_proxy='http://192.168.10.1:8888'
user='squid_user'
cache_dir='/var/spool/squid'
squid_port='3128'
ca_bundle='/etc/ssl/certs/ca-certificates.crt'
```

### Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `db_file` | Path to SQLite database | `/home/user/salsa2.db` |
| `conf_file` | Squid configuration file path | `/etc/squid/squid.conf` |
| `log_file` | Squid access log path | `/var/log/squid/access.log` |
| `http_proxy` | HTTP proxy server URL | `http://127.0.0.1:3128` |
| `https_proxy` | HTTPS proxy server URL | `http://192.168.10.1:8888` |
| `user` | SSH user for cache servers | `squid` |
| `cache_dir` | Squid cache directory | `/var/spool/squid` |
| `squid_port` | Squid port number | `3128` |
| `ca_bundle` | SSL CA certificates path | `/etc/ssl/certs/ca-certificates.crt` |

## 📖 Usage

### Starting the Simulator

```bash
python3 salsa2.py
```

### Main Menu Options

```
Choose your destiny:
    1: Show previous runs
    2: Show Traces
    3: Show last requests
    4: Execute single request
    5: Run entire trace
    6: Show caches
    0: Exit
```

### Example Workflow

1. **Create a trace** using `TracesGenerator.py`
   ```bash
   python3 traces/trace_generator.py
   ```

2. **View available traces**
   - Select option `2` from main menu
   - Choose a trace to inspect its URLs

3. **Run a simulation**
   - Select option `5` from main menu
   - Choose trace ID and set request limit
   - Monitor execution and results

4. **Analyze results**
   - View cache hit/miss patterns
   - Review cost calculations
   - Examine classification metrics (accuracy, precision, recall, F1-score)

## 📂 Project Structure

```
Salsa2Simulator/
├── salsa2.py                  # Main entry point
├── salsa2.config.example      # Configuration template
├── requirements.txt           # Python dependencies
├── reqUpdate.py               # Requirements updater
├── README.md                  # This file
├── QUICKSTART.md              # Quick start guide
├── CHANGELOG.md               # Version history
├── LICENSE                    # MIT License
│
├── config/                    # Configuration management
│   ├── __init__.py
│   └── config.py              # Configuration loader
│
├── database/                  # Database access layer
│   ├── __init__.py
│   └── db_access.py           # SQLite connection management
│
├── http_requests/             # HTTP request execution
│   ├── __init__.py
│   └── request_executor.py    # Request handling with proxy support
│
├── metrics/                   # Performance metrics
│   ├── __init__.py
│   └── calculator.py          # Accuracy, precision, recall, F1-score
│
├── simulation/                # Simulation engine
│   ├── __init__.py
│   └── simulator.py           # Trace execution orchestration
│
├── ui/                        # User interface
│   ├── __init__.py
│   ├── display.py             # Display functions
│   └── repository.py          # Data repository
│
├── testlabs/                  # Test labs
│   └── run_all_tests.py       # Test runner
│
└── parsers/                   # External data parsers
    ├── __init__.py
    ├── httpParser.py          # HTTP log parser
    ├── shodanParser.py        # Shodan data parser
    ├── MajestaParser.py       # Majesta format parser
    └── trace_generator.py     # Trace creation utilities
```

## 🔑 Key Concepts

### Traces
Predefined sequences of URLs that simulate real-world access patterns. Traces can be:
- Generated randomly from a URL pool
- Imported from web server logs
- Created from Shodan or other external sources

### Runs
A simulation execution where all URLs in a trace are requested through the cache hierarchy. Each run tracks:
- Request timestamps
- Cache access patterns
- Hit/miss resolutions
- Total cost metrics

### Cache Hierarchy
Multi-level cache architecture where:
- **Parent caches**: Upstream proxy servers
- **ICP (Internet Cache Protocol)**: Cache discovery mechanism
- **Cost model**: Each cache has an associated access cost

### Cost Calculation
```
Total Cost = Σ(Cache Access Costs) + Miss Penalty × Number of Misses
```

### Performance Metrics
- **Accuracy**: (TP + TN) / Total
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)
- **F1-Score**: 2 × (Precision × Recall) / (Precision + Recall)

Where:
- **TP** (True Positive): Cache indicated and resolved
- **FP** (False Positive): Cache indicated but did not resolve
- **TN** (True Negative): Cache not indicated and did not resolve
- **FN** (False Negative): Cache not indicated but would have resolved

## 🧪 Testingand Reports

### Run Summary
```
┌────┬──────────┬─────────────────────┬─────────────────────┬──────────┬──────────┬──────────────┬──────────────┐
│ ID │ Name     │ Start Time          │ End Time            │ Trace    │ Requests │ Total Cost   │ Average Cost │
├────┼──────────┼─────────────────────┼─────────────────────┼──────────┼──────────┼──────────────┼──────────────┤
│ 1  │ TestRun1 │ 2025-11-13 10:30:00 │ 2025-11-13 10:45:00 │ Trace1   │ 1000     │ 2500.00      │ 2.50         │
└────┴──────────┴─────────────────────┴─────────────────────┴──────────┴──────────┴──────────────┴──────────────┘
```

### Classification Metrics
```
┌─────────┬──────────┬────────┬───────────┬──────────┐
│ Cache   │ Accuracy │ Recall │ Precision │ F1 Score │
├─────────┼──────────┼────────┼───────────┼──────────┤
│ P1      │ 0.850    │ 0.780  │ 0.820     │ 0.800    │
│ P2      │ 0.920    │ 0.890  │ 0.910     │ 0.900    │
└─────────┴──────────┴────────┴───────────┴──────────┘
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Lior Brown**
- GitHub: [@liorbrown](https://github.com/liorbrown)
- Repository: [Salsa2Simulator](https://github.com/liorbrown/Salsa2Simulator)

## 🙏 Acknowledgments

- Squid Cache project for the robust proxy server
- PrettyTable for console output formatting
- The open-source community for invaluable tools and libraries

--- simulator is designed for research and testing purposes. Ensure proper authorization before testing against production cache servers.
