# Contributing to GitInspector

Thank you for your interest in contributing to GitInspector! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Development Setup

### Prerequisites

- **Python 3.10 or higher** - GitInspector requires Python 3.10+
- **Poetry** - We use Poetry for dependency management
- **Git** - For version control

### Installing Poetry

If you don't have Poetry installed, you can install it using:

```bash
# On macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# On Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Alternative: using pip
pip install poetry
```

### Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ejwa/gitinspector.git
   cd gitinspector
   ```

2. **Install dependencies:**
   ```bash
   # Install all dependencies including development tools
   poetry install --with dev
   
   # Activate the virtual environment
   poetry shell
   ```

3. **Verify the installation:**
   ```bash
   # Run tests to ensure everything is working
   poetry run pytest
   
   # Run the application
   poetry run gitinspector --help
   ```

## Project Structure

```
gitinspector/
├── gitinspector/           # Main package
│   ├── __init__.py
│   ├── gitinspector.py     # Main entry point
│   ├── blame.py            # Blame analysis
│   ├── changes.py          # Change tracking
│   ├── output/             # Output formatters
│   └── ...
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml          # Poetry configuration
├── Makefile               # Development commands
└── CONTRIBUTING.md        # This file
```

## Development Workflow

### Available Make Commands

We provide a Makefile with common development tasks:

```bash
# Show all available commands
make help

# Install development dependencies
make dev-install

# Run tests
make test

# Run tests with coverage
make test-coverage

# Run linting
make lint

# Format code
make format

# Run type checking
make type-check

# Build the package
make dist

# Clean build artifacts
make clean
```

### Using Poetry Directly

You can also use Poetry commands directly:

```bash
# Install dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run linting
poetry run flake8 gitinspector tests
poetry run pylint gitinspector

# Format code
poetry run black gitinspector tests
poetry run isort gitinspector tests

# Type checking
poetry run mypy gitinspector

# Build package
poetry build

# Update dependencies
poetry update
```

## Code Quality

We maintain high code quality standards using several tools:

### Code Formatting

- **Black**: Code formatter with 120 character line length
- **isort**: Import sorting

Run formatting with:
```bash
make format
# or
poetry run black gitinspector tests
poetry run isort gitinspector tests
```

### Linting

- **flake8**: Style guide enforcement
- **pylint**: Static code analysis

Run linting with:
```bash
make lint
# or
poetry run flake8 gitinspector tests
poetry run pylint gitinspector
```

### Type Checking

- **mypy**: Static type checking

Run type checking with:
```bash
make type-check
# or
poetry run mypy gitinspector
```

### Code Style Guidelines

1. **Python Version**: Target Python 3.10+ features
2. **Line Length**: Maximum 120 characters
3. **Type Hints**: Use type hints for all public functions and methods
4. **Docstrings**: Use Google-style docstrings for all public APIs
5. **F-strings**: Use f-strings for string formatting (no % formatting)
6. **Modern Python**: Use modern Python idioms and features

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
poetry run pytest tests/test_specific.py

# Run tests with verbose output
poetry run pytest -v

# Run tests matching a pattern
poetry run pytest -k "test_pattern"
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Name test files with `test_` prefix
3. Use pytest fixtures for setup/teardown
4. Aim for high test coverage
5. Write both unit and integration tests

### Test Categories

- **Unit Tests**: Test individual functions/classes
- **Integration Tests**: Test component interactions
- **Slow Tests**: Mark with `@pytest.mark.slow` for long-running tests

## Submitting Changes

### Before Submitting

1. **Run the full test suite:**
   ```bash
   make test
   ```

2. **Check code quality:**
   ```bash
   make lint
   make type-check
   ```

3. **Format your code:**
   ```bash
   make format
   ```

4. **Update documentation** if needed

### Pull Request Process

1. **Fork the repository** on GitHub
2. **Create a feature branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the guidelines above
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Commit your changes** with clear, descriptive messages
7. **Push to your fork** and create a pull request

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Release Process

### Version Management

We use semantic versioning (SemVer):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Creating a Release

1. **Update version** in `pyproject.toml`
2. **Update CHANGES.txt** with release notes
3. **Create and push tag:**
   ```bash
   make tag-version
   make push-tagged-version
   ```
4. **Build and publish:**
   ```bash
   make dist
   make release
   ```

## Getting Help

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/ejwa/gitinspector/issues)
- **Discussions**: Join discussions on [GitHub Discussions](https://github.com/ejwa/gitinspector/discussions)
- **Email**: Contact the maintainers at gitinspector@ejwa.se

## Development Tips

### IDE Setup

For the best development experience:

1. **Configure your IDE** to use the Poetry virtual environment
2. **Enable type checking** with mypy
3. **Set up code formatting** to run on save
4. **Configure linting** to show errors inline

### Common Issues

1. **Poetry not found**: Make sure Poetry is in your PATH
2. **Python version issues**: Ensure you have Python 3.10+ installed
3. **Virtual environment issues**: Try `poetry env remove python` and `poetry install`

### Performance Testing

When making performance-related changes:

1. **Benchmark before and after** your changes
2. **Test with large repositories** to ensure scalability
3. **Profile your code** to identify bottlenecks
4. **Consider memory usage** as well as execution time

Thank you for contributing to GitInspector! 🎉
