import { TradeHistory } from '../components/trades/TradeHistory';

export function Trades() {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-white">Trade History</h1>
      <TradeHistory />
    </div>
  );
}
