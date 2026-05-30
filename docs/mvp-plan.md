# MVP Plan

## MVP Definition

The MVP is a fully functional paper trading system that:
1. Fetches real-time market data from Alpaca (paper account)
2. Generates signals using SMC and MA Crossover strategies
3. Applies risk management (1% risk per trade, 3% daily loss limit)
4. Uses Claude AI to make final trade decisions
5. Executes paper trades via Alpaca
6. Displays results in real-time dashboard

## MVP Scope (4 weeks)

### Week 1: Infrastructure
- [x] Docker Compose with all services
- [x] PostgreSQL schema initialized
- [x] Redis configured
- [x] Nginx routing

### Week 2: Core Services
- [x] Market Data: Alpaca quotes + historical bars
- [x] Strategy Engine: Order Block + MA Crossover signals
- [x] Risk Management: Fixed fractional sizing + circuit breakers

### Week 3: AI Agent
- [x] Claude API integration with prompt caching
- [x] Market Analyst agent (analyze conditions)
- [x] Risk Manager agent (validate trades)
- [x] Trade Executor agent (place orders)
- [x] Orchestrator (coordinate all agents)

### Week 4: Frontend + Polish
- [x] Dashboard with candlestick charts
- [x] Portfolio view (positions, P&L)
- [x] Trade history table
- [x] Risk dashboard (drawdown, circuit breaker)
- [x] Real-time data via polling

## MVP Success Criteria

1. **Functional**: Can run a complete trading cycle (analyze → decide → execute)
2. **Safe**: Never exceeds daily loss limit, circuit breaker works
3. **Observable**: All metrics visible in Grafana
4. **Reliable**: Services recover from crashes, DB persists state
5. **Paper Only**: Only connects to Alpaca paper account

## MVP Non-Scope

- Live trading (paper only)
- Mobile app
- Multiple broker support
- Options trading
- Advanced backtesting UI
- User authentication/multi-user

## Quick Start for MVP

```bash
# 1. Configure
cp .env.example .env
# Add ANTHROPIC_API_KEY and ALPACA paper trading keys

# 2. Start
docker-compose up -d

# 3. Verify
curl http://localhost:8001/api/v1/health
curl http://localhost:8005/api/v1/health

# 4. Run first AI cycle
curl -X POST http://localhost:8005/api/v1/agent/cycle/run \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "SPY"], "account_equity": 100000, "execute_trades": false}'

# 5. Open dashboard
open http://localhost:3000
```
