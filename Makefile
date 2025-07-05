.PHONY: help install install-dev test lint format clean build publish docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install the package in development mode
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-fast: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linting checks
	flake8 .
	black --check --diff .
	mypy .

format: ## Format code with black and isort
	black .
	isort .

clean: ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	python -m build

publish: ## Publish to PyPI (requires twine)
	twine upload dist/*

docs: ## Generate documentation
	# Add documentation generation commands here
	@echo "Documentation generation not yet implemented"

install-playwright: ## Install Playwright browsers
	playwright install

run-example: ## Run the example script
	python examples/basic_usage.py

check-all: ## Run all checks (lint, test, format)
	make lint
	make test
	make format

setup: ## Complete setup for development
	make install-dev
	make install-playwright
	@echo "Setup complete! You can now run 'make run-example' to test the analyzer." 