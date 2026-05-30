import { Bell, RefreshCw, Settings } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { marketApi } from '../../api/market';

export function Header() {
  const { data: quotes, refetch, isFetching } = useQuery({
    queryKey: ['quotes', ['SPY', 'QQQ']],
    queryFn: () => marketApi.getQuotes(['SPY', 'QQQ']),
    refetchInterval: 15000,
  });

  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      {/* Market tickers */}
      <div className="flex items-center gap-6">
        {quotes?.map((quote) => (
          <div key={quote.ticker} className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-300">{quote.ticker}</span>
            <span className="text-sm font-mono text-white">
              ${quote.last.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            {quote.change_pct !== null && (
              <span
                className={`text-xs font-medium ${
                  quote.change_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {quote.change_pct >= 0 ? '+' : ''}
                {(quote.change_pct * 100).toFixed(2)}%
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => refetch()}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          title="Refresh data"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
        <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
