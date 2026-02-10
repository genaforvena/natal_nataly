# CI/CD Pipeline and Testing Guide

This document explains the CI/CD pipeline and testing infrastructure for the natal_nataly bot.

## Overview

The project now includes:
- **Automated testing** with pytest
- **Linting** with flake8
- **Type checking** with mypy
- **CI/CD pipeline** with GitHub Actions
- **Code coverage** reporting

## Running Tests Locally

### Prerequisites

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

### Running All Tests

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN=test_token
export LLM_PROVIDER=groq
export GROQ_API_KEY=test_key

# Run all tests
pytest tests/ -v
```

### Running Specific Test Suites

```bash
# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration

# Run a specific test file
pytest tests/test_chart_builder.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Organization

Tests are organized by module:

- **`tests/test_chart_builder.py`** - Tests for natal chart generation
  - Chart text export formatting
  - JSON structure generation
  - Timezone handling
  - Coordinate validation

- **`tests/test_llm.py`** - Tests for LLM integration
  - Prompt loading and variable substitution
  - API call mocking
  - Response parsing

- **`tests/test_bot.py`** - Tests for bot message handling
  - Message splitting for Telegram limits
  - Text parsing
  - State management

- **`tests/test_integration.py`** - Integration tests
  - Telegram webhook handling
  - API error handling
  - Database operations

## Linting and Type Checking

### Running Flake8

```bash
# Check all files
flake8 .

# Check with statistics
flake8 . --count --statistics

# Check specific file
flake8 main.py
```

### Running Mypy

```bash
# Type check all files
mypy . --config-file mypy.ini

# Check specific file
mypy main.py
```

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on:
- Pull requests to `main` or `development` branches
- Pushes to `main` or `development` branches

### Pipeline Jobs

1. **Lint** - Runs flake8 to check code style
2. **Type Check** - Runs mypy for type checking (advisory)
3. **Test** - Runs all tests with coverage reporting
4. **Docker Build** - Verifies Docker image builds successfully
5. **Security Scan** - Runs safety check for dependency vulnerabilities

### Pipeline Failure Behavior

- **Lint failures** block merging
- **Type check failures** are advisory (do not block)
- **Test failures** block merging
- **Docker build failures** block merging

### Viewing CI Results

1. Go to the GitHub repository
2. Click on "Actions" tab
3. Select the workflow run to view details
4. Click on individual jobs to see logs

### Coverage Reports

Coverage reports are:
- Uploaded to Codecov (if configured)
- Stored as artifacts in GitHub Actions (viewable for 30 days)
- Generated as HTML reports in the `htmlcov/` directory

## Adding New Tests

### Unit Test Template

```python
import pytest
from your_module import your_function

@pytest.mark.unit
class TestYourFeature:
    def test_basic_functionality(self):
        """Test basic functionality."""
        result = your_function(param="value")
        assert result == expected_value
```

### Integration Test Template

```python
import pytest
from unittest.mock import patch, Mock

@pytest.mark.integration
class TestYourIntegration:
    @pytest.mark.asyncio
    async def test_api_integration(self):
        """Test API integration."""
        # Your test code here
        pass
```

### Mocking External Services

Use `pytest-httpx` for mocking HTTP requests:

```python
from pytest_httpx import HTTPXMock

@pytest.mark.asyncio
async def test_api_call(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"status": "ok"})
    # Your test code here
```

Use `unittest.mock` for mocking other dependencies:

```python
from unittest.mock import patch, Mock

@patch('module.function')
def test_with_mock(mock_function):
    mock_function.return_value = "mocked value"
    # Your test code here
```

## Configuration Files

### pytest.ini
Configures pytest behavior:
- Test discovery patterns
- Markers for test categorization
- Output formatting

### .flake8
Configures flake8 linting:
- Line length limits
- Ignored error codes
- Excluded directories

### mypy.ini
Configures mypy type checking:
- Python version
- Strictness level
- Excluded directories

## Continuous Improvement

### Adding New Checks

To add new checks to the pipeline:

1. Edit `.github/workflows/ci.yml`
2. Add a new job or step
3. Test locally first
4. Commit and push changes

### Updating Dependencies

When adding new test dependencies:

1. Add to `requirements-dev.txt`
2. Update the workflow if needed
3. Test locally to ensure compatibility

### Test Coverage Goals

- Aim for >80% code coverage
- Focus on critical business logic
- Test edge cases and error handling
- Mock external dependencies

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Check Python version (CI uses 3.12)
- Verify all dependencies are installed
- Check environment variables

### Tests Pass Locally But Fail in CI

- Review CI logs for error messages
- Check for missing environment variables
- Verify ephemeris directory exists

### Flake8 Errors

- Run `flake8 .` to see all issues
- Fix or ignore specific errors in `.flake8`
- Consider using `# noqa` comments for one-off ignores

### Coverage Too Low

- Identify untested modules with `--cov-report=term-missing`
- Add tests for critical paths first
- Consider integration tests for complex workflows

## Best Practices

1. **Write tests before fixing bugs** - Test-driven debugging
2. **Keep tests independent** - Tests should not depend on each other
3. **Use descriptive test names** - Name should describe what's being tested
4. **Mock external dependencies** - Tests should be fast and reliable
5. **Test edge cases** - Test boundary conditions and error states
6. **Keep tests simple** - One concept per test
7. **Run tests before committing** - Catch issues early

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [mypy documentation](https://mypy.readthedocs.io/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
