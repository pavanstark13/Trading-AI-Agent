import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { portfolioApi } from '../api/portfolio';
import type { DrawdownStatus, Order, Position, PortfolioSummary, Trade } from '../types';

interface PortfolioState {
  positions: Position[];
  orders: Order[];
  trades: Trade[];
  drawdownStatus: DrawdownStatus | null;
  summary: PortfolioSummary | null;
  loading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  positions: [],
  orders: [],
  trades: [],
  drawdownStatus: null,
  summary: null,
  loading: false,
  error: null,
};

export const fetchPositions = createAsyncThunk('portfolio/fetchPositions', async () => {
  return portfolioApi.getPositions();
});

export const fetchOrders = createAsyncThunk('portfolio/fetchOrders', async (status?: string) => {
  return portfolioApi.getOrders(status);
});

export const fetchTrades = createAsyncThunk('portfolio/fetchTrades', async (limit: number = 50) => {
  return portfolioApi.getTrades(limit);
});

export const fetchDrawdownStatus = createAsyncThunk(
  'portfolio/fetchDrawdownStatus',
  async (equity: number) => {
    return portfolioApi.getDrawdownStatus(equity);
  }
);

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    updatePosition(state, action: PayloadAction<Position>) {
      const idx = state.positions.findIndex((p) => p.id === action.payload.id);
      if (idx >= 0) {
        state.positions[idx] = action.payload;
      } else {
        state.positions.push(action.payload);
      }
    },
    updateSummary(state, action: PayloadAction<PortfolioSummary>) {
      state.summary = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPositions.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchPositions.fulfilled, (state, action) => {
        state.positions = action.payload;
        state.loading = false;
      })
      .addCase(fetchPositions.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to fetch positions';
        state.loading = false;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.orders = action.payload;
      })
      .addCase(fetchTrades.fulfilled, (state, action) => {
        state.trades = action.payload;
      })
      .addCase(fetchDrawdownStatus.fulfilled, (state, action) => {
        state.drawdownStatus = action.payload;
      });
  },
});

export const { updatePosition, updateSummary, clearError } = portfolioSlice.actions;
export default portfolioSlice.reducer;
