# UPI Pulse - one entry point for every workflow.
# On Windows, run from Git Bash with GNU make installed (see docs/PROGRESS.md).
UV ?= uv
.DEFAULT_GOAL := help

.PHONY: help setup lint format test demo ingest pipeline dbt dq up down destroy

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install deps and git hooks
	$(UV) sync
	$(UV) run pre-commit install

lint: ## Ruff lint + format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## Auto-fix lint and formatting
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

test: ## Unit + integration tests with coverage (>=80%)
	$(UV) run pytest

demo: ## End-to-end run on committed fixtures (Phase 2+)
	@echo "demo: not implemented yet (arrives in Phase 2)"; exit 1

ingest: ## Download/collect source files into landing/ (Phase 1)
	@echo "ingest: not implemented yet (arrives in Phase 1)"; exit 1

pipeline: ## landing -> bronze -> silver in PySpark (Phase 2)
	@echo "pipeline: not implemented yet (arrives in Phase 2)"; exit 1

dbt: ## dbt build of gold marts (Phase 3)
	@echo "dbt: not implemented yet (arrives in Phase 3)"; exit 1

dq: ## Data-quality checkpoints on silver (Phase 3)
	@echo "dq: not implemented yet (arrives in Phase 3)"; exit 1

up: ## Start local Airflow in Docker (Phase 4)
	@echo "up: not implemented yet (arrives in Phase 4)"; exit 1

down: ## Stop local Airflow (Phase 4)
	@echo "down: not implemented yet (arrives in Phase 4)"; exit 1

destroy: ## Tear down Azure resources (Phase 5)
	@echo "destroy: not implemented yet (arrives in Phase 5)"; exit 1
