.PHONY: help setup install install-dev test lint format clean run

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Self-Correcting Technical Architect$(NC)"
	@echo "$(BLUE)Available Commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

setup: ## Initialize the development environment
	@echo "$(BLUE)Setting up environment...$(NC)"
	@bash setup.sh

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@pip install -r requirements.txt

install-dev: ## Install dependencies including dev tools
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	@pip install -r requirements.txt
	@pip install pytest pytest-asyncio pytest-cov black pylint mypy

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	@pytest tests/ -v --cov=src

test-quick: ## Run tests without coverage
	@echo "$(BLUE)Running quick tests...$(NC)"
	@pytest tests/ -v

lint: ## Lint the code
	@echo "$(BLUE)Linting code...$(NC)"
	@pylint src/ --disable=W0212,C0111
	@mypy src/ --ignore-missing-imports

format: ## Format code with Black
	@echo "$(BLUE)Formatting code...$(NC)"
	@black src/ tests/

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code format...$(NC)"
	@black --check src/ tests/

clean: ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(NC)"

run: ## Run the agent (requires API keys in .env)
	@echo "$(BLUE)Starting agent...$(NC)"
	@python -m src.main

run-example: ## Run with example task
	@echo "$(BLUE)Running example task...$(NC)"
	@python -c "import asyncio; from src.main import run_agent; asyncio.run(run_agent('Write a Python function that calculates factorial', 'Function should accept n as parameter, return factorial of n, handle edge cases'))"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	@python3 -m venv venv
	@echo "$(GREEN)Virtual environment created. Activate with: source venv/bin/activate$(NC)"

activate: ## Instructions for activating venv
	@echo "$(BLUE)To activate the virtual environment, run:$(NC)"
	@echo "  source venv/bin/activate"

env: ## Create .env file from template
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "$(GREEN).env file created from template$(NC)"; \
		echo "$(YELLOW)⚠️  Update .env with your API keys$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

check: format-check lint ## Run all checks (format, lint)

all: clean install-dev test lint ## Run all checks and tests

.PHONY: venv activate env
