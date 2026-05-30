# Database Schema

All tables use UUID primary keys and PostgreSQL. See `infra/postgres/init.sql` for full DDL.

## Market Data

### symbols
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| ticker | VARCHAR(20) UNIQUE | e.g., AAPL, SPY |
| name | VARCHAR(255) | Full company name |
| exchange | VARCHAR(50) | NASDAQ, NYSE, CRYPTO |
| asset_type | VARCHAR(50) | stock, etf, crypto, forex |
| is_active | BOOLEAN | Default TRUE |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### ohlcv
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| symbol_id | UUID FK → symbols | |
| timeframe | VARCHAR(10) | 1m, 5m, 1h, 1d |
| open/high/low/close | NUMERIC(20,8) | |
| volume | NUMERIC(20,2) | |
| timestamp | TIMESTAMPTZ | Unique with (symbol_id, timeframe) |

### market_snapshots
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| symbol_id | UUID FK | |
| bid/ask/last | NUMERIC(20,8) | |
| volume, bid_size, ask_size | NUMERIC | |
| snapshot_time | TIMESTAMPTZ | |

## Strategy Engine

### strategies
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(100) UNIQUE | |
| type | VARCHAR(50) | smc, rule_based, ml |
| parameters | JSONB | Strategy-specific config |
| is_active | BOOLEAN | |

### signals
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| strategy_id | UUID FK | |
| symbol_id | UUID FK | |
| signal_type | VARCHAR(50) | entry, exit |
| direction | VARCHAR(10) | long, short |
| strength | NUMERIC(5,4) | 0.0 to 1.0 |
| price | NUMERIC(20,8) | |
| stop_loss | NUMERIC(20,8) | |
| take_profit | NUMERIC(20,8) | |
| metadata | JSONB | Additional info |
| is_executed | BOOLEAN | |

## Risk Management

### risk_profiles
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(100) UNIQUE | |
| max_position_size_pct | NUMERIC(5,4) | Default 0.02 (2%) |
| daily_loss_limit_pct | NUMERIC(5,4) | Default 0.05 (5%) |
| max_drawdown_pct | NUMERIC(5,4) | Default 0.15 (15%) |
| risk_per_trade_pct | NUMERIC(5,4) | Default 0.01 (1%) |
| kelly_fraction | NUMERIC(5,4) | Default 0.25 |
| is_active | BOOLEAN | |

### risk_events
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| event_type | VARCHAR(50) | limit_breach, drawdown_alert |
| severity | VARCHAR(20) | info, warning, critical |
| message | TEXT | |
| details | JSONB | |
| acknowledged | BOOLEAN | |

## Execution Engine

### orders
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| external_order_id | VARCHAR(100) UNIQUE | Broker's ID |
| symbol_id | UUID FK | |
| strategy_id | UUID FK | |
| order_type | VARCHAR(20) | market, limit, stop |
| side | VARCHAR(10) | buy, sell |
| quantity | NUMERIC(20,8) | |
| status | VARCHAR(20) | pending, filled, cancelled |
| filled_qty | NUMERIC(20,8) | |
| avg_fill_price | NUMERIC(20,8) | |

### trades
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| order_id | UUID FK | |
| symbol_id | UUID FK | |
| side | VARCHAR(10) | |
| quantity | NUMERIC(20,8) | |
| price | NUMERIC(20,8) | Fill price |
| commission | NUMERIC(20,8) | |
| pnl | NUMERIC(20,8) | Null for opening trades |
| executed_at | TIMESTAMPTZ | |

### positions
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| symbol_id | UUID FK UNIQUE | One position per symbol |
| side | VARCHAR(10) | long, short |
| quantity | NUMERIC(20,8) | |
| avg_entry_price | NUMERIC(20,8) | |
| current_price | NUMERIC(20,8) | Updated in real-time |
| unrealized_pnl | NUMERIC(20,8) | |
| realized_pnl | NUMERIC(20,8) | |

## AI Agent

### agent_sessions
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| agent_type | VARCHAR(50) | orchestrator, market_analyst |
| context | JSONB | Session context |
| status | VARCHAR(20) | active, completed, failed |
| started_at | TIMESTAMPTZ | |
| ended_at | TIMESTAMPTZ | |

### agent_decisions
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| session_id | UUID FK | |
| decision_type | VARCHAR(50) | trade_signal, risk_assessment |
| reasoning | TEXT | Claude's reasoning |
| action | JSONB | Recommended action |
| confidence_score | NUMERIC(5,4) | 0.0 to 1.0 |
| input_tokens | INTEGER | API usage |
| output_tokens | INTEGER | |

## Monitoring

### alerts
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| alert_type | VARCHAR(50) | risk_limit, system_error |
| severity | VARCHAR(20) | info, warning, critical |
| message | TEXT | |
| metadata | JSONB | |
| acknowledged | BOOLEAN | |

### performance_metrics
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| metric_name | VARCHAR(100) | portfolio_value, drawdown |
| metric_value | NUMERIC(20,8) | |
| dimensions | JSONB | Labels/tags |
| recorded_at | TIMESTAMPTZ | |
