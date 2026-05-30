# API Reference

All services expose REST APIs under `/api/v1/`. Nginx routes external requests.

## Market Data Service (Port 8001)

### GET /api/v1/health
Returns service health status.

### GET /api/v1/market/symbols
List all tracked symbols. `?active_only=true`

### GET /api/v1/market/symbols/{ticker}
Get symbol details by ticker.

### GET /api/v1/market/quotes/{ticker}
Get real-time quote for a symbol.

### GET /api/v1/market/quotes?tickers=AAPL,SPY
Get quotes for multiple symbols.

### GET /api/v1/market/historical/{ticker}
Get historical OHLCV bars.

Parameters: `timeframe`, `start`, `end`, `limit`, `refresh`

---

## Strategy Engine (Port 8002)

### GET /api/v1/health

### GET /api/v1/strategy/available
List available strategy names.

### POST /api/v1/strategy/signals/generate
Generate signals for a ticker.

Body: `{ "ticker": "AAPL", "timeframe": "1h" }`

### POST /api/v1/strategy/backtest
Run backtest for a strategy.

Body: `{ "strategy_id": "uuid", "ticker": "AAPL", "timeframe": "1h", "start": "2024-01-01", "end": "2024-06-01", "initial_capital": 100000 }`

---

## Risk Management Service (Port 8003)

### GET /api/v1/health

### POST /api/v1/risk/position-size
Calculate position size.

Body:
```json
{
  "ticker": "AAPL",
  "entry_price": 150.0,
  "stop_loss": 145.0,
  "account_equity": 100000,
  "risk_per_trade_pct": 0.01,
  "method": "fixed_fractional"
}
```

### POST /api/v1/risk/check
Check if trade meets risk criteria.

Body: `{ "account_equity": 100000, "daily_pnl": -500, "current_drawdown_pct": 0.05, "open_positions": 3, "proposed_position_pct": 0.02 }`

### GET /api/v1/risk/drawdown/{equity}
Get drawdown status for current equity level.

### POST /api/v1/risk/circuit-breaker/activate
Activate circuit breaker. Query param: `reason`

### POST /api/v1/risk/circuit-breaker/deactivate
Deactivate circuit breaker.

### GET /api/v1/risk/circuit-breaker/status
Get circuit breaker status.

---

## Execution Engine (Port 8004)

### GET /api/v1/health

### POST /api/v1/orders/place
Place a new order.

Body:
```json
{
  "ticker": "AAPL",
  "order_type": "market",
  "side": "buy",
  "quantity": 10.0,
  "time_in_force": "day"
}
```

### DELETE /api/v1/orders/{external_order_id}
Cancel an open order.

---

## AI Agent Service (Port 8005)

### GET /api/v1/health

### POST /api/v1/agent/cycle/run
Run a full multi-agent trading cycle.

Body:
```json
{
  "tickers": ["AAPL", "SPY", "QQQ"],
  "account_equity": 100000,
  "execute_trades": false
}
```

### POST /api/v1/agent/analyze
Run market analysis only.

Body: `{ "tickers": ["AAPL"], "account_equity": 100000 }`

### POST /api/v1/agent/performance/review
Run performance review.

Body: `{ "trade_history": [...], "time_period": "last 7 days" }`

---

## Monitoring Service (Port 8006)

### GET /api/v1/health

### POST /api/v1/metrics-data/record
Record a performance metric.

Body: `{ "metric_name": "portfolio_value", "metric_value": 102500, "dimensions": {} }`

### GET /api/v1/metrics-data/summary
Get recent metrics summary.

### GET /api/v1/alerts
List alerts. `?unacknowledged_only=true`

### POST /api/v1/alerts
Create a new alert.

Body: `{ "alert_type": "risk_limit", "severity": "warning", "message": "...", "metadata": {} }`

### POST /api/v1/alerts/{id}/acknowledge
Acknowledge an alert.
