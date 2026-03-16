# Agent Guidelines for check-repo-status

## Build, Lint, and Test Commands

- **Install dependencies**: `make install` (uses uv for virtual environment and dependency management)
- **Run all tests**: `make test` or `PYTHONPATH=src uv run pytest`
- **Run a single test**: `PYTHONPATH=src uv run pytest tests/test_check_repo_status.py::test_name`
- **Run tests with coverage**: `PYTHONPATH=src uv run pytest --cov=check_repo_status`
- **Clean cache files**: `make clean`

## Code Style Guidelines

### General Structure
- Package uses `src/` layout with module in `src/check_repo_status/`
- Tests are in `tests/` directory following pytest conventions
- Entry points defined in `pyproject.toml`

### Imports
- Standard library imports first, then third-party, then local imports
- Use explicit imports rather than wildcards
- Group imports logically with blank lines between groups

### Formatting
- Follow PEP 8 style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (compatible with black formatter)
- Use double quotes for strings unless single quotes are needed to avoid escaping

### Types and Naming
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Use descriptive variable names that convey purpose

### Error Handling
- Use appropriate exception handling with specific exception types
- Provide clear error messages that help users understand issues
- Exit gracefully with proper status codes (0 for success, non-zero for errors)
- Use sys.exit() for user-facing error conditions

### GitPython Usage
- Handle GitCommandError and InvalidGitRepositoryError exceptions
- Use repo.active_branch as primary branch reference with fallbacks to main/master
- Implement caching for git fetch operations to improve performance
- Use proper resource management when working with GitPython objects

### Testing
- Use pytest with mocks for external dependencies
- Follow AAA pattern (Arrange, Act, Assert) in tests
- Test both success and failure cases
- Use temporary directories for filesystem tests