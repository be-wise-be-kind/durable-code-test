# Racing Game Demo - Detailed PR Breakdown

**Purpose**: Detailed implementation instructions for each pull request in the racing game demo feature

**Scope**: Step-by-step guidance for all 8 PRs required to complete the racing game demo

**Overview**: This document provides comprehensive implementation details for each PR, including specific
    file changes, code examples, testing requirements, and validation criteria. Each PR is designed to be
    independently functional while building toward the complete feature.

---

## PR1: Navigation Dropdown Support

### Overview
Transform the Demo tab into a dropdown menu supporting multiple demo applications.

### Branch
`feat/racing-game-pr1-navigation`

### Files to Modify

#### 1. Update Navigation Types
**File**: `src/features/navigation/types/navigation.types.ts`
```typescript
// Add sub-navigation support
export interface SubTabContent {
  id: string;
  title: string;
  icon?: string;
  description: string;
  component: LazyExoticComponent<ComponentType>;
}

export interface TabContent {
  title: string;
  icon: string;
  description: string;
  component?: LazyExoticComponent<ComponentType>;
  subTabs?: SubTabContent[]; // New: Support for sub-tabs
}
```

#### 2. Create Demo Router Component
**File**: `src/features/demo/components/DemoRouter/DemoRouter.tsx`
```typescript
import { Routes, Route } from 'react-router-dom';
import { OscilloscopeDemo } from '../OscilloscopeDemo';
import { RacingGameDemo } from '../../racing/components/RacingGameTab';

export function DemoRouter() {
  return (
    <Routes>
      <Route path="oscilloscope" element={<OscilloscopeDemo />} />
      <Route path="racing" element={<RacingGameDemo />} />
      <Route index element={<DemoSelector />} />
    </Routes>
  );
}
```

#### 3. Create Demo Selector
**File**: `src/features/demo/components/DemoSelector/DemoSelector.tsx`
```typescript
// Landing page for demo selection with cards for each demo
```

#### 4. Update Tab Configuration
**File**: `src/config/tabs.config.ts`
```typescript
Demo: {
  title: 'Demo',
  icon: '🎮',
  description: 'Interactive demonstrations',
  subTabs: [
    {
      id: 'oscilloscope',
      title: 'Oscilloscope',
      icon: '📊',
      description: 'Real-time waveform visualization',
      component: OscilloscopeDemo,
    },
    {
      id: 'racing',
      title: 'Racing Game',
      icon: '🏎️',
      description: 'Physics-based racing game',
      component: RacingGameDemo,
    },
  ],
}
```

### Testing Requirements
- Navigation dropdown renders correctly
- Sub-navigation items are clickable
- Routing works for each demo
- Back navigation functions properly
- Mobile responsive dropdown

### Success Criteria
- [ ] Demo tab shows dropdown on hover/click
- [ ] Both demos accessible via dropdown
- [ ] URLs reflect current demo
- [ ] Navigation state preserved
- [ ] All existing tests pass

---

## PR2: Basic Physics Foundation

### Overview
Get a basic car moving on a simple track with Matter.js physics engine. This is a minimal viable racing implementation to establish the foundation.

### Branch
`feat/racing-game-pr2-physics`

### Dependencies to Install
```bash
npm install matter-js @types/matter-js --save
```

### New Files to Create

#### 1. Backend Racing API (Simple Track)
**File**: `durable-code-app/backend/app/racing.py`
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/racing", tags=["racing"])

class SimpleTrack(BaseModel):
    width: int = 800
    height: int = 600
    boundaries: list[dict] = []

@router.get("/track/simple")
async def get_simple_track() -> SimpleTrack:
    # Return a basic oval track for testing
    return SimpleTrack(
        boundaries=[
            {"x": 100, "y": 100}, {"x": 700, "y": 100},
            {"x": 700, "y": 500}, {"x": 100, "y": 500}
        ]
    )
```

#### 2. Physics Setup with Matter.js
**File**: `src/features/racing/physics/setup.ts`
```typescript
import Matter from 'matter-js';

export function createPhysicsEngine() {
  const engine = Matter.Engine.create();
  engine.gravity.y = 0; // Top-down view, no gravity

  return engine;
}

export function createCar(x: number, y: number) {
  return Matter.Bodies.rectangle(x, y, 30, 20, {
    frictionAir: 0.05,
    mass: 1,
  });
}
```

#### 3. Basic Racing Game Hook
**File**: `src/features/racing/hooks/useRacingGame.ts`
```typescript
export function useRacingGame() {
  const [engine] = useState(() => createPhysicsEngine());
  const [car] = useState(() => createCar(400, 300));
  const [track, setTrack] = useState(null);

  useEffect(() => {
    // Fetch simple track from backend
    fetch('/api/racing/track/simple')
      .then(res => res.json())
      .then(setTrack);
  }, []);

  useEffect(() => {
    // Basic game loop
    const runner = Matter.Runner.create();
    Matter.Runner.run(runner, engine);

    return () => Matter.Runner.stop(runner);
  }, [engine]);

  return { car, track };
}
```

#### 4. Update RacingGameTab Component
**File**: `src/features/racing/components/RacingGameTab/RacingGameTab.tsx`
```typescript
export function RacingGameTab() {
  const { car, track } = useRacingGame();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Basic rendering
    const canvas = canvasRef.current;
    if (!canvas || !track) return;

    const ctx = canvas.getContext('2d');
    // Draw track boundaries
    // Draw car
  }, [car, track]);

  return <canvas ref={canvasRef} width={800} height={600} />;
}
```

### Testing Requirements
- Backend endpoint returns track data
- Matter.js engine initializes
- Car body is created
- Basic rendering works

### Success Criteria
- [ ] Backend track endpoint working
- [ ] Matter.js installed and configured
- [ ] Car visible on canvas
- [ ] Car responds to physics
- [ ] Basic tests passing

---

## PR3: Track Generation & Rendering

### Overview
Implement backend procedural track generation and frontend rendering with proper collision boundaries.

### Branch
`feat/racing-game-pr3-track`

### New Features

#### 1. Backend Procedural Track Generation
**File**: `durable-code-app/backend/app/racing.py` (update)
```python
@router.post("/track/generate")
async def generate_track(difficulty: str = "medium") -> Track:
    # Generate procedural track with curves, straights
    # Use seed for reproducibility
    # Return track segments and boundaries
    pass
```

#### 2. Track Renderer
**File**: `src/features/racing/rendering/trackRenderer.ts`
```typescript
export function renderTrack(ctx: CanvasRenderingContext2D, track: Track) {
  // Draw track boundaries
  // Draw track surface
  // Draw start/finish line
}
```

#### 3. Collision Boundaries
**File**: `src/features/racing/physics/boundaries.ts`
```typescript
export function createTrackBoundaries(track: Track, engine: Matter.Engine) {
  // Convert track data to Matter.js static bodies
  // Create walls for collision detection
}
```

### Testing Requirements
- Track generation produces valid tracks
- Boundaries align with visual track
- Collision detection works
- Different difficulties produce appropriate tracks

### Success Criteria
- [ ] Backend generates varied tracks
- [ ] Track renders visually
- [ ] Car collides with walls
- [ ] Multiple track layouts available
- [ ] Performance remains good

---

## PR4: Game UI & Controls

### Overview
Implement user interface components, control systems, and game state management.

### Branch
`feat/racing-game-pr4-controls`

### New Components

#### 1. Game Canvas Component
**File**: `src/features/racing/components/GameCanvas/GameCanvas.tsx`
```typescript
export function GameCanvas({ track, car }: GameCanvasProps) {
  // Full canvas implementation
  // Mouse tracking
  // Render loop
  // Input handling
}
```

#### 2. Control Panel
**File**: `src/features/racing/components/ControlPanel/ControlPanel.tsx`
```typescript
export function ControlPanel({ onStart, onPause, onReset }: ControlPanelProps) {
  // Start/Pause/Reset buttons
  // Difficulty selector
  // Instructions display
}
```

#### 3. Status Display
**File**: `src/features/racing/components/StatusDisplay/StatusDisplay.tsx`
```typescript
export function StatusDisplay({ speed, time }: StatusDisplayProps) {
  // Speed indicator
  // Time display
  // Current lap
}
```

#### 4. Game State Management
**File**: `src/features/racing/utils/gameState.ts`
```typescript
export class GameStateManager {
  // Menu -> Racing -> Paused -> Finished transitions
  // State persistence
  // Event handling
}
```

### Testing Requirements
- UI components render correctly
- Controls are responsive
- State transitions work
- Canvas updates smoothly

### Success Criteria
- [ ] Canvas displays game properly
- [ ] Controls work intuitively
- [ ] Status updates in real-time
- [ ] Game states transition smoothly
- [ ] UI is responsive on all screens

---

## PR5: Advanced Car Physics

### Overview
Implement realistic car physics with proper steering mechanics, rear-wheel pivot point, drift mechanics, and improved handling model.

### Branch
`feat/racing-game-pr5-physics`

### Physics Improvements

#### 1. Realistic Steering Model
**File**: `src/features/racing/physics/carPhysics.ts`
```typescript
export class CarPhysicsModel {
  // Rear-wheel pivot point (car rotates around rear axle, not center)
  // Front-wheel steering angle calculation
  // Ackermann steering geometry
  // Speed-dependent steering sensitivity
}
```

#### 2. Drift Mechanics
**File**: `src/features/racing/physics/driftMechanics.ts`
```typescript
export class DriftSystem {
  // Tire grip calculation
  // Slip angle simulation
  // Counter-steering detection
  // Drift scoring (optional)
}
```

#### 3. Advanced Forces
**File**: `src/features/racing/physics/forces.ts`
```typescript
export class ForceSystem {
  // Weight transfer (acceleration/braking)
  // Lateral forces (cornering)
  // Traction control
  // Downforce (at high speeds)
}
```

#### 4. Tire Model
**File**: `src/features/racing/physics/tireModel.ts`
```typescript
export interface TireModel {
  // Friction circle
  // Temperature simulation
  // Wear model (optional)
  // Surface interaction
}
```

### Implementation Details

#### Rear-Wheel Pivot Point
- Calculate steering based on front wheel angle
- Apply forces at rear axle position
- Rotate car body around rear pivot point
- Adjust turning radius based on wheelbase

#### Improved Handling
- Speed-dependent steering (tighter at low speed, wider at high speed)
- Momentum preservation during turns
- Realistic acceleration/deceleration curves
- Better collision response

### Testing Requirements
- Car handles realistically at different speeds
- Turning feels natural and intuitive
- Drift mechanics work smoothly
- No physics glitches or unrealistic behavior

### Success Criteria
- [ ] Car pivots around rear axle
- [ ] Steering angle affects turn radius correctly
- [ ] Speed influences handling appropriately
- [ ] Drift mechanics implemented
- [ ] Physics feel responsive and fun
- [ ] No performance degradation

---

## PR6: Timing & Scoring System

### Overview
Implement checkpoint system, lap timing, best time tracking, and race completion logic.

### Branch
`feat/racing-game-pr6-scoring`

### New Systems

#### 1. Timing System
**File**: `src/features/racing/utils/timing.ts`
```typescript
export class TimingSystem {
  // Start/stop timer
  // Lap timing
  // Best time tracking
  // Checkpoint validation
}
```

#### 2. Checkpoint System
**File**: `src/features/racing/utils/checkpoints.ts`
```typescript
export class CheckpointManager {
  // Checkpoint detection
  // Order validation
  // Progress tracking
  // Lap completion
}
```

#### 3. Scoring Display
**File**: `src/features/racing/components/ScoreBoard/ScoreBoard.tsx`
```typescript
export function ScoreBoard({ currentTime, bestTime, lap }: ScoreBoardProps) {
  // Current time display
  // Best time comparison
  // Lap counter
  // Finish celebration
}
```

### Testing Requirements
- Timer accuracy
- Checkpoint detection reliability
- Score persistence
- Edge cases handled

### Success Criteria
- [ ] Timer works accurately
- [ ] Checkpoints detect properly
- [ ] Lap times tracked
- [ ] Best times saved
- [ ] Finish line works

---

## PR7: Polish & Effects

### Overview
Add visual effects, particle systems, and performance optimizations to enhance gameplay experience.

### Branch
`feat/racing-game-pr7-polish`

### Enhancements

#### 1. Particle Effects
**File**: `src/features/racing/effects/particles.ts`
```typescript
export class ParticleSystem {
  // Dust particles
  // Exhaust smoke
  // Collision sparks
  // Object pooling
}
```

#### 2. Visual Effects
**File**: `src/features/racing/effects/visualEffects.ts`
```typescript
export class VisualEffects {
  // Skid marks
  // Speed lines
  // Motion blur
  // Screen shake
}
```

#### 3. Sound Effects (Optional)
**File**: `src/features/racing/audio/soundManager.ts`
```typescript
export class SoundManager {
  // Engine sounds
  // Collision sounds
  // UI feedback
  // Background music
}
```

#### 4. Performance Optimizations
**File**: `src/features/racing/utils/optimization.ts`
```typescript
export class RenderOptimizer {
  // Dirty rectangle rendering
  // Layer caching
  // Object pooling
  // Frame rate limiting
}
```

### Visual Improvements
- Smooth camera following
- Track shadows
- Animated countdown
- Victory celebration
- UI animations

### Performance Targets
- Maintain 60 FPS
- < 50MB memory usage
- Smooth on mobile devices

### Success Criteria
- [ ] Particle effects working
- [ ] Visual polish added
- [ ] Performance maintained
- [ ] Mobile responsive
- [ ] Effects enhance gameplay

---

## PR8: Security Review & Hardening

### Overview
Comprehensive security audit, vulnerability scanning, and implementation of security best practices.

### Branch
`feat/racing-game-pr8-security`

### Security Tasks

#### 1. Security Audit
**Areas to Review**:
- Input validation (mouse coordinates, API parameters)
- API rate limiting verification
- XSS prevention in canvas rendering
- CORS configuration
- WebSocket security (for future multiplayer)
- Dependency vulnerabilities

#### 2. Input Sanitization
**File**: `src/features/racing/security/inputValidator.ts`
```typescript
export class InputValidator {
  // Validate mouse coordinates
  // Sanitize track parameters
  // Prevent injection attacks
  // Boundary checking
}
```

#### 3. API Security
**File**: `durable-code-app/backend/app/racing.py` (update)
```python
# Add rate limiting
# Input validation with Pydantic
# Error message sanitization
# Request size limits
```

#### 4. Frontend Security
- Content Security Policy headers
- Secure canvas operations
- Memory leak prevention
- Resource cleanup

### Security Testing
- Penetration testing
- Fuzzing inputs
- Performance DoS prevention
- Dependency scanning

### Success Criteria
- [ ] No known vulnerabilities
- [ ] Input validation complete
- [ ] Rate limiting working
- [ ] Security tests passing
- [ ] Documentation updated

---

## PR8: Testing & Documentation

### Overview
Comprehensive testing suite and complete documentation for the racing game feature.

### Branch
`feat/racing-game-pr8-testing`

### Testing Coverage

#### 1. Unit Tests
**Frontend Tests**:
- Physics calculations
- Track generation
- Game state management
- Component rendering
- Utility functions

**Backend Tests**:
- API endpoints
- Track generation
- Validation logic
- Error handling

#### 2. Integration Tests
- Full game flow
- API integration
- State persistence
- Performance benchmarks

#### 3. Security Tests
- Input validation
- API security
- XSS prevention
- Rate limiting

### Documentation

#### 1. User Documentation
**File**: `docs/racing-game-user-guide.md`
- How to play
- Controls reference
- Features overview
- Troubleshooting

#### 2. Developer Documentation
**File**: `src/features/racing/README.md`
- Architecture overview
- API reference
- Adding features
- Performance tips

#### 3. Security Documentation
**File**: `docs/racing-game-security.md`
- Security measures
- Threat model
- Best practices
- Incident response

### Success Criteria
- [ ] 80%+ test coverage
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Security tests passing
- [ ] Performance benchmarks met

---

## 🚀 Deployment Checklist

After all PRs are complete:

### Final Integration
1. [ ] Merge all PRs to main
2. [ ] Run full test suite
3. [ ] Performance validation
4. [ ] Cross-browser testing
5. [ ] Mobile responsiveness check

### Documentation Update
1. [ ] Update main README
2. [ ] Add to feature showcase
3. [ ] Create demo video/GIF
4. [ ] Update roadmap status

### Release
1. [ ] Tag release version
2. [ ] Deploy to production
3. [ ] Announce feature completion
4. [ ] Move roadmap item to complete

---

**Document Version**: 1.0.0
**Last Updated**: 2025-09-28
**Status**: Ready for Implementation