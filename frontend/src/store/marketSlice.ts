import { createAsyncThunk, createSlice, type PayloadAction } from '@reduxjs/toolkit';
import { marketApi } from '../api/market';
import type { MarketQuote, OHLCVBar, Symbol } from '../types';

interface MarketState {
  symbols: Symbol[];
  quotes: Record<string, MarketQuote>;
  historicalBars: Record<string, OHLCVBar[]>;
  selectedTicker: string;
  selectedTimeframe: string;
  loading: boolean;
  error: string | null;
}

const initialState: MarketState = {
  symbols: [],
  quotes: {},
  historicalBars: {},
  selectedTicker: 'AAPL',
  selectedTimeframe: '1h',
  loading: false,
  error: null,
};

export const fetchSymbols = createAsyncThunk('market/fetchSymbols', async () => {
  return marketApi.getSymbols();
});

export const fetchQuotes = createAsyncThunk('market/fetchQuotes', async (tickers: string[]) => {
  return marketApi.getQuotes(tickers);
});

export const fetchHistorical = createAsyncThunk(
  'market/fetchHistorical',
  async ({ ticker, timeframe, limit }: { ticker: string; timeframe: string; limit?: number }) => {
    const bars = await marketApi.getHistorical(ticker, timeframe, undefined, undefined, limit);
    return { ticker, timeframe, bars };
  }
);

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setSelectedTicker(state, action: PayloadAction<string>) {
      state.selectedTicker = action.payload;
    },
    setSelectedTimeframe(state, action: PayloadAction<string>) {
      state.selectedTimeframe = action.payload;
    },
    updateQuote(state, action: PayloadAction<MarketQuote>) {
      state.quotes[action.payload.ticker] = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchSymbols.fulfilled, (state, action) => {
        state.symbols = action.payload;
      })
      .addCase(fetchQuotes.fulfilled, (state, action) => {
        for (const quote of action.payload) {
          state.quotes[quote.ticker] = quote;
        }
      })
      .addCase(fetchHistorical.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchHistorical.fulfilled, (state, action) => {
        const { ticker, bars } = action.payload;
        state.historicalBars[ticker] = bars;
        state.loading = false;
      })
      .addCase(fetchHistorical.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to fetch historical data';
        state.loading = false;
      });
  },
});

export const { setSelectedTicker, setSelectedTimeframe, updateQuote } = marketSlice.actions;
export default marketSlice.reducer;
