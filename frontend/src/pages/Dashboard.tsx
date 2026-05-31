import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../api/market';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { EquityCurve } from '../components/charts/EquityCurve';
import { PortfolioView } from '../components/portfolio/PortfolioView';
import { useState, useMemo } from 'react';
import type { OHLCVBar } from '../types';

const TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d'];
const DEFAULT_TICKERS = ['AAPL', 'SPY', 'NVDA', 'TSLA'];

const MOCK_PRICES: Record<string, number> = {
  AAPL: 189.5, SPY: 528.3, NVDA: 1208.4, TSLA: 182.6,
};

function generateMockBars(ticker: string, count = 100): OHLCVBar[] {
  const base = MOCK_PRICES[ticker] ?? 100;
  const bars: OHLCVBar[] = [];
  let price = base;
  const now = Date.now();
  for (let i = count; i >= 0; i--) {
    const change = (Math.random() - 0.48) * base * 0.012;
    const open = price;
    price = Math.max(price + change, base * 0.7);
    const high = Math.max(open, price) * (1 + Math.random() * 0.004);
    const low = Math.min(open, price) * (1 - Math.random() * 0.004);
    bars.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(price.toFixed(2)),
      volume: Math.floor(Math.random() * 5000000 + 1000000),
    });
  }
  return bars;
}

export function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');

  const { data: bars } = useQuery({
    queryKey: ['historical', selectedTicker, selectedTimeframe],
    queryFn: () => marketApi.getHistorical(selectedTicker, selectedTimeframe, undefined, undefined, 200),
    refetchInterval: 60000,
    retry: 1,
  });

  const mockBars = useMemo(() => generateMockBars(selectedTicker), [selectedTicker]);
  const chartData = bars && bars.length > 0 ? bars : mockBars;

  const equityData = useMemo(() => {
    let equity = 100000;
    return Array.from({ length: 30 }, (_, i) => {
      equity += (Math.random() - 0.42) * 1200;
      return {
        timestamp: new Date(Date.now() - (29 - i) * 86400000).toISOString(),
        equity: parseFloat(equity.toFixed(2)),
      };
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Dashboard</h1>
        <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
          {bars && bars.length > 0 ? '🟢 Live' : '🟡 Demo'}
        </span>
      </div>

      {/* Chart Controls */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex gap-2 flex-wrap">
          {DEFAULT_TICKERS.map((ticker) => (
            <button
              key={ticker}
              onClick={() => setSelectedTicker(ticker)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedTicker === ticker
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {ticker}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setSelectedTimeframe(tf)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                selectedTimeframe === tf
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-800 text-gray-500 hover:text-white'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Main Chart */}
      <CandlestickChart data={chartData} ticker={selectedTicker} timeframe={selectedTimeframe} height={400} />

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EquityCurve data={equityData} />
        <PortfolioView />
      </div>
    </div>
  );
}
