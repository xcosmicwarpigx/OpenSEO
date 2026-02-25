# Testing

This directory contains all tests for the OpenSEO backend.

## Structure

```
tests/
├── unit/           # Unit tests for individual functions
│   ├── test_content_analyzer.py
│   ├── test_security_analyzer.py
│   └── test_accessibility_analyzer.py
└── integration/    # Integration tests for API endpoints
    ├── test_api.py
    └── test_models.py
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run unit tests only
```bash
pytest tests/unit -v
```

### Run integration tests only
```bash
pytest tests/integration -v
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html --cov-report=xml
```

### Run specific test file
```bash
pytest tests/unit/test_content_analyzer.py -v
```

## Test Coverage

Current test coverage targets:
- Unit tests: 80%+ coverage
- Integration tests: API endpoint validation

View coverage report:
```bash
open htmlcov/index.html
```

## Writing Tests

### Unit Test Example
```python
def test_calculate_readability():
    text = "The cat sat on the mat."
    result = calculate_readability(text)
    assert result.word_count == 6
    assert result.flesch_reading_ease is not None
```

### Integration Test Example
```python
def test_crawl_endpoint():
    response = client.post("/api/crawl", json={
        "url": "https://example.com",
        "max_pages": 10
    })
    assert response.status_code == 200
    assert "task_id" in response.json()
```

## Continuous Integration

Tests are automatically run on:
- Push to `main`, `master`, `develop` branches
- Push to `feature/*` branches
- Pull requests to `main`, `master`, `develop`

See `.github/workflows/ci.yml` for CI configuration.