import { PortfolioView } from '../components/portfolio/PortfolioView';
import { TradeHistory } from '../components/trades/TradeHistory';

export function Portfolio() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-white">Portfolio</h1>
      <PortfolioView />
      <TradeHistory />
    </div>
  );
}
