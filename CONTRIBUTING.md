# Contributing to Salsa2 Simulator

Thank you for your interest in contributing to Salsa2 Simulator! This document provides guidelines and instructions for contributing.

## 🌟 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- **Clear title**: Brief description of the bug
- **Steps to reproduce**: Detailed steps to recreate the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Environment**: OS, Python version, Squid version
- **Logs**: Relevant error messages or log excerpts

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:
- **Clear title**: Brief description of the enhancement
- **Motivation**: Why this enhancement would be useful
- **Proposed solution**: How you envision it working
- **Alternatives**: Other solutions you've considered

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/liorbrown/Salsa2Simulator.git
   cd Salsa2Simulator
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add docstrings to new functions/classes
   - Update documentation if needed

4. **Test your changes**
   - Ensure existing functionality still works
   - Test new features thoroughly
   - Add unit tests if applicable

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference related issues
   - Include screenshots if UI changes

## 📝 Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) style guidelines:

```python
# Good
def execute_request(url: str, run_id: int) -> int:
    """
    Execute a request through the proxy.
    
    Args:
        url: The URL to request
        run_id: The run identifier
        
    Returns:
        Request ID if successful, None otherwise
    """
    pass

# Bad
def ExecReq(URL,runid):
    pass
```

### Module Organization

- Each module should have a single, clear responsibility
- Use `__init__.py` for clean imports
- Keep functions focused and small (< 50 lines when possible)

### Documentation

- Add docstrings to all public functions and classes
- Use type hints for function parameters and returns
- Update README.md for user-facing changes
- Update REFACTORING_README.md for architectural changes

### Commit Messages

Use clear, descriptive commit messages:

```
Good:
- Add: Support for IPv6 proxy addresses
- Fix: Cache clearing timeout on slow connections
- Update: README with new configuration options
- Refactor: Split large cache_manager.py module

Bad:
- fixed stuff
- update
- WIP
```

## 🧪 Testing

Currently, the project doesn't have automated tests. Contributions adding test coverage are highly valued!

### Manual Testing Checklist

Before submitting a PR, verify:
- [ ] Main menu loads correctly
- [ ] Database operations work (reads/writes)
- [ ] Single request execution succeeds
- [ ] Trace runs complete without errors
- [ ] Cache management functions work
- [ ] No Python exceptions in normal operation

## 📦 Project Structure

When adding new features:

```
Salsa2Simulator/
├── config/         # Configuration management only
├── database/       # Database operations only
├── cache/          # Cache-related operations
├── requests/       # HTTP request handling
├── simulation/     # Trace execution logic
├── ui/             # Display and user interaction
├── traces/         # Trace generation
└── parsers/        # External data parsing
```

Place new code in the appropriate module. If uncertain, open an issue for discussion.

## 🐛 Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Inspection

```bash
sqlite3 salsa2.db
.tables
SELECT * FROM Runs LIMIT 5;
```

### Squid Logs

```bash
tail -f /var/log/squid/access.log
```

## 🔒 Security

- **Never commit** `salsa2.config` or files containing passwords
- Use environment variables for sensitive data
- Report security vulnerabilities privately via email
- Don't include API keys or tokens in code

## 📋 Code Review Process

Pull requests will be reviewed for:
1. **Functionality**: Does it work as intended?
2. **Code quality**: Is it readable and maintainable?
3. **Documentation**: Are changes documented?
4. **Style**: Does it follow coding standards?
5. **Impact**: Does it break existing functionality?

## ❓ Questions

If you have questions:
- Check existing [issues](https://github.com/liorbrown/Salsa2Simulator/issues)
- Read the [README.md](README.md) and [REFACTORING_README.md](REFACTORING_README.md)
- Open a new issue with the "question" label

## 🎉 Recognition

Contributors will be acknowledged in:
- GitHub contributors page
- Release notes
- Future README updates (if significant contribution)

Thank you for helping improve Salsa2 Simulator! 🚀
