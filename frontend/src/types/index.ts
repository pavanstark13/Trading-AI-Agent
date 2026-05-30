// ── Market Data Types ─────────────────────────────────────────────────────────

export interface Symbol {
  id: string;
  ticker: string;
  name: string;
  exchange: string;
  asset_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OHLCVBar {
  id: string;
  symbol_id: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
}

export interface MarketQuote {
  ticker: string;
  bid: number | null;
  ask: number | null;
  last: number;
  change: number | null;
  change_pct: number | null;
  volume: number | null;
  timestamp: string;
}

// ── Portfolio Types ───────────────────────────────────────────────────────────

export interface Position {
  id: string;
  symbol_id: string;
  ticker?: string;
  side: 'long' | 'short';
  quantity: number;
  avg_entry_price: number;
  current_price: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  realized_pnl: number;
  opened_at: string;
}

export interface Trade {
  id: string;
  order_id: string;
  symbol_id: string;
  ticker?: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission: number;
  pnl: number | null;
  pnl_pct: number | null;
  executed_at: string;
}

export interface Order {
  id: string;
  external_order_id: string | null;
  symbol_id: string;
  order_type: string;
  side: string;
  quantity: number;
  price: number | null;
  stop_price: number | null;
  time_in_force: string;
  status: string;
  filled_qty: number;
  avg_fill_price: number | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
}

// ── Strategy Types ────────────────────────────────────────────────────────────

export interface Strategy {
  id: string;
  name: string;
  description: string | null;
  type: string;
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export interface Signal {
  id: string;
  strategy_id: string;
  symbol_id: string;
  signal_type: string;
  direction: 'long' | 'short';
  strength: number;
  price: number;
  stop_loss: number | null;
  take_profit: number | null;
  timeframe: string | null;
  metadata: Record<string, unknown>;
  is_executed: boolean;
  created_at: string;
}

// ── Risk Types ────────────────────────────────────────────────────────────────

export interface RiskProfile {
  id: string;
  name: string;
  max_position_size_pct: number;
  daily_loss_limit_pct: number;
  max_drawdown_pct: number;
  risk_per_trade_pct: number;
  max_open_positions: number;
  is_active: boolean;
}

export interface DrawdownStatus {
  current_equity: number;
  peak_equity: number;
  current_drawdown_pct: number;
  max_drawdown_pct: number;
  is_circuit_breaker_active: boolean;
  daily_loss_pct: number;
  daily_loss_limit_pct: number;
}

// ── Agent Types ───────────────────────────────────────────────────────────────

export interface AgentDecision {
  id: string;
  session_id: string;
  decision_type: string;
  reasoning: string;
  action: Record<string, unknown>;
  confidence_score: number;
  was_executed: boolean;
  created_at: string;
}

// ── Portfolio Summary ─────────────────────────────────────────────────────────

export interface PortfolioSummary {
  total_equity: number;
  cash_balance: number;
  positions_value: number;
  total_pnl: number;
  total_pnl_pct: number;
  daily_pnl: number;
  daily_pnl_pct: number;
  open_positions: number;
  realized_pnl: number;
}

// ── Alert Types ───────────────────────────────────────────────────────────────

export interface Alert {
  id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  metadata: Record<string, unknown>;
  acknowledged: boolean;
  created_at: string;
}

// ── API Response Types ────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
