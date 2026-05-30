import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { portfolioApi } from '../../api/portfolio';
import type { Trade } from '../../types';

export function TradeHistory() {
  const { data: trades = [], isLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: () => portfolioApi.getTrades(50),
    refetchInterval: 60000,
  });

  if (isLoading) {
    return <div className="bg-gray-900 rounded-xl p-8 animate-pulse h-64" />;
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800">
      <div className="px-4 py-3 border-b border-gray-800">
        <h3 className="text-sm font-semibold text-white">Trade History</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-400 border-b border-gray-800">
              <th className="px-4 py-2 text-left">Time</th>
              <th className="px-4 py-2 text-left">Ticker</th>
              <th className="px-4 py-2 text-left">Side</th>
              <th className="px-4 py-2 text-right">Qty</th>
              <th className="px-4 py-2 text-right">Price</th>
              <th className="px-4 py-2 text-right">Commission</th>
              <th className="px-4 py-2 text-right">P&L</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No trades yet
                </td>
              </tr>
            ) : (
              trades.map((trade) => (
                <TradeRow key={trade.id} trade={trade} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TradeRow({ trade }: { trade: Trade }) {
  const pnl = trade.pnl ?? 0;
  const isProfit = pnl >= 0;

  return (
    <tr className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
      <td className="px-4 py-2 text-gray-400">
        {format(new Date(trade.executed_at), 'MM/dd HH:mm')}
      </td>
      <td className="px-4 py-2 font-medium text-white">
        {trade.ticker || trade.symbol_id.slice(0, 8)}
      </td>
      <td className="px-4 py-2">
        <span
          className={`font-medium ${
            trade.side === 'buy' ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {trade.side.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-2 text-right font-mono text-gray-300">
        {trade.quantity.toFixed(4)}
      </td>
      <td className="px-4 py-2 text-right font-mono text-gray-300">
        ${trade.price.toFixed(2)}
      </td>
      <td className="px-4 py-2 text-right font-mono text-gray-400">
        ${trade.commission.toFixed(2)}
      </td>
      <td className={`px-4 py-2 text-right font-mono font-semibold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
        {trade.pnl !== null ? `${isProfit ? '+' : ''}$${pnl.toFixed(2)}` : '—'}
      </td>
    </tr>
  );
}
