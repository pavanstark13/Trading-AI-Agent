import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { format } from 'date-fns';

interface EquityPoint {
  timestamp: string;
  equity: number;
  pnl?: number;
}

interface EquityCurveProps {
  data: EquityPoint[];
  height?: number;
}

export function EquityCurve({ data, height = 250 }: EquityCurveProps) {
  const isPositive = data.length >= 2 && data[data.length - 1].equity >= data[0].equity;
  const color = isPositive ? '#22c55e' : '#ef4444';

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-white mb-4">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.3} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(val) => format(new Date(val), 'MM/dd')}
            stroke="#475569"
            tick={{ fontSize: 11, fill: '#94a3b8' }}
          />
          <YAxis
            tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
            stroke="#475569"
            tick={{ fontSize: 11, fill: '#94a3b8' }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
            labelFormatter={(val) => format(new Date(val), 'MMM dd, yyyy HH:mm')}
            formatter={(val: number) => [`$${val.toLocaleString()}`, 'Equity']}
          />
          <Area
            type="monotone"
            dataKey="equity"
            stroke={color}
            strokeWidth={2}
            fill="url(#equityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
