import { configureStore } from '@reduxjs/toolkit';
import portfolioReducer from './portfolioSlice';
import marketReducer from './marketSlice';

export const store = configureStore({
  reducer: {
    portfolio: portfolioReducer,
    market: marketReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
