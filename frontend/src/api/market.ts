import { marketDataClient } from './client';
import type { MarketQuote, OHLCVBar, Symbol } from '../types';

export const marketApi = {
  getSymbols: async (activeOnly = true): Promise<Symbol[]> => {
    const { data } = await marketDataClient.get('/market/symbols', {
      params: { active_only: activeOnly },
    });
    return data;
  },

  getSymbol: async (ticker: string): Promise<Symbol> => {
    const { data } = await marketDataClient.get(`/market/symbols/${ticker}`);
    return data;
  },

  getQuote: async (ticker: string): Promise<MarketQuote> => {
    const { data } = await marketDataClient.get(`/market/quotes/${ticker}`);
    return data;
  },

  getQuotes: async (tickers: string[]): Promise<MarketQuote[]> => {
    const { data } = await marketDataClient.get('/market/quotes', {
      params: { tickers: tickers.join(',') },
    });
    return data;
  },

  getHistorical: async (
    ticker: string,
    timeframe: string = '1h',
    start?: string,
    end?: string,
    limit: number = 200
  ): Promise<OHLCVBar[]> => {
    const { data } = await marketDataClient.get(`/market/historical/${ticker}`, {
      params: { timeframe, start, end, limit },
    });
    return data;
  },
};
