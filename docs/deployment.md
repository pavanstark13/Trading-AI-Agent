# Deployment Guide

## Prerequisites

- Docker 24.x+
- Docker Compose 2.x+
- Git
- At minimum: 4 CPU cores, 8GB RAM

## Development Setup

### 1. Clone and configure

```bash
git clone https://github.com/your-org/trading-ai-agent.git
cd trading-ai-agent

# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Required environment variables

```bash
# .env - minimum required
ANTHROPIC_API_KEY=sk-ant-...
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Start development environment

```bash
# Start all services
docker-compose up --build

# Or start specific services
docker-compose up postgres redis market-data strategy-engine

# View logs
docker-compose logs -f ai-agent

# Run in background
docker-compose up -d
```

### 4. Verify services

```bash
curl http://localhost:8001/api/v1/health  # Market Data
curl http://localhost:8002/api/v1/health  # Strategy Engine
curl http://localhost:8003/api/v1/health  # Risk Management
curl http://localhost:8004/api/v1/health  # Execution Engine
curl http://localhost:8005/api/v1/health  # AI Agent
curl http://localhost:8006/api/v1/health  # Monitoring

# Frontend
open http://localhost:3000

# Grafana
open http://localhost:3001  # admin/admin_pass
```

## Makefile Commands

```bash
make help       # Show all commands
make dev        # Start development environment
make build      # Build all Docker images
make test       # Run all tests
make lint       # Run linters
make clean      # Remove containers and volumes
make logs       # Follow all service logs
```

## Staging Deployment

Staging is deployed automatically on push to `main` via GitHub Actions.

Requirements:
- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY` secrets in GitHub
- `docker-compose.prod.yml` on the staging server

Manual staging deployment:
```bash
# On staging server
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Production Deployment

Production is deployed on GitHub Release publication.

### Production environment variables

All secrets should be stored in a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.):

```bash
ANTHROPIC_API_KEY=<production key>
ALPACA_API_KEY=<live trading key>
ALPACA_SECRET_KEY=<live trading secret>
ALPACA_BASE_URL=https://api.alpaca.markets  # Live trading!
SECRET_KEY=<strong random 64-char key>
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
ENVIRONMENT=production
DEBUG=false
```

### Production docker-compose

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Differences from dev:
- Multi-replica services for HA
- Resource limits
- No port exposure (only via Nginx)
- Production logging configuration

## Monitoring Setup

### Prometheus
Automatically scrapes all services at `/metrics`.
Access: http://localhost:9090

### Grafana
Pre-configured with:
- Trading dashboard (portfolio value, P&L, drawdown)
- Service health dashboard
- API latency dashboard

Access: http://localhost:3001 (default: admin/admin_pass)

## Database Migrations

The database schema is initialized from `infra/postgres/init.sql` on first startup.

For schema changes in production, use Alembic:
```bash
# Generate migration
alembic revision --autogenerate -m "add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Service won't start
```bash
docker-compose logs <service-name>
docker-compose ps
```

### Database connection errors
```bash
# Verify postgres is running
docker-compose exec postgres pg_isready -U trader

# Check database
docker-compose exec postgres psql -U trader -d trading_db -c "SELECT count(*) FROM symbols;"
```

### Redis connection errors
```bash
docker-compose exec redis redis-cli ping
```

### AI Agent not responding
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check rate limits in Anthropic console
- View logs: `docker-compose logs ai-agent`
