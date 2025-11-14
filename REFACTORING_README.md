# Salsa2 Simulator - Refactored Structure

## Overview
The Salsa2 Simulator has been refactored into a clean, modular architecture for better maintainability and extensibility.

## Project Structure

```
Salsa2Simulator/
├── salsa2.py               # Main entry point (~80 lines)
├── config/                 # Configuration management
│   ├── __init__.py
│   └── config.py          # MyConfig class and configuration loading
├── database/               # Database access layer
│   ├── __init__.py
│   └── db_access.py       # DBAccess class for SQLite operations
├── parsers/                # External data parsers
│   ├── __init__.py
│   ├── httpParser.py
│   ├── shodanParser.py
│   └── MajestaParser.py
├── requests/               # HTTP request execution
│   ├── __init__.py
│   └── request_executor.py # execute_req, execute_single_req, get_proxies_for_cache
├── cache/                  # Cache management and operations
│   ├── __init__.py
│   └── cache_manager.py   # Cache CRUD, clearing, cost calculations, fill_caches
├── simulation/             # Trace simulation orchestration
│   ├── __init__.py
│   └── simulator.py       # run_trace function
├── ui/                     # Display and user interface
│   ├── __init__.py
│   └── display.py         # show_runs, show_traces, show_requests, etc.
├── traces/                 # Trace generation
│   ├── __init__.py
│   └── trace_generator.py # Trace generation utilities
└── old/                    # Backup of original files
    └── *.py               # Original monolithic files

```

## Key Changes

### Before
- Single `salsa2.py` file (~900 lines)
- Mixed responsibilities
- Difficult to test and maintain
- Hard to understand code flow

### After
- Clean separation of concerns
- Each module has a single responsibility
- Main file is now ~80 lines (orchestration only)
- Easy to test individual components
- Clear imports and dependencies

## Module Responsibilities

### `config/`
- Load and manage configuration from `salsa2.config`
- Provide CA bundle paths
- Centralized configuration access

### `database/`
- SQLite connection management
- Database open/close operations
- Cursor access

### `parsers/`
- Parse external data sources (HTTP, Shodan, Majesta)
- Independent from core simulator logic

### `requests/`
- Execute HTTP requests through Squid proxies
- Manage proxy configuration
- Handle request logging and errors
- **Key feature**: Automatic redirect following disabled for full control

### `cache/`
- Cache CRUD operations (show, add, update, delete)
- Clear cache directories via SSH
- Cost calculations
- Cache status monitoring
- Load cache configurations from Squid config files

### `simulation/`
- Orchestrate trace runs
- Execute all URLs in a trace
- Track run statistics and costs
- Display run results

### `ui/`
- Display functions for runs, traces, requests
- PrettyTable formatting
- Accuracy metrics and classification statistics
- User input handling

### `traces/`
- Generate random traces
- Populate trace entries in database

## Running the Simulator

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run the simulator
python3 salsa2.py
```

## Benefits of Refactoring

1. **Maintainability**: Each module is focused and easier to understand
2. **Testability**: Individual components can be tested in isolation
3. **Extensibility**: Easy to add new features or parsers
4. **Reusability**: Modules can be imported and used in other projects
5. **Collaboration**: Multiple developers can work on different modules
6. **Debugging**: Easier to locate and fix bugs in specific modules

## Backward Compatibility

- All original functionality is preserved
- Old files backed up in `old/` directory
- Database schema unchanged
- Configuration file format unchanged

## Migration Notes

If you have scripts that import from the old structure:

**Old:**
```python
from DBAccess import DBAccess
from MyConfig import MyConfig
```

**New:**
```python
from database.db_access import DBAccess
from config.config import MyConfig
```

## Important Changes

### Redirect Handling
The request executor now has `allow_redirects=False` by default. This ensures:
- Exactly one request per URL (no automatic redirect following)
- Squid can cache 301/302 redirect responses
- Full control over what gets sent to the proxy
- Accurate request counting for cost calculations

## Future Enhancements

Potential areas for future improvement:
- Add unit tests for each module
- Add type hints throughout the codebase
- Create a REST API wrapper
- Add logging instead of print statements
- Configuration file validation
- Async request execution for better performance
