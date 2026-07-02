.PHONY: setup lint test benchmark docs docker demo clean install dev help

help:
	@echo "NCP Monorepo - Available Commands"
	@echo "=================================="
	@echo "  make setup      - Install dependencies"
	@echo "  make lint       - Run linters (ruff, mypy)"
	@echo "  make format     - Format code (black)"
	@echo "  make test       - Run test suite"
	@echo "  make benchmark  - Run benchmarks"
	@echo "  make docs       - Build documentation"
	@echo "  make docker     - Build Docker image"
	@echo "  make demo       - Run demo"
	@echo "  make clean      - Clean build artifacts"

setup:
	pip install -e ".[all]"

lint:
	ruff check ncp tests
	mypy ncp --ignore-missing-imports

format:
	black ncp tests
	ruff check --fix ncp tests

test:
	pytest tests/ -v --tb=short

benchmark:
	pytest benchmarks/ -v

docs:
	@echo "Building documentation..."
	mkdir -p docs/api
	python -m pydoc -w ncp || true

docker:
	docker-compose build

demo:
	python -m ncp.cli.main --demo

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
