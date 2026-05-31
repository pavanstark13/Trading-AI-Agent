import { agentClient } from './client';
import type { Position, Trade } from '../types';

export const portfolioApi = {
  getAccount: async (): Promise<{ equity: number; cash: number; buying_power: number; total_pnl: number; total_pnl_pct: number; day_pnl: number }> => {
    const { data } = await agentClient.get('/portfolio/account');
    return data;
  },

  getPositions: async (): Promise<Position[]> => {
    const { data } = await agentClient.get('/portfolio/positions');
    return data;
  },

  getTrades: async (limit = 50): Promise<Trade[]> => {
    const { data } = await agentClient.get('/portfolio/trades', {
      params: { limit },
    });
    return data;
  },

  placeOrder: async (ticker: string, side: string, qty: number): Promise<unknown> => {
    const { data } = await agentClient.post('/portfolio/orders', null, {
      params: { ticker, side, qty },
    });
    return data;
  },
};
