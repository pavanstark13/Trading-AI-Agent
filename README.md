# AI Trading Agent Platform

A production-grade algorithmic trading platform powered by multi-agent AI (Anthropic Claude), Smart Money Concepts (SMC), and a microservices architecture.

## Architecture

```
Frontend (React) → Nginx → 6 Microservices → PostgreSQL + Redis
                                 ↓
                         AI Agent (Claude claude-sonnet-4-6)
                         Multi-agent: Analyst + Risk + Executor + Reviewer
```

See [docs/architecture.md](docs/architecture.md) for the full ASCII diagram.

## Services

| Service | Port | Description |
|---------|------|-------------|
| Market Data | 8001 | OHLCV bars, real-time quotes (Alpaca) |
| Strategy Engine | 8002 | SMC + rule-based signal generation |
| Risk Management | 8003 | Position sizing, circuit breakers |
| Execution Engine | 8004 | Order placement (Alpaca) |
| AI Agent | 8005 | Multi-agent Claude AI orchestration |
| Monitoring | 8006 | Metrics, alerts |
| Frontend | 3000 | React dashboard |
| Prometheus | 9090 | Metrics scraping |
| Grafana | 3001 | Visualization |

## Quick Start

```bash
# 1. Clone and configure
git clone <repo>
cd Trading-AI-Agent
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and ALPACA keys

# 2. Start everything
docker-compose up --build

# 3. Open dashboard
open http://localhost:3000

# 4. Run an AI trading cycle
curl -X POST http://localhost:8005/api/v1/agent/cycle/run \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "SPY"], "account_equity": 100000, "execute_trades": false}'
```

## Key Features

### Smart Money Concepts (SMC)
- **Order Block Detection**: Identifies institutional order blocks from swing displacements
- **Fair Value Gaps**: Detects price imbalances between candles
- **Market Structure**: BOS (Break of Structure) and CHoCH (Change of Character)

### Multi-Agent AI (Claude)
- **Orchestrator**: Coordinates the full trading pipeline
- **Market Analyst**: Analyzes conditions using real market tools
- **Risk Manager**: Validates every trade against risk limits
- **Trade Executor**: Places orders with optimal timing
- **Performance Reviewer**: Analyzes P&L and recommends improvements

All agents use **prompt caching** (`cache_control: {"type": "ephemeral"}`) for efficiency.

### Risk Management
- **Position Sizing**: Fixed Fractional and Kelly Criterion
- **Circuit Breakers**: Daily loss limit (3%), max drawdown (15%)
- **Real-time Monitoring**: Equity curve tracking, drawdown alerts

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov

# Lint
ruff check .
ruff format .

# Docker build specific service
docker-compose build market-data
```

## Environment Variables

See [.env.example](.env.example) for all configuration options.

Required:
- `ANTHROPIC_API_KEY` - Anthropic API key
- `ALPACA_API_KEY` + `ALPACA_SECRET_KEY` - Alpaca Markets credentials
- `SECRET_KEY` - JWT secret (generate with `openssl rand -hex 32`)

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api-spec.md)
- [Database Schema](docs/database-schema.md)
- [Deployment Guide](docs/deployment.md)
- [Development Roadmap](docs/development-roadmap.md)
- [MVP Plan](docs/mvp-plan.md)

## Safety

This platform defaults to **paper trading** (Alpaca paper endpoint). To enable live trading:
1. Change `ALPACA_BASE_URL` to `https://api.alpaca.markets`
2. Use live Alpaca API credentials
3. Thoroughly backtest strategies first

**Never risk capital you cannot afford to lose.**
