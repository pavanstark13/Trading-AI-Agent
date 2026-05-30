import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { EquityCurve } from '../components/charts/EquityCurve';
import { portfolioApi } from '../api/portfolio';

export function Analytics() {
  const { data: trades = [] } = useQuery({
    queryKey: ['trades', 100],
    queryFn: () => portfolioApi.getTrades(100),
  });

  // Compute P&L by day from trades
  const dailyPnl = trades.reduce((acc: Record<string, number>, trade) => {
    const day = trade.executed_at.slice(0, 10);
    acc[day] = (acc[day] ?? 0) + (trade.pnl ?? 0);
    return acc;
  }, {});

  const pnlData = Object.entries(dailyPnl)
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-30)
    .map(([date, pnl]) => ({ date: date.slice(5), pnl: Math.round(pnl * 100) / 100 }));

  const winningTrades = trades.filter((t) => (t.pnl ?? 0) > 0).length;
  const winRate = trades.length > 0 ? (winningTrades / trades.length) * 100 : 0;
  const totalPnl = trades.reduce((sum, t) => sum + (t.pnl ?? 0), 0);
  const avgWin = trades.filter((t) => (t.pnl ?? 0) > 0).reduce((s, t) => s + (t.pnl ?? 0), 0) / Math.max(winningTrades, 1);
  const avgLoss = trades.filter((t) => (t.pnl ?? 0) <= 0).reduce((s, t) => s + Math.abs(t.pnl ?? 0), 0) / Math.max(trades.length - winningTrades, 1);

  // Mock equity curve
  const equityData = Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(Date.now() - (29 - i) * 86400000).toISOString(),
    equity: 100000 + totalPnl * (i / 30),
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-white">Analytics</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Trades', value: trades.length.toString() },
          { label: 'Win Rate', value: `${winRate.toFixed(1)}%` },
          { label: 'Avg Win', value: `$${avgWin.toFixed(2)}` },
          { label: 'Avg Loss', value: `-$${avgLoss.toFixed(2)}` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-xs text-gray-400 mb-1">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      {/* Equity Curve */}
      <EquityCurve data={equityData} />

      {/* Daily P&L Bar Chart */}
      <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
        <h3 className="text-sm font-semibold text-white mb-4">Daily P&L</h3>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={pnlData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <YAxis stroke="#475569" tick={{ fontSize: 10, fill: '#94a3b8' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              formatter={(val: number) => [`$${val.toFixed(2)}`, 'P&L']}
            />
            <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
              {pnlData.map((entry, i) => (
                <Cell key={i} fill={entry.pnl >= 0 ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
