import { TrendingDown, TrendingUp } from 'lucide-react';
import type { Position } from '../../types';

interface PositionCardProps {
  position: Position;
}

export function PositionCard({ position }: PositionCardProps) {
  const pnl = position.unrealized_pnl ?? 0;
  const pnlPct = position.unrealized_pnl_pct ?? 0;
  const isProfit = pnl >= 0;

  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base font-bold text-white">
              {position.ticker || position.symbol_id.slice(0, 8)}
            </span>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                position.side === 'long'
                  ? 'bg-green-900 text-green-300'
                  : 'bg-red-900 text-red-300'
              }`}
            >
              {position.side.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">{position.quantity.toFixed(4)} units</p>
        </div>
        <div className="flex items-center gap-1">
          {isProfit ? (
            <TrendingUp className="w-4 h-4 text-green-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-gray-500">Entry</p>
          <p className="text-gray-200 font-mono">${position.avg_entry_price.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-gray-500">Current</p>
          <p className="text-gray-200 font-mono">
            ${position.current_price?.toFixed(2) ?? 'N/A'}
          </p>
        </div>
        <div>
          <p className="text-gray-500">Unrealized P&L</p>
          <p className={`font-mono font-semibold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
            {isProfit ? '+' : ''}${pnl.toFixed(2)}
          </p>
        </div>
        <div>
          <p className="text-gray-500">P&L %</p>
          <p className={`font-mono font-semibold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
            {isProfit ? '+' : ''}{(pnlPct * 100).toFixed(2)}%
          </p>
        </div>
      </div>
    </div>
  );
}
