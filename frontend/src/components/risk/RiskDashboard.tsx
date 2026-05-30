import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle, Shield, XCircle } from 'lucide-react';
import { portfolioApi } from '../../api/portfolio';

const ACCOUNT_EQUITY = 100_000; // Would come from portfolio summary in production

export function RiskDashboard() {
  const { data: drawdown } = useQuery({
    queryKey: ['drawdown', ACCOUNT_EQUITY],
    queryFn: () => portfolioApi.getDrawdownStatus(ACCOUNT_EQUITY),
    refetchInterval: 30000,
  });

  return (
    <div className="space-y-4">
      {/* Circuit Breaker Status */}
      <div
        className={`rounded-xl p-4 border ${
          drawdown?.is_circuit_breaker_active
            ? 'bg-red-950 border-red-800'
            : 'bg-gray-900 border-gray-800'
        }`}
      >
        <div className="flex items-center gap-3">
          {drawdown?.is_circuit_breaker_active ? (
            <XCircle className="w-6 h-6 text-red-400" />
          ) : (
            <CheckCircle className="w-6 h-6 text-green-400" />
          )}
          <div>
            <h3 className="text-sm font-semibold text-white">Circuit Breaker</h3>
            <p className="text-xs text-gray-400">
              {drawdown?.is_circuit_breaker_active ? 'ACTIVE - Trading Halted' : 'Inactive - Trading Allowed'}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        <RiskMetric
          label="Current Drawdown"
          value={`${((drawdown?.current_drawdown_pct ?? 0) * 100).toFixed(2)}%`}
          limit={`${((drawdown?.max_drawdown_pct ?? 0.15) * 100).toFixed(0)}% max`}
          level={getDrawdownLevel(drawdown?.current_drawdown_pct ?? 0, drawdown?.max_drawdown_pct ?? 0.15)}
        />
        <RiskMetric
          label="Daily Loss"
          value={`${((drawdown?.daily_loss_pct ?? 0) * 100).toFixed(2)}%`}
          limit={`${((drawdown?.daily_loss_limit_pct ?? 0.05) * 100).toFixed(0)}% limit`}
          level={getDrawdownLevel(drawdown?.daily_loss_pct ?? 0, drawdown?.daily_loss_limit_pct ?? 0.05)}
        />
        <RiskMetric
          label="Peak Equity"
          value={`$${(drawdown?.peak_equity ?? ACCOUNT_EQUITY).toLocaleString()}`}
          limit="All-time high"
          level="info"
        />
        <RiskMetric
          label="Current Equity"
          value={`$${(drawdown?.current_equity ?? ACCOUNT_EQUITY).toLocaleString()}`}
          limit={`$${Math.max(0, (drawdown?.current_equity ?? ACCOUNT_EQUITY) - (drawdown?.peak_equity ?? ACCOUNT_EQUITY)).toFixed(0)} from peak`}
          level="info"
        />
      </div>
    </div>
  );
}

function getDrawdownLevel(current: number, max: number): 'safe' | 'warning' | 'danger' | 'info' {
  const pct = current / max;
  if (pct >= 1) return 'danger';
  if (pct >= 0.8) return 'warning';
  return 'safe';
}

function RiskMetric({
  label,
  value,
  limit,
  level,
}: {
  label: string;
  value: string;
  limit: string;
  level: 'safe' | 'warning' | 'danger' | 'info';
}) {
  const colors = {
    safe: 'text-green-400',
    warning: 'text-yellow-400',
    danger: 'text-red-400',
    info: 'text-blue-400',
  };

  const icons = {
    safe: <CheckCircle className="w-4 h-4 text-green-400" />,
    warning: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
    danger: <XCircle className="w-4 h-4 text-red-400" />,
    info: <Shield className="w-4 h-4 text-blue-400" />,
  };

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-400">{label}</p>
        {icons[level]}
      </div>
      <p className={`text-xl font-bold font-mono ${colors[level]}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-1">{limit}</p>
    </div>
  );
}
