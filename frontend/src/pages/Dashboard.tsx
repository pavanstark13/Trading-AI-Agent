import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../api/market';
import { CandlestickChart } from '../components/charts/CandlestickChart';
import { EquityCurve } from '../components/charts/EquityCurve';
import { PortfolioView } from '../components/portfolio/PortfolioView';
import { useState } from 'react';

const TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d'];
const DEFAULT_TICKERS = ['AAPL', 'SPY', 'NVDA', 'TSLA'];

export function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');

  const { data: bars = [] } = useQuery({
    queryKey: ['historical', selectedTicker, selectedTimeframe],
    queryFn: () => marketApi.getHistorical(selectedTicker, selectedTimeframe, undefined, undefined, 200),
    refetchInterval: 60000,
  });

  // Mock equity curve data
  const equityData = Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(Date.now() - (29 - i) * 86400000).toISOString(),
    equity: 100000 + (Math.random() - 0.3) * 2000 * i,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-white">Dashboard</h1>

      {/* Chart Controls */}
      <div className="flex items-center gap-4">
        <div className="flex gap-2">
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
      <CandlestickChart data={bars} ticker={selectedTicker} timeframe={selectedTimeframe} height={400} />

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EquityCurve data={equityData} />
        <PortfolioView />
      </div>
    </div>
  );
}
