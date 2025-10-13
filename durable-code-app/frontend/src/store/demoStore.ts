import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface WaveformPoint {
  x: number;
  y: number;
}

interface DemoState {
  // WebSocket connection state
  isConnected: boolean;
  connectionStatus: 'disconnected' | 'connecting' | 'connected' | 'error';
  socket: WebSocket | null;

  // Oscilloscope data
  waveformData: WaveformPoint[];
  amplitude: number;
  frequency: number;

  // Actions
  setConnected: (connected: boolean) => void;
  setConnectionStatus: (
    status: 'disconnected' | 'connecting' | 'connected' | 'error',
  ) => void;
  setSocket: (socket: WebSocket | null) => void;
  setWaveformData: (data: WaveformPoint[]) => void;
  setAmplitude: (amplitude: number) => void;
  setFrequency: (frequency: number) => void;
  reset: () => void;
}

// Conditionally apply devtools middleware only in development
const middleware = import.meta.env.DEV ? devtools : <T>(f: T) => f;

export const useDemoStore = create<DemoState>()(
  middleware(
    (set) => ({
      // Initial state
      isConnected: false,
      connectionStatus: 'disconnected',
      socket: null,
      waveformData: [],
      amplitude: 1.0,
      frequency: 1.0,

      // Actions
      setConnected: (isConnected) => set({ isConnected }),
      setConnectionStatus: (connectionStatus) => set({ connectionStatus }),
      setSocket: (socket) => set({ socket }),
      setWaveformData: (waveformData) => set({ waveformData }),
      setAmplitude: (amplitude) => set({ amplitude }),
      setFrequency: (frequency) => set({ frequency }),
      reset: () =>
        set({
          isConnected: false,
          connectionStatus: 'disconnected',
          socket: null,
          waveformData: [],
          amplitude: 1.0,
          frequency: 1.0,
        }),
    }),
    { name: 'demo-store' },
  ),
);
