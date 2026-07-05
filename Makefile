# ============================================================
# DOWNLOADER ULTIMATE — Makefile
# Usage: make <target>
# ============================================================

.PHONY: help dev dev-build test lint format clean build push logs

# Default target
help: ## Show available commands
	@echo "\nDownloader Ultimate — Available Commands:"
	@echo "=========================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- Development ---
dev: ## Start all services in development mode
	docker compose up --build

dev-d: ## Start all services in background
	docker compose up --build -d

dev-stop: ## Stop all services
	docker compose down

dev-clean: ## Stop all services and remove volumes
	docker compose down -v --remove-orphans

# --- Testing ---
test: ## Run all tests with coverage
	cd backend && poetry run pytest --cov=app --cov-report=term-missing -v

test-unit: ## Run only unit tests
	cd backend && poetry run pytest tests/unit/ -v

test-integration: ## Run only integration tests
	cd backend && poetry run pytest tests/integration/ -v

test-load: ## Run load tests with Locust
	cd backend && poetry run locust -f tests/load/locustfile.py --headless -u 10 -r 2 --run-time 60s

# --- Code Quality ---
lint: ## Run linting (flake8)
	cd backend && poetry run flake8 .

format: ## Format code (black + isort)
	cd backend && poetry run black . && poetry run isort .

format-check: ## Check code formatting without changing files
	cd backend && poetry run black --check . && poetry run isort --check-only .

# --- Docker ---
build: ## Build Docker images
	docker compose build

build-prod: ## Build production Docker images
	docker compose -f docker-compose.yml build

push: ## Push Docker images to registry
	docker compose push

# --- Logs ---
logs: ## Tail logs from all services
	docker compose logs -f

logs-api: ## Tail logs from API service
	docker compose logs -f api

logs-worker: ## Tail logs from worker
	docker compose logs -f worker

# --- Setup ---
install: ## Install Python dependencies via Poetry
	cd backend && poetry install --with dev

install-hooks: ## Install pre-commit hooks
	cd backend && poetry run pre-commit install

# --- Cleanup ---
clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	find . -type f -name '*.pyo' -delete 2>/dev/null || true

clean-jobs: ## Remove all job data (CAUTION: deletes processed videos)
	rm -rf /data/jobs/*
