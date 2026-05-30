import { useEffect, useRef } from 'react';
import type { OHLCVBar } from '../../types';

interface CandlestickChartProps {
  data: OHLCVBar[];
  ticker: string;
  timeframe: string;
  height?: number;
}

export function CandlestickChart({ data, ticker, timeframe, height = 400 }: CandlestickChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data.length) return;

    // Dynamic import of lightweight-charts to avoid SSR issues
    let chart: ReturnType<typeof import('lightweight-charts')['createChart']> | null = null;

    import('lightweight-charts').then(({ createChart, CrosshairMode }) => {
      if (!containerRef.current) return;

      chart = createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height,
        layout: {
          background: { color: '#0f172a' },
          textColor: '#94a3b8',
        },
        grid: {
          vertLines: { color: '#1e293b' },
          horzLines: { color: '#1e293b' },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
        },
        rightPriceScale: {
          borderColor: '#334155',
        },
        timeScale: {
          borderColor: '#334155',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      const candleSeries = chart.addCandlestickSeries({
        upColor: '#22c55e',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#22c55e',
        wickDownColor: '#ef4444',
      });

      const volumeSeries = chart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      });

      const chartData = data.map((bar) => ({
        time: new Date(bar.timestamp).getTime() / 1000 as any,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      }));

      const volumeData = data.map((bar) => ({
        time: new Date(bar.timestamp).getTime() / 1000 as any,
        value: bar.volume,
        color: bar.close >= bar.open ? '#22c55e33' : '#ef444433',
      }));

      candleSeries.setData(chartData);
      volumeSeries.setData(volumeData);
      chart.timeScale().fitContent();

      // Handle resize
      const handleResize = () => {
        if (chart && containerRef.current) {
          chart.applyOptions({ width: containerRef.current.clientWidth });
        }
      };

      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
        chart?.remove();
      };
    });

    return () => {
      chart?.remove();
    };
  }, [data, height]);

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">
          {ticker} <span className="text-gray-400 font-normal">({timeframe})</span>
        </h3>
        {data.length > 0 && (
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <span>O: {data[data.length - 1]?.open.toFixed(2)}</span>
            <span>H: {data[data.length - 1]?.high.toFixed(2)}</span>
            <span>L: {data[data.length - 1]?.low.toFixed(2)}</span>
            <span className={data[data.length - 1]?.close >= data[data.length - 1]?.open ? 'text-green-400' : 'text-red-400'}>
              C: {data[data.length - 1]?.close.toFixed(2)}
            </span>
          </div>
        )}
      </div>
      <div ref={containerRef} style={{ height }} />
    </div>
  );
}
