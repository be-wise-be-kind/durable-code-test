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
export const useAppStore = import.meta.env.DEV
  ? create<AppState>()(
      devtools(
        (set) => ({
          theme: 'light',
          isLoading: false,
          error: null,
          setTheme: (theme: 'light' | 'dark') => set({ theme }),
          setLoading: (isLoading: boolean) => set({ isLoading }),
          setError: (error: string | null) => set({ error }),
        }),
        { name: 'app-store' },
      ),
    )
  : create<AppState>()((set) => ({
      theme: 'light',
      isLoading: false,
      error: null,
      setTheme: (theme: 'light' | 'dark') => set({ theme }),
      setLoading: (isLoading: boolean) => set({ isLoading }),
      setError: (error: string | null) => set({ error }),
    }));
