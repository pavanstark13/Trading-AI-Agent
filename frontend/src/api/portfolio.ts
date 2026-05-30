import { executionClient, riskClient } from './client';
import type { DrawdownStatus, Order, Position, Trade } from '../types';

export const portfolioApi = {
  getPositions: async (): Promise<Position[]> => {
    const { data } = await executionClient.get('/orders/positions');
    return data;
  },

  getOrders: async (status?: string): Promise<Order[]> => {
    const { data } = await executionClient.get('/orders', {
      params: status ? { status } : {},
    });
    return data;
  },

  getTrades: async (limit = 50): Promise<Trade[]> => {
    const { data } = await executionClient.get('/orders/trades', {
      params: { limit },
    });
    return data;
  },

  getDrawdownStatus: async (equity: number): Promise<DrawdownStatus> => {
    const { data } = await riskClient.get(`/risk/drawdown/${equity}`);
    return data;
  },

  cancelOrder: async (externalOrderId: string): Promise<void> => {
    await executionClient.delete(`/orders/${externalOrderId}`);
  },
};
