import { useQuery } from '@tanstack/react-query';
import { portfolioApi } from '../../api/portfolio';
import { PositionCard } from './PositionCard';

export function PortfolioView() {
  const { data: positions = [], isLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: portfolioApi.getPositions,
    refetchInterval: 30000,
  });

  const totalUnrealizedPnl = positions.reduce((sum, p) => sum + (p.unrealized_pnl ?? 0), 0);
  const totalRealizedPnl = positions.reduce((sum, p) => sum + p.realized_pnl, 0);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-gray-900 rounded-xl p-4 animate-pulse h-28" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-400 mb-1">Open Positions</p>
          <p className="text-2xl font-bold text-white">{positions.length}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-400 mb-1">Unrealized P&L</p>
          <p className={`text-2xl font-bold ${totalUnrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalUnrealizedPnl >= 0 ? '+' : ''}${totalUnrealizedPnl.toFixed(2)}
          </p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
          <p className="text-xs text-gray-400 mb-1">Realized P&L</p>
          <p className={`text-2xl font-bold ${totalRealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {totalRealizedPnl >= 0 ? '+' : ''}${totalRealizedPnl.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Positions */}
      {positions.length === 0 ? (
        <div className="bg-gray-900 rounded-xl p-8 text-center border border-gray-800">
          <p className="text-gray-400">No open positions</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {positions.map((position) => (
            <PositionCard key={position.id} position={position} />
          ))}
        </div>
      )}
    </div>
  );
}
