# Changelog

All notable changes to Salsa2 Simulator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-13

### Major Refactoring
Complete architectural overhaul from monolithic to modular design.

### Added
- **Modular architecture**: Split 900+ line monolith into 8 focused modules
- **Professional documentation**: README, CONTRIBUTING, LICENSE, and detailed guides
- **Configuration example**: Template file for easy setup (`salsa2.config.example`)
- **Enhanced .gitignore**: Comprehensive exclusions for Python projects
- **requirements.txt**: Clear dependency management

### Changed
- **Main entry point**: Reduced from 912 lines to 79 lines
- **Request handling**: Disabled automatic redirects (`allow_redirects=False`) for precise control
- **Import structure**: Organized imports with proper `__init__.py` files
- **Code organization**: Separated concerns into config/, database/, cache/, requests/, simulation/, ui/, traces/, parsers/

### Improved
- **Maintainability**: Each module has single, clear responsibility
- **Testability**: Components can be tested independently
- **Documentation**: Added comprehensive docstrings throughout
- **Error handling**: Consistent error reporting across modules

### Fixed
- Duplicate request issue caused by automatic HTTP redirects
- Import organization and circular dependency issues

### Technical Details
- **Before**: Single `salsa2.py` (912 lines)
- **After**: Main `salsa2.py` (79 lines) + 8 specialized modules
- **Modules created**:
  - `config/`: Configuration management
  - `database/`: SQLite operations
  - `cache/`: Cache management and operations
  - `requests/`: HTTP request execution
  - `simulation/`: Trace orchestration
  - `ui/`: Display and user interface
  - `traces/`: Trace generation
  - `parsers/`: External data parsing

### Migration Notes
See [REFACTORING_README.md](REFACTORING_README.md) for detailed migration guide.

---

## [1.0.0] - 2025-05-04

### Initial Release
- Basic trace simulation functionality
- Squid proxy integration
- Cache hierarchy support
- Cost calculation engine
- Database-backed trace storage
- Remote cache management via SSH
- Classification metrics (accuracy, precision, recall, F1)

### Features
- Execute single requests through proxy
- Run entire traces
- View run history and statistics
- Manage cache configurations
- Parse external data sources (Shodan, HTTP logs, Majesta)

---

## Future Releases

### [Planned]
- Unit test suite
- REST API interface
- Web-based dashboard
- Docker containerization
- Performance optimizations
- ML-based cache prediction
