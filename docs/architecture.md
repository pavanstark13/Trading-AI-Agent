# System Architecture

## Overview

The AI Trading Agent Platform is a production-grade microservices architecture that combines algorithmic trading strategies with multi-agent AI decision-making powered by Claude.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI TRADING AGENT PLATFORM                      │
├─────────────────────────────────────────────────────────────────┤
│  FRONTEND (React/TypeScript)                                      │
│  Dashboard | Portfolio | Trades | Analytics | Risk               │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/WebSocket
                       ▼
              ┌────────────────┐
              │   Nginx (80)   │
              │  Reverse Proxy │
              └────────┬───────┘
         ┌─────────────┼─────────────────────────────┐
         ▼             ▼             ▼                ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐   ┌──────────┐
   │ Market   │  │Strategy  │  │   Risk   │   │Execution │
   │ Data     │  │ Engine   │  │  Mgmt    │   │ Engine   │
   │ :8001    │  │  :8002   │  │  :8003   │   │  :8004   │
   └────┬─────┘  └────┬─────┘  └────┬─────┘   └────┬─────┘
        │              │              │               │
        └──────────────┴──────────────┴───────────────┘
                                │
                     ┌──────────▼──────────┐
                     │    AI Agent :8005    │
                     │  ┌────────────────┐ │
                     │  │  Orchestrator  │ │
                     │  ├────────────────┤ │
                     │  │Market Analyst  │ │
                     │  │Risk Manager    │ │
                     │  │Trade Executor  │ │
                     │  │Perf Reviewer   │ │
                     │  └────────────────┘ │
                     └──────────┬──────────┘
                                │ Anthropic API
                                ▼
                         ┌─────────────┐
                         │ Claude API  │
                         │(claude-     │
                         │sonnet-4-6)  │
                         └─────────────┘
        ┌───────────────────────────────────────┐
        │          Data Layer                    │
        │  ┌──────────────┐  ┌───────────────┐  │
        │  │  PostgreSQL  │  │     Redis     │  │
        │  │   :5432      │  │    :6379      │  │
        │  └──────────────┘  └───────────────┘  │
        └───────────────────────────────────────┘
        ┌───────────────────────────────────────┐
        │        Observability                   │
        │  ┌───────────┐  ┌──────────────────┐  │
        │  │Prometheus │  │    Grafana       │  │
        │  │  :9090    │  │     :3001        │  │
        │  └───────────┘  └──────────────────┘  │
        └───────────────────────────────────────┘
```

## Services

### Market Data Service (Port 8001)
Fetches and caches OHLCV bars, real-time quotes, and market snapshots.

- **Adapters**: Alpaca Markets API (extensible to other brokers)
- **Endpoints**: `/symbols`, `/quotes/{ticker}`, `/historical/{ticker}`
- **Caching**: Redis caching for quotes (5s TTL), historical bars (1h TTL)
- **WebSocket**: Real-time price streaming

### Strategy Engine (Port 8002)
Implements and runs trading strategies to generate signals.

- **SMC Strategies**: Order Blocks, Fair Value Gaps, Market Structure (BOS/CHoCH)
- **Rule-Based**: Moving Average Crossover, RSI Mean Reversion
- **Signal Aggregation**: Multi-strategy confluence scoring
- **Backtesting**: Walk-forward simulation engine

### Risk Management Service (Port 8003)
Enforces risk controls and position sizing.

- **Position Sizing**: Fixed Fractional, Kelly Criterion
- **Circuit Breakers**: Daily loss limit, max drawdown halt
- **Drawdown Monitoring**: Real-time equity tracking
- **Limits**: Max positions, position size, daily loss

### Execution Engine (Port 8004)
Handles order lifecycle from placement to fill.

- **Adapters**: Alpaca execution (paper + live)
- **Order Types**: Market, Limit, Stop, Stop-Limit
- **Trade Logging**: All executions persisted to DB
- **Position Tracking**: Real-time position P&L

### AI Agent Service (Port 8005)
Multi-agent AI system powered by Claude.

- **Orchestrator**: Coordinates full trading pipeline
- **Market Analyst**: Identifies opportunities using tools
- **Risk Manager**: Validates trades against risk parameters
- **Trade Executor**: Places orders with optimal timing
- **Performance Reviewer**: Analyzes P&L and suggests improvements
- **Prompt Caching**: System prompts cached for efficiency

### Monitoring Service (Port 8006)
Aggregates metrics, manages alerts, and tracks performance.

- **Prometheus Metrics**: All services expose `/metrics`
- **Grafana Dashboard**: Pre-configured trading dashboard
- **Alert Management**: Create, acknowledge, and query alerts

## Data Flow

### Trading Cycle

```
1. Market Data Service fetches OHLCV from Alpaca
   └─> Persists to PostgreSQL
   └─> Caches in Redis

2. Strategy Engine reads cached data
   └─> Runs SMC + Rule-Based strategies
   └─> Generates signals with strength scores

3. AI Agent Orchestrator runs cycle:
   a. Market Analyst calls strategy-engine tools
   b. Risk Manager validates signals, calculates sizes
   c. Trade Executor places approved orders

4. Execution Engine receives orders
   └─> Routes to Alpaca adapter
   └─> Logs trades to PostgreSQL

5. Monitoring Service records metrics
   └─> Prometheus scrapes all services
   └─> Grafana visualizes in real-time
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, asyncio |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| Broker | Alpaca Markets API (alpaca-py) |
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| Charts | lightweight-charts, recharts |
| State | Redux Toolkit |
| Proxy | Nginx 1.25 |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Containers | Docker + Docker Compose |
