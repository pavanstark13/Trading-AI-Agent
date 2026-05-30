.PHONY: help build up down logs test lint format migrate seed

DOCKER_COMPOSE = docker-compose
PYTHON = python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ─────────────────────────────────────────────────────────────────────
build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d

up-infra: ## Start only infrastructure (postgres, redis)
	$(DOCKER_COMPOSE) up -d postgres redis

down: ## Stop all services
	$(DOCKER_COMPOSE) down

down-volumes: ## Stop all services and remove volumes
	$(DOCKER_COMPOSE) down -v

logs: ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f

logs-ai: ## Tail AI agent logs
	$(DOCKER_COMPOSE) logs -f ai-agent

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

ps: ## Show running services
	$(DOCKER_COMPOSE) ps

# ── Development ────────────────────────────────────────────────────────────────
install: ## Install Python dev dependencies
	pip install -e ".[dev]"
	cd frontend && npm install

dev-market: ## Run market data service locally
	cd services/market_data && uvicorn main:app --reload --port 8001

dev-strategy: ## Run strategy engine locally
	cd services/strategy_engine && uvicorn main:app --reload --port 8002

dev-risk: ## Run risk management locally
	cd services/risk_management && uvicorn main:app --reload --port 8003

dev-execution: ## Run execution engine locally
	cd services/execution_engine && uvicorn main:app --reload --port 8004

dev-agent: ## Run AI agent locally
	cd services/ai_agent && uvicorn main:app --reload --port 8005

dev-monitoring: ## Run monitoring locally
	cd services/monitoring && uvicorn main:app --reload --port 8006

dev-frontend: ## Run frontend dev server
	cd frontend && npm run dev

# ── Database ───────────────────────────────────────────────────────────────────
db-init: ## Initialize database schema
	$(DOCKER_COMPOSE) exec postgres psql -U trader -d trading_db -f /docker-entrypoint-initdb.d/init.sql

db-shell: ## Open a psql shell
	$(DOCKER_COMPOSE) exec postgres psql -U trader -d trading_db

db-backup: ## Backup database
	$(DOCKER_COMPOSE) exec postgres pg_dump -U trader trading_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

# ── Testing ────────────────────────────────────────────────────────────────────
test: ## Run all tests
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-ci: ## Run tests as in CI
	pytest tests/ --cov=. --cov-report=xml -q

# ── Code Quality ───────────────────────────────────────────────────────────────
lint: ## Run linters
	ruff check .
	mypy shared/ services/ --ignore-missing-imports

format: ## Format code
	ruff format .
	ruff check . --fix

security: ## Run security scan
	bandit -r services/ shared/ -ll

# ── Monitoring ─────────────────────────────────────────────────────────────────
prometheus: ## Open Prometheus UI
	open http://localhost:9090

grafana: ## Open Grafana UI
	open http://localhost:3001

# ── Production ─────────────────────────────────────────────────────────────────
prod-up: ## Start production stack
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down: ## Stop production stack
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## Tail production logs
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml logs -f
