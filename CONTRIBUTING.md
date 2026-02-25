# Contributing to OpenSEO

Thank you for your interest in contributing to OpenSEO!

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Redis (for Celery)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
playwright install chromium
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Running Tests

### Backend Tests
```bash
cd backend
pytest                    # Run all tests
pytest tests/unit        # Run unit tests only
pytest tests/integration # Run integration tests only
pytest --cov            # Run with coverage
```

### Frontend Tests
```bash
cd frontend
npm test                # Run in watch mode
npm run coverage        # Run with coverage report
```

### All Tests (Docker)
```bash
docker-compose -f docker-compose.test.yml up --build
```

## Code Style

### Python
- Follow PEP 8
- Use black for formatting: `black .`
- Use isort for imports: `isort .`
- Max line length: 127 characters

### TypeScript/React
- Use TypeScript strict mode
- Follow ESLint configuration
- Use Prettier for formatting

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## CI/CD

All pull requests trigger:
- Backend unit tests
- Frontend unit tests
- Docker build tests
- Linting and type checking
- Security scans

## Reporting Issues

When reporting issues, please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python/Node versions)
- Relevant logs or error messages

## License

By contributing, you agree that your contributions will be licensed under the MIT License.