-- ============================================================
-- AI Trading Agent Platform - PostgreSQL Schema
-- ============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- MARKET DATA SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS symbols (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker        VARCHAR(20)  NOT NULL UNIQUE,
    name          VARCHAR(255) NOT NULL,
    exchange      VARCHAR(50)  NOT NULL,
    asset_type    VARCHAR(50)  NOT NULL DEFAULT 'stock', -- stock, crypto, forex, futures
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_symbols_ticker    ON symbols (ticker);
CREATE INDEX idx_symbols_exchange  ON symbols (exchange);
CREATE INDEX idx_symbols_is_active ON symbols (is_active);

CREATE TABLE IF NOT EXISTS ohlcv (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol_id   UUID        NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    timeframe   VARCHAR(10) NOT NULL, -- 1m, 5m, 15m, 1h, 4h, 1d
    open        NUMERIC(20,8) NOT NULL,
    high        NUMERIC(20,8) NOT NULL,
    low         NUMERIC(20,8) NOT NULL,
    close       NUMERIC(20,8) NOT NULL,
    volume      NUMERIC(20,2) NOT NULL,
    timestamp   TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (symbol_id, timeframe, timestamp)
);

CREATE INDEX idx_ohlcv_symbol_timeframe_ts ON ohlcv (symbol_id, timeframe, timestamp DESC);
CREATE INDEX idx_ohlcv_timestamp           ON ohlcv (timestamp DESC);

CREATE TABLE IF NOT EXISTS market_snapshots (
    id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol_id     UUID        NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    bid           NUMERIC(20,8),
    ask           NUMERIC(20,8),
    last          NUMERIC(20,8) NOT NULL,
    volume        NUMERIC(20,2),
    bid_size      NUMERIC(20,2),
    ask_size      NUMERIC(20,2),
    snapshot_time TIMESTAMPTZ NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_market_snapshots_symbol_time ON market_snapshots (symbol_id, snapshot_time DESC);

-- ============================================================
-- STRATEGY ENGINE SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS strategies (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    type        VARCHAR(50) NOT NULL, -- smc, rule_based, ml, hybrid
    parameters  JSONB       NOT NULL DEFAULT '{}',
    is_active   BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_strategies_type      ON strategies (type);
CREATE INDEX idx_strategies_is_active ON strategies (is_active);

CREATE TABLE IF NOT EXISTS signals (
    id           UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id  UUID          NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    symbol_id    UUID          NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    signal_type  VARCHAR(50)   NOT NULL, -- entry, exit, scale_in, scale_out
    direction    VARCHAR(10)   NOT NULL, -- long, short
    strength     NUMERIC(5,4)  NOT NULL CHECK (strength BETWEEN 0 AND 1),
    price        NUMERIC(20,8) NOT NULL,
    stop_loss    NUMERIC(20,8),
    take_profit  NUMERIC(20,8),
    timeframe    VARCHAR(10),
    metadata     JSONB         NOT NULL DEFAULT '{}',
    is_executed  BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_signals_strategy    ON signals (strategy_id);
CREATE INDEX idx_signals_symbol      ON signals (symbol_id);
CREATE INDEX idx_signals_created_at  ON signals (created_at DESC);
CREATE INDEX idx_signals_is_executed ON signals (is_executed);

-- ============================================================
-- RISK MANAGEMENT SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS risk_profiles (
    id                       UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                     VARCHAR(100)  NOT NULL UNIQUE,
    description              TEXT,
    max_position_size_pct    NUMERIC(5,4)  NOT NULL DEFAULT 0.02, -- 2%
    daily_loss_limit_pct     NUMERIC(5,4)  NOT NULL DEFAULT 0.05, -- 5%
    max_drawdown_pct         NUMERIC(5,4)  NOT NULL DEFAULT 0.15, -- 15%
    risk_per_trade_pct       NUMERIC(5,4)  NOT NULL DEFAULT 0.01, -- 1%
    max_open_positions       INTEGER       NOT NULL DEFAULT 10,
    kelly_fraction           NUMERIC(5,4)  NOT NULL DEFAULT 0.25, -- quarter-kelly
    is_active                BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_events (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type  VARCHAR(50) NOT NULL, -- limit_breach, drawdown_alert, position_limit, daily_loss
    severity    VARCHAR(20) NOT NULL, -- info, warning, critical
    message     TEXT        NOT NULL,
    details     JSONB       NOT NULL DEFAULT '{}',
    acknowledged BOOLEAN    NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_events_event_type ON risk_events (event_type);
CREATE INDEX idx_risk_events_severity   ON risk_events (severity);
CREATE INDEX idx_risk_events_created_at ON risk_events (created_at DESC);

-- ============================================================
-- EXECUTION ENGINE SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS orders (
    id                UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_order_id VARCHAR(100)  UNIQUE,
    symbol_id         UUID          NOT NULL REFERENCES symbols(id),
    strategy_id       UUID          REFERENCES strategies(id),
    signal_id         UUID          REFERENCES signals(id),
    order_type        VARCHAR(20)   NOT NULL, -- market, limit, stop, stop_limit
    side              VARCHAR(10)   NOT NULL, -- buy, sell
    quantity          NUMERIC(20,8) NOT NULL,
    price             NUMERIC(20,8),
    stop_price        NUMERIC(20,8),
    time_in_force     VARCHAR(10)   NOT NULL DEFAULT 'day', -- day, gtc, ioc, fok
    status            VARCHAR(20)   NOT NULL DEFAULT 'pending', -- pending, submitted, partial, filled, cancelled, rejected
    filled_qty        NUMERIC(20,8) NOT NULL DEFAULT 0,
    avg_fill_price    NUMERIC(20,8),
    rejection_reason  TEXT,
    broker_metadata   JSONB         NOT NULL DEFAULT '{}',
    submitted_at      TIMESTAMPTZ,
    filled_at         TIMESTAMPTZ,
    cancelled_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_symbol_id   ON orders (symbol_id);
CREATE INDEX idx_orders_strategy_id ON orders (strategy_id);
CREATE INDEX idx_orders_status      ON orders (status);
CREATE INDEX idx_orders_created_at  ON orders (created_at DESC);

CREATE TABLE IF NOT EXISTS trades (
    id             UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id       UUID          NOT NULL REFERENCES orders(id),
    symbol_id      UUID          NOT NULL REFERENCES symbols(id),
    side           VARCHAR(10)   NOT NULL, -- buy, sell
    quantity       NUMERIC(20,8) NOT NULL,
    price          NUMERIC(20,8) NOT NULL,
    commission     NUMERIC(20,8) NOT NULL DEFAULT 0,
    pnl            NUMERIC(20,8),
    pnl_pct        NUMERIC(10,6),
    is_closing     BOOLEAN       NOT NULL DEFAULT FALSE,
    executed_at    TIMESTAMPTZ   NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trades_order_id   ON trades (order_id);
CREATE INDEX idx_trades_symbol_id  ON trades (symbol_id);
CREATE INDEX idx_trades_executed_at ON trades (executed_at DESC);

CREATE TABLE IF NOT EXISTS positions (
    id                 UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol_id          UUID          NOT NULL REFERENCES symbols(id) UNIQUE,
    side               VARCHAR(10)   NOT NULL, -- long, short
    quantity           NUMERIC(20,8) NOT NULL,
    avg_entry_price    NUMERIC(20,8) NOT NULL,
    current_price      NUMERIC(20,8),
    unrealized_pnl     NUMERIC(20,8),
    unrealized_pnl_pct NUMERIC(10,6),
    realized_pnl       NUMERIC(20,8) NOT NULL DEFAULT 0,
    opened_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_positions_symbol_id ON positions (symbol_id);

-- ============================================================
-- AI AGENT SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS agent_sessions (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type  VARCHAR(50) NOT NULL, -- market_analyst, risk_manager, trade_executor, performance_reviewer, orchestrator
    context     JSONB       NOT NULL DEFAULT '{}',
    status      VARCHAR(20) NOT NULL DEFAULT 'active', -- active, completed, failed
    started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_sessions_agent_type ON agent_sessions (agent_type);
CREATE INDEX idx_agent_sessions_started_at ON agent_sessions (started_at DESC);

CREATE TABLE IF NOT EXISTS agent_decisions (
    id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id       UUID          NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    decision_type    VARCHAR(50)   NOT NULL, -- trade_signal, risk_assessment, position_size, portfolio_review
    reasoning        TEXT          NOT NULL,
    action           JSONB         NOT NULL DEFAULT '{}',
    confidence_score NUMERIC(5,4)  NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    was_executed     BOOLEAN       NOT NULL DEFAULT FALSE,
    input_tokens     INTEGER,
    output_tokens    INTEGER,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_decisions_session_id    ON agent_decisions (session_id);
CREATE INDEX idx_agent_decisions_decision_type ON agent_decisions (decision_type);
CREATE INDEX idx_agent_decisions_created_at    ON agent_decisions (created_at DESC);

-- ============================================================
-- MONITORING SERVICE
-- ============================================================

CREATE TABLE IF NOT EXISTS alerts (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type   VARCHAR(50) NOT NULL, -- price_alert, drawdown_alert, position_limit, system_error
    severity     VARCHAR(20) NOT NULL, -- info, warning, critical
    message      TEXT        NOT NULL,
    metadata     JSONB       NOT NULL DEFAULT '{}',
    acknowledged BOOLEAN     NOT NULL DEFAULT FALSE,
    ack_at       TIMESTAMPTZ,
    ack_by       VARCHAR(100),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_alert_type   ON alerts (alert_type);
CREATE INDEX idx_alerts_severity     ON alerts (severity);
CREATE INDEX idx_alerts_acknowledged ON alerts (acknowledged);
CREATE INDEX idx_alerts_created_at   ON alerts (created_at DESC);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id           UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name  VARCHAR(100)  NOT NULL,
    metric_value NUMERIC(20,8) NOT NULL,
    dimensions   JSONB         NOT NULL DEFAULT '{}',
    recorded_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_perf_metrics_name        ON performance_metrics (metric_name);
CREATE INDEX idx_perf_metrics_recorded_at ON performance_metrics (recorded_at DESC);
CREATE INDEX idx_perf_metrics_name_time   ON performance_metrics (metric_name, recorded_at DESC);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default risk profile
INSERT INTO risk_profiles (name, description, max_position_size_pct, daily_loss_limit_pct, max_drawdown_pct, risk_per_trade_pct, is_active)
VALUES ('default', 'Conservative default risk profile', 0.02, 0.05, 0.15, 0.01, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Common symbols
INSERT INTO symbols (ticker, name, exchange, asset_type) VALUES
    ('AAPL',  'Apple Inc.',         'NASDAQ', 'stock'),
    ('MSFT',  'Microsoft Corp.',    'NASDAQ', 'stock'),
    ('GOOGL', 'Alphabet Inc.',      'NASDAQ', 'stock'),
    ('AMZN',  'Amazon.com Inc.',    'NASDAQ', 'stock'),
    ('NVDA',  'NVIDIA Corp.',       'NASDAQ', 'stock'),
    ('TSLA',  'Tesla Inc.',         'NASDAQ', 'stock'),
    ('SPY',   'SPDR S&P 500 ETF',   'NYSE',   'etf'),
    ('QQQ',   'Invesco QQQ ETF',    'NASDAQ', 'etf'),
    ('BTC/USD', 'Bitcoin',          'CRYPTO', 'crypto'),
    ('ETH/USD', 'Ethereum',         'CRYPTO', 'crypto')
ON CONFLICT (ticker) DO NOTHING;

-- Default strategies
INSERT INTO strategies (name, description, type, parameters) VALUES
    ('SMC_Primary', 'Smart Money Concepts primary strategy', 'smc',
        '{"timeframe": "1h", "min_strength": 0.7, "order_block_lookback": 20}'),
    ('MA_Crossover', 'Moving Average Crossover strategy', 'rule_based',
        '{"fast_period": 20, "slow_period": 50, "signal_period": 9}'),
    ('RSI_Mean_Reversion', 'RSI mean reversion strategy', 'rule_based',
        '{"rsi_period": 14, "oversold": 30, "overbought": 70}')
ON CONFLICT (name) DO NOTHING;
