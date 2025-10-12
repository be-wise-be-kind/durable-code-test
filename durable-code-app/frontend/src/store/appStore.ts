import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppState {
  theme: 'light' | 'dark';
  isLoading: boolean;
  error: string | null;
  setTheme: (theme: 'light' | 'dark') => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

// Conditionally apply devtools middleware only in development
const middleware = import.meta.env.DEV ? devtools : <T>(f: T) => f;

export const useAppStore = create<AppState>()(
  middleware(
    (set) => ({
      theme: 'light',
      isLoading: false,
      error: null,
      setTheme: (theme) => set({ theme }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    { name: 'app-store' },
  ),
);
