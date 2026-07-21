.PHONY: dev test lint format build deploy help

# ════════════════════════════════════════════════════════════
# FinGuard AI Makefile
# ════════════════════════════════════════════════════════════

help: ## Show this help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment using docker-compose
	docker-compose up -d
	@echo "Services started natively. Head to http://localhost:5173"

test: ## Run backend unit and integration tests
	pytest tests/ -v --cov=backend --cov-report=term-missing

lint: ## Run pre-commit checks and ruff
	pre-commit run --all-files

format: ## Format codebase using black and ruff
	black backend tests src
	ruff check backend tests src --fix

build: ## Build docker images locally
	docker-compose build

deploy: ## Deploy to production environment (Mock/CI)
	docker-compose -f docker-compose.prod.yml up -d
