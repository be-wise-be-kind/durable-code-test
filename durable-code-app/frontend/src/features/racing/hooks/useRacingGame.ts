/**
 * Purpose: Racing game hook for state management and game loop
 * Scope: Complete racing game state and physics management
 * Overview: Manages game state, physics engine, track loading, and rendering loop
 * Dependencies: React, Matter.js, racing types, physics setup
 * Exports: useRacingGame hook
 * Implementation: React hook with Matter.js integration and game loop
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import Matter from 'matter-js';
import type {
  CarState,
  InputState,
  PhysicsWorld,
  Track,
  UseRacingGameReturn,
} from '../types/racing.types';
import { GameState } from '../types/racing.types';
import {
  applyCarForces,
  createCar,
  createPhysicsEngine,
  createTrackWalls,
  getCarState,
} from '../physics/setup';
import {
  renderBackground,
  renderCar,
  renderDebugInfo,
  renderTrack,
} from '../rendering/trackRenderer';
import { SoundManager } from '../audio/soundManager';
import { TimingSystem } from '../utils/timing';
import { CheckpointManager } from '../utils/checkpoints';
import { logger } from '../../../utils/logger';
import { validateTrack } from '../types/track.schema';

// Constants
const CANVAS_WIDTH = 1200; // Larger canvas for bigger track
const CANVAS_HEIGHT = 900; // Larger canvas for bigger track
const TARGET_FPS = 60;
const PHYSICS_TIMESTEP = 1000 / TARGET_FPS;

// Initial states
const initialCarState: CarState = {
  x: CANVAS_WIDTH / 2,
  y: CANVAS_HEIGHT - 100,
  angle: 0,
  velocityX: 0,
  velocityY: 0,
  angularVelocity: 0,
  speed: 0,
};

const initialInputState: InputState = {
  mouseX: 0,
  mouseY: 0,
  leftMouseDown: false,
  rightMouseDown: false,
  keys: new Set(),
};

/**
 * Racing game hook for managing game state and physics
 *
 * @returns Racing game state and control functions
 */
export function useRacingGame(): UseRacingGameReturn {
  // Game state
  const [gameState, setGameState] = useState<GameState>(GameState.MENU);
  const [track, setTrack] = useState<Track | null>(null);
  const [carState, setCarState] = useState<CarState>(initialCarState);
  const [inputState, setInputState] = useState<InputState>(initialInputState);
  const [isLoadingTrack, setIsLoadingTrack] = useState(false);
  const [trackError, setTrackError] = useState<string | null>(null);

  // Refs for physics and rendering
  const physicsWorldRef = useRef<PhysicsWorld | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number>(0);
  const inputStateRef = useRef<InputState>(initialInputState);
  const soundManagerRef = useRef<SoundManager | null>(null);
  const lastSpeedRef = useRef<number>(0);
  const timingSystemRef = useRef<TimingSystem>(new TimingSystem());
  const checkpointManagerRef = useRef<CheckpointManager>(new CheckpointManager());

  // Lap and timing state
  const [currentLapNumber, setCurrentLapNumber] = useState<number>(1);
  const [currentLapTime, setCurrentLapTime] = useState<number>(0);
  const [bestLapTime, setBestLapTime] = useState<number | null>(null);
  const [wrongWayWarning, setWrongWayWarning] = useState<boolean>(false);

  // Track loading function
  const loadTrack = useCallback(async () => {
    setIsLoadingTrack(true);
    setTrackError(null);

    try {
      // Use procedural track generation for more interesting layouts
      const response = await fetch('/api/racing/track/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          difficulty: 'medium',
          width: CANVAS_WIDTH,
          height: CANVAS_HEIGHT,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to load track: ${response.statusText}`);
      }

      const rawTrackData = await response.json();
      try {
        const trackData = validateTrack(rawTrackData);
        setTrack(trackData);
      } catch (validationError) {
        logger.error('Invalid track data received from server:', validationError);
        throw new Error('Received invalid track data from server');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setTrackError(errorMessage);
      logger.error('Failed to load track:', error);
    } finally {
      setIsLoadingTrack(false);
    }
  }, []);

  // Initialize physics world
  const initializePhysicsWorld = useCallback((trackData: Track) => {
    if (!trackData) return null;

    const engine = createPhysicsEngine();
    const car = createCar(trackData.start_position.x, trackData.start_position.y);

    // Create walls from track boundaries
    const outerWalls = createTrackWalls(trackData.boundaries.outer);
    const innerWalls = createTrackWalls(trackData.boundaries.inner);
    const walls = [...outerWalls, ...innerWalls];

    // Add bodies to the world
    Matter.World.add(engine.world, [car, ...walls]);

    return { engine, car, walls };
  }, []);

  // Rendering function
  const renderGame = useCallback(
    (canvas: HTMLCanvasElement, world: PhysicsWorld, trackData: Track) => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Clear and draw background
      renderBackground(ctx, canvas.width, canvas.height);

      // Draw track
      renderTrack(ctx, trackData);

      // Draw car with speed for visual effects
      const { car } = world;
      const speed = Math.sqrt(car.velocity.x ** 2 + car.velocity.y ** 2);
      renderCar(ctx, car.position.x, car.position.y, car.angle, speed);

      // Draw debug info
      renderDebugInfo(ctx, speed, { x: car.position.x, y: car.position.y });
    },
    [],
  );

  // Game loop
  const gameLoop = useCallback(
    (timestamp: number) => {
      if (!physicsWorldRef.current || gameState !== GameState.RACING) {
        return;
      }

      const deltaTime = timestamp - lastTimeRef.current;
      lastTimeRef.current = timestamp;

      // Update physics (fixed timestep for consistency)
      if (deltaTime >= PHYSICS_TIMESTEP) {
        const { engine, car } = physicsWorldRef.current;
        const input = inputStateRef.current;

        // Store velocity before physics update for collision detection
        const velocityBefore = Math.sqrt(car.velocity.x ** 2 + car.velocity.y ** 2);

        // Check for finish line crossing
        const checkpointResult = checkpointManagerRef.current.checkFinishLineCrossing({
          x: car.position.x,
          y: car.position.y,
        });

        // Update wrong way warning
        setWrongWayWarning(checkpointResult.wrongWayWarning);

        // If lap completed, update timing
        if (checkpointResult.isValidLap) {
          timingSystemRef.current.completeLap();
          setBestLapTime(timingSystemRef.current.getBestLapTime());
          setCurrentLapNumber(timingSystemRef.current.getCurrentLapNumber());
        }

        // Apply forces based on input (with wrong-way resistance)
        applyCarForces(
          car,
          input.mouseX,
          input.mouseY,
          input.leftMouseDown,
          input.rightMouseDown,
          checkpointResult.wrongWayWarning,
        );

        // Update physics engine
        Matter.Engine.update(engine, PHYSICS_TIMESTEP);

        // Check for collisions (significant velocity change)
        const velocityAfter = Math.sqrt(car.velocity.x ** 2 + car.velocity.y ** 2);
        const velocityChange = Math.abs(velocityBefore - velocityAfter);

        if (velocityChange > 1.0 && soundManagerRef.current) {
          // Collision detected - play sound based on impact strength
          const intensity = Math.min(1, velocityChange / 5);
          soundManagerRef.current.playCollisionSound(intensity);
        }

        // Update car state
        const newCarState = getCarState(car);
        setCarState(newCarState);

        // Update current lap time for display
        setCurrentLapTime(timingSystemRef.current.getCurrentLapTime());

        // Update engine sound based on speed
        if (soundManagerRef.current) {
          soundManagerRef.current.updateEngineSound(newCarState.speed);
          lastSpeedRef.current = newCarState.speed;
        }
      }

      // Render if canvas is available
      if (canvasRef.current && track) {
        renderGame(canvasRef.current, physicsWorldRef.current, track);
      }

      // Continue game loop
      animationFrameRef.current = requestAnimationFrame(gameLoop);
    },
    [gameState, track, renderGame],
  );

  // Mouse event handlers
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    const newState = {
      ...inputStateRef.current,
      mouseX,
      mouseY,
    };
    inputStateRef.current = newState;
    setInputState(newState);
  }, []);

  const handleMouseDown = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    const isLeftClick = event.button === 0;
    const isRightClick = event.button === 2;

    const newState = {
      ...inputStateRef.current,
      leftMouseDown: isLeftClick ? true : inputStateRef.current.leftMouseDown,
      rightMouseDown: isRightClick ? true : inputStateRef.current.rightMouseDown,
    };
    inputStateRef.current = newState;
    setInputState(newState);
  }, []);

  const handleMouseUp = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const isLeftClick = event.button === 0;
    const isRightClick = event.button === 2;

    const newState = {
      ...inputStateRef.current,
      leftMouseDown: isLeftClick ? false : inputStateRef.current.leftMouseDown,
      rightMouseDown: isRightClick ? false : inputStateRef.current.rightMouseDown,
    };
    inputStateRef.current = newState;
    setInputState(newState);
  }, []);

  // Game control functions
  const startGame = useCallback(async () => {
    if (!track) {
      await loadTrack();
      return;
    }

    const world = initializePhysicsWorld(track);
    if (!world) {
      logger.error('Failed to initialize physics world');
      return;
    }

    physicsWorldRef.current = world;
    setCarState(getCarState(world.car));

    // Initialize checkpoint system with finish line
    checkpointManagerRef.current.setupFinishLine(
      track.start_position,
      track.track_width,
      track.boundaries,
    );

    // Initialize and start timing system
    timingSystemRef.current.start();
    setCurrentLapNumber(1);
    setCurrentLapTime(0);
    setBestLapTime(null);
    setWrongWayWarning(false);

    // Initialize and start sound
    if (!soundManagerRef.current) {
      soundManagerRef.current = new SoundManager();
    }
    soundManagerRef.current.initialize();
    soundManagerRef.current.startEngine();

    // Start game loop BEFORE setting state so gameLoop has the right state
    lastTimeRef.current = performance.now();

    // Set state which will cause gameLoop to re-render with correct dependencies
    setGameState(GameState.RACING);
  }, [track, loadTrack, initializePhysicsWorld]);

  const pauseGame = useCallback(() => {
    const isPausing = gameState === GameState.RACING;
    setGameState((prev) =>
      prev === GameState.RACING ? GameState.PAUSED : GameState.RACING,
    );

    // Stop or restart timing when pausing/unpausing
    if (isPausing) {
      timingSystemRef.current.stop();
    } else {
      timingSystemRef.current.start();
    }

    // Stop or restart engine sound when pausing/unpausing
    if (soundManagerRef.current) {
      if (isPausing) {
        soundManagerRef.current.stopEngine();
      } else {
        soundManagerRef.current.startEngine();
      }
    }
  }, [gameState]);

  const resetGame = useCallback(() => {
    // Stop game loop
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Stop and dispose sound
    if (soundManagerRef.current) {
      soundManagerRef.current.dispose();
      soundManagerRef.current = null;
    }

    // Reset timing and checkpoints
    timingSystemRef.current.reset();
    checkpointManagerRef.current.reset();
    setCurrentLapNumber(1);
    setCurrentLapTime(0);
    setBestLapTime(null);
    setWrongWayWarning(false);

    // Reset state
    setGameState(GameState.MENU);
    setCarState(initialCarState);
    setInputState(initialInputState);
    physicsWorldRef.current = null;
  }, []);

  // Regenerate track with custom parameters
  const regenerateTrack = useCallback(
    async (params?: {
      numPoints?: number;
      variationAmount?: number;
      hairpinChance?: number;
      hairpinIntensity?: number;
      smoothingPasses?: number;
      trackWidth?: number;
      seed?: number;
    }) => {
      setIsLoadingTrack(true);
      setTrackError(null);

      try {
        const response = await fetch('/api/racing/track/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            difficulty: 'medium',
            width: CANVAS_WIDTH,
            height: CANVAS_HEIGHT,
            num_points: params?.numPoints,
            variation_amount: params?.variationAmount,
            hairpin_chance: params?.hairpinChance,
            hairpin_intensity: params?.hairpinIntensity,
            smoothing_passes: params?.smoothingPasses,
            track_width_override: params?.trackWidth,
            seed: params?.seed,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to generate track: ${response.statusText}`);
        }

        const rawTrackData = await response.json();
        try {
          const trackData = validateTrack(rawTrackData);
          setTrack(trackData);
        } catch (validationError) {
          logger.error('Invalid track data received from server:', validationError);
          throw new Error('Received invalid track data from server');
        }

        // Reset game state when track changes
        setGameState(GameState.MENU);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        setTrackError(errorMessage);
        logger.error('Failed to generate track:', error);
      } finally {
        setIsLoadingTrack(false);
      }
    },
    [],
  );

  // Load track on mount
  useEffect(() => {
    loadTrack();
  }, [loadTrack]);

  // Setup canvas event listeners
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Prevent context menu on right click
    const preventContextMenu = (e: Event) => e.preventDefault();
    canvas.addEventListener('contextmenu', preventContextMenu);

    return () => {
      canvas.removeEventListener('contextmenu', preventContextMenu);
    };
  }, []);

  // Start/stop game loop based on game state
  useEffect(() => {
    if (gameState === GameState.RACING && !animationFrameRef.current) {
      // Start game loop
      animationFrameRef.current = requestAnimationFrame(gameLoop);
    } else if (gameState !== GameState.RACING && animationFrameRef.current) {
      // Stop game loop
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, [gameState, gameLoop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (soundManagerRef.current) {
        soundManagerRef.current.dispose();
      }
    };
  }, []);

  return {
    gameState,
    track,
    carState,
    inputState,
    startGame,
    pauseGame,
    resetGame,
    regenerateTrack,
    isLoadingTrack,
    trackError,
    canvasRef,
    currentLapNumber,
    currentLapTime,
    bestLapTime,
    wrongWayWarning,
    // Canvas event handlers
    onMouseMove: handleMouseMove,
    onMouseDown: handleMouseDown,
    onMouseUp: handleMouseUp,
  };
}
