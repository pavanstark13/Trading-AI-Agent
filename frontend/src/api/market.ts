import { agentClient } from './client';
import type { MarketQuote, OHLCVBar } from '../types';

export const marketApi = {
  getAssets: async (): Promise<{ stocks: string[]; crypto: string[]; forex: string[] }> => {
    const { data } = await agentClient.get('/market/assets');
    return data;
  },

  getQuote: async (ticker: string): Promise<MarketQuote> => {
    const { data } = await agentClient.get(`/market/quotes/${ticker}`);
    return data;
  },

  getQuotes: async (tickers: string[]): Promise<MarketQuote[]> => {
    const { data } = await agentClient.get('/market/quotes', {
      params: { tickers: tickers.join(',') },
    });
    return data;
  },

  getHistorical: async (
    ticker: string,
    timeframe = '1h',
    start?: string,
    end?: string,
    limit = 200,
  ): Promise<OHLCVBar[]> => {
    const { data } = await agentClient.get(`/market/historical/${ticker}`, {
      params: { timeframe, start, end, limit },
    });
    return data;
  },

  getMarketStatus: async (): Promise<Record<string, unknown>> => {
    const { data } = await agentClient.get('/market/market-status');
    return data;
  },
};
