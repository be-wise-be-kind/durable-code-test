# How to Implement WebSocket in React with StrictMode

## Overview
This guide explains how to implement WebSocket connections in React applications while maintaining compatibility with React StrictMode. The approach uses a singleton pattern to prevent connection thrashing during component re-renders.

## Problem Statement
React StrictMode intentionally double-invokes effects in development to help detect side effects. This causes WebSocket connections to connect and immediately disconnect, breaking real-time features. The singleton pattern solves this by maintaining a persistent connection outside the React component lifecycle.

## Implementation Steps

### 1. Create WebSocket Service
Use the template: `.ai/templates/react-websocket-service.ts.template`

```bash
# Generate the service file
# Replace placeholders:
# - {{SERVICE_CLASS_NAME}}: WebSocketService
# - {{DATA_TYPE}}: YourDataType
# - {{COMMAND_TYPE}}: YourCommandType
# - {{WEBSOCKET_ENDPOINT}}: /api/your-endpoint/stream
# - {{BACKEND_PORT}}: 8000
```

Example implementation:
```typescript
// src/features/demo/services/websocketService.ts
export class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();

  connect(url?: string): Promise<void> {
    // If already connected, resolve immediately
    if (this.isConnected) {
      return Promise.resolve();
    }
    // ... connection logic
  }
}
```

### 2. Create Singleton Wrapper
Use the template: `.ai/templates/react-websocket-singleton.ts.template`

```bash
# Generate the singleton file
# Replace placeholders:
# - {{SERVICE_CLASS_NAME}}: WebSocketService
# - {{SERVICE_NAME}}: WebSocket
# - {{SERVICE_FILE}}: websocketService
```

Example implementation:
```typescript
// src/features/demo/services/websocketSingleton.ts
import { WebSocketService } from './websocketService';

let instance: WebSocketService | null = null;

export function getWebSocketSingleton(): WebSocketService {
  if (!instance) {
    instance = new WebSocketService();
  }
  return instance;
}
```

### 3. Create React Hook
Use the template: `.ai/templates/react-websocket-hook.ts.template`

```bash
# Generate the hook file
# Replace placeholders:
# - {{HOOK_NAME}}: WebSocket
# - {{DATA_TYPE}}: YourDataType
# - {{COMMAND_TYPE}}: YourCommandType
# - {{SERVICE_NAME}}: WebSocket
```

Example implementation:
```typescript
// src/features/demo/hooks/useWebSocket.ts
export function useWebSocket(url?: string): UseWebSocketReturn {
  const service = getWebSocketSingleton();
  const [isConnected, setIsConnected] = useState(false);

  // Setup event listeners
  useEffect(() => {
    const handleOpen = () => {
      setIsConnected(true);
    };

    service.on('open', handleOpen);

    return () => {
      service.off('open', handleOpen);
    };
  }, [service]);

  // Auto-connect on mount
  useEffect(() => {
    if (service.isConnected) {
      setIsConnected(true);
      return;
    }

    service.connect(url);
  }, [service, url]);

  return {
    isConnected,
    send: (cmd) => service.send(cmd),
  };
}
```

### 4. Use in Component
```typescript
// src/features/demo/components/DemoTab.tsx
export function DemoTab() {
  const {
    isConnected,
    lastData,
    send,
    error
  } = useWebSocket();

  const handleStart = () => {
    send({ command: 'start', params: {...} });
  };

  return (
    <div>
      {isConnected ? 'Connected' : 'Disconnected'}
      <button onClick={handleStart} disabled={!isConnected}>
        Start
      </button>
    </div>
  );
}
```

## Key Considerations

### 1. StrictMode Compatibility
- **Problem**: StrictMode double-invokes useEffect, causing connection/disconnection cycles
- **Solution**: Singleton pattern keeps connection alive outside React lifecycle
- **Important**: Never use `mountedRef` patterns that block data updates

### 2. State Synchronization
- **Problem**: Singleton state may not sync with React component state
- **Solution**: Use periodic check (500ms interval) to sync states
```typescript
useEffect(() => {
  const checkInterval = setInterval(() => {
    if (service && service.isConnected !== isConnected) {
      setIsConnected(service.isConnected);
    }
  }, 500);

  return () => clearInterval(checkInterval);
}, [service, isConnected]);
```

### 3. Error Handling
- Emit error events from service
- Handle errors in hook and propagate to components
- Clear errors on successful data receipt
- Implement reconnection logic with max attempts

### 4. Memory Management
- Remove event listeners in cleanup functions
- Don't disconnect singleton on component unmount
- Provide reset function for testing

### 5. Type Safety
```typescript
// Define strong types for all data structures
interface WebSocketCommand {
  command: 'start' | 'stop' | 'configure';
  // ... parameters
}

interface WebSocketData {
  timestamp: number;
  samples: number[];
  // ... data fields
}
```

## Common Pitfalls and Solutions

### Pitfall 1: Connection Thrashing
**Issue**: Connection opens and closes repeatedly
**Solution**: Check if already connected before attempting new connection

### Pitfall 2: Lost Events
**Issue**: Events fired before listeners attached
**Solution**: Check service state immediately after mounting

### Pitfall 3: Memory Leaks
**Issue**: Event listeners not cleaned up
**Solution**: Always return cleanup function from useEffect

### Pitfall 4: Stale Closures
**Issue**: Callbacks reference old state values
**Solution**: Use refs for values that shouldn't trigger re-renders

## Testing Approach

### Unit Tests
```typescript
describe('WebSocketService', () => {
  it('should connect to WebSocket server', async () => {
    const service = new WebSocketService();
    await service.connect('ws://localhost:8000');
    expect(service.isConnected).toBe(true);
  });
});
```

### Integration Tests
```typescript
describe('useWebSocket', () => {
  it('should sync with singleton state', () => {
    const { result } = renderHook(() => useWebSocket());
    expect(result.current.isConnected).toBe(false);

    // Simulate connection
    act(() => {
      // ... trigger connection
    });

    expect(result.current.isConnected).toBe(true);
  });
});
```

## File Structure
```
src/features/your-feature/
├── services/
│   ├── websocketService.ts       # WebSocket service class
│   └── websocketSingleton.ts     # Singleton wrapper
├── hooks/
│   └── useWebSocket.ts           # React hook for WebSocket
├── types/
│   └── websocket.types.ts        # TypeScript interfaces
└── components/
    └── YourComponent.tsx          # Component using WebSocket
```

## Backend Integration
Ensure your backend WebSocket endpoint follows the pattern in:
`.ai/templates/websocket-endpoint.py.template`

Key backend considerations:
- Accept JSON commands
- Send JSON data packets
- Handle connection lifecycle
- Implement heartbeat/ping-pong if needed

## Example: Oscilloscope Implementation
See the complete working example in:
- Service: `src/features/demo/services/websocketService.ts`
- Singleton: `src/features/demo/services/websocketSingleton.ts`
- Hook: `src/features/demo/hooks/useWebSocket.ts`
- Usage: `src/features/demo/components/DemoTab/DemoTab.tsx`

This implementation handles:
- Real-time data streaming
- Start/stop commands
- Configuration updates
- Automatic reconnection
- Error recovery

## Debugging Tips

### Check Console Logs
```typescript
console.log('[WebSocket] Connection state:', service.isConnected);
console.log('[Hook] State sync:', { isConnected, service: service.isConnected });
```

### Monitor Network Tab
- Check WebSocket connection in browser DevTools
- Verify messages being sent/received
- Look for connection errors

### Common Issues
1. **Button stays disabled**: Check if service.isConnected is true
2. **No data received**: Verify backend is sending data
3. **Connection drops**: Check for network issues or backend errors

## Additional Resources
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React StrictMode](https://react.dev/reference/react/StrictMode)
- [React Hooks Rules](https://react.dev/reference/rules/rules-of-hooks)
