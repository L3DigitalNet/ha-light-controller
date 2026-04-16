.PHONY: help verify test test-cov lint lint-fix format type-check quality clean install setup

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Use uv run to invoke tools from the managed venv
RUN := uv run

help: ## Show this help message
	@echo "$(BLUE)HA Light Controller - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup          # Initial project setup"
	@echo "  make quality        # Run all quality checks"
	@echo "  make test-cov       # Run tests with coverage report"

verify: ## Verify development environment
	@echo "$(BLUE)Verifying development environment...$(NC)"
	@$(RUN) python scripts/verify_environment.py

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(RUN) pytest tests/ -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(RUN) pytest tests/ \
		--cov=custom_components \
		--cov-report=html \
		--cov-report=term-missing \
		-v
	@echo "$(GREEN)Coverage report generated: htmlcov/index.html$(NC)"

test-specific: ## Run specific test file (usage: make test-specific FILE=tests/test_config_flow.py)
	@echo "$(BLUE)Running specific test: $(FILE)...$(NC)"
	@$(RUN) pytest $(FILE) -v

lint: ## Run Ruff linter
	@echo "$(BLUE)Running Ruff linter...$(NC)"
	@$(RUN) ruff check custom_components/ tests/ scripts/

lint-fix: ## Run Ruff linter with auto-fix
	@echo "$(BLUE)Running Ruff linter with auto-fix...$(NC)"
	@$(RUN) ruff check custom_components/ tests/ scripts/ --fix

format: ## Format code with Ruff
	@echo "$(BLUE)Formatting code with Ruff...$(NC)"
	@$(RUN) ruff format custom_components/ tests/ scripts/

type-check: ## Run mypy type checker
	@echo "$(BLUE)Running mypy type checker...$(NC)"
	@$(RUN) mypy custom_components/

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	@$(RUN) pre-commit run --all-files

quality: lint-fix format type-check test ## Run all quality checks (lint, format, type-check, test)
	@echo "$(GREEN)All quality checks completed!$(NC)"

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf coverage.xml
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Cleanup complete!$(NC)"

install: ## Install dependencies from lockfile
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@uv sync --locked --group dev
	@echo "$(GREEN)Dependencies installed!$(NC)"

setup: install ## Initial project setup (install + pre-commit hooks)
	@echo "$(BLUE)Setting up pre-commit hooks...$(NC)"
	@$(RUN) pre-commit install
	@echo "$(GREEN)Project setup complete!$(NC)"
	@echo "$(YELLOW)Run 'make verify' to check your environment$(NC)"

coverage-report: ## Open HTML coverage report in browser
	@if [ ! -f htmlcov/index.html ]; then \
		echo "$(RED)Coverage report not found. Run 'make test-cov' first.$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "$(YELLOW)Please open htmlcov/index.html manually$(NC)"

ci: ## Simulate CI checks locally
	@echo "$(BLUE)Running CI checks locally...$(NC)"
	@echo ""
	@echo "$(BLUE)[0/5] Version check...$(NC)"
	@$(RUN) python scripts/check_versions.py || (echo "$(RED)Version check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Version check passed$(NC)"
	@echo ""
	@echo "$(BLUE)[1/5] Linting...$(NC)"
	@$(RUN) ruff check custom_components/ tests/ scripts/ || (echo "$(RED)Linting failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Linting passed$(NC)"
	@echo ""
	@echo "$(BLUE)[2/5] Format check...$(NC)"
	@$(RUN) ruff format --check custom_components/ tests/ scripts/ || (echo "$(RED)Format check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Format check passed$(NC)"
	@echo ""
	@echo "$(BLUE)[3/5] Type checking...$(NC)"
	@$(RUN) mypy custom_components/ || (echo "$(RED)Type check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Type check passed$(NC)"
	@echo ""
	@echo "$(BLUE)[4/5] Tests...$(NC)"
	@$(RUN) pytest tests/ -v || (echo "$(RED)Tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ All tests passed$(NC)"
	@echo ""
	@echo "$(GREEN)All CI checks passed! ✓$(NC)"

watch-test: ## Watch for file changes and run tests automatically (requires entr)
	@command -v entr >/dev/null 2>&1 || (echo "$(RED)Error: entr not installed. Install with: sudo apt install entr$(NC)" && exit 1)
	@echo "$(BLUE)Watching for file changes... (Ctrl+C to stop)$(NC)"
	@find custom_components tests -name "*.py" | entr -c $(RUN) pytest tests/ -v

info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "  Python version:        $$(python --version 2>&1)"
	@echo "  Home Assistant:        $$($(RUN) pip show homeassistant 2>/dev/null | grep Version | cut -d' ' -f2 || echo 'Not installed')"
	@echo "  Ruff:                  $$($(RUN) ruff --version 2>/dev/null || echo 'Not installed')"
	@echo "  mypy:                  $$($(RUN) mypy --version 2>/dev/null || echo 'Not installed')"
	@echo "  pytest:                $$($(RUN) pytest --version 2>/dev/null | head -1 || echo 'Not installed')"
	@echo "  Virtual environment:   $$([ -n "$$VIRTUAL_ENV" ] && echo "$$VIRTUAL_ENV" || echo 'Not activated')"
