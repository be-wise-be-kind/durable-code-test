/**
 * Purpose: Sound effects manager for racing game
 * Scope: Engine sounds, collision sounds, and audio management
 * Overview: Supports both real audio files and synthetic audio generation.
 *           Automatically falls back to synthesized audio if files are unavailable.
 * Dependencies: Web Audio API
 * Exports: SoundManager class
 * Implementation: Hybrid audio system with real samples and procedural synthesis
 */

/**
 * Audio file configuration
 */
interface AudioFile {
  path: string;
  loop: boolean;
  volume: number;
}

/**
 * Sound manager for racing game audio effects with real audio file support
 */
export class SoundManager {
  private audioContext: AudioContext | null = null;
  private engineOscillator: OscillatorNode | null = null;
  private engineOscillator2: OscillatorNode | null = null;
  private modulatorOscillator: OscillatorNode | null = null;
  private modulatorGain: GainNode | null = null;
  private engineGain: GainNode | null = null;
  private isEngineRunning = false;
  private masterGain: GainNode | null = null;

  // Real audio file support
  private audioBuffers: Map<string, AudioBuffer> = new Map();
  private activeAudioSources: Map<string, AudioBufferSourceNode> = new Map();
  private useRealAudio = false;
  private engineSource: AudioBufferSourceNode | null = null;
  private engineSourceGain: GainNode | null = null;

  // Audio file paths
  private readonly audioFiles: Record<string, AudioFile> = {
    engineIdle: { path: '/audio/racing/engine-idle.mp3', loop: true, volume: 0.4 },
    engineRev: { path: '/audio/racing/engine-rev.mp3', loop: false, volume: 0.6 },
    engineHigh: { path: '/audio/racing/engine-high.mp3', loop: true, volume: 0.5 },
    tireScreech: { path: '/audio/racing/tire-screech.mp3', loop: false, volume: 0.7 },
    collision: { path: '/audio/racing/collision.mp3', loop: false, volume: 0.8 },
    gearShift: { path: '/audio/racing/gear-shift.mp3', loop: false, volume: 0.5 },
  };

  /**
   * Initialize the audio context and attempt to load real audio files
   */
  public async initialize(): Promise<void> {
    if (this.audioContext) return;

    try {
      this.audioContext = new (window.AudioContext ||
        (window as Window & { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext)();

      // Master gain for overall volume control
      this.masterGain = this.audioContext.createGain();
      this.masterGain.gain.value = 0.3; // 30% volume
      this.masterGain.connect(this.audioContext.destination);

      // Try to load real audio files
      await this.loadAudioFiles();

      // If real audio failed, fallback to synthesized
      if (!this.useRealAudio) {
        this.setupEngineSound();
      }
    } catch (error) {
      console.warn('Web Audio API not supported:', error);
    }
  }

  /**
   * Attempt to load real audio files
   */
  private async loadAudioFiles(): Promise<void> {
    if (!this.audioContext) return;

    try {
      const loadPromises = Object.entries(this.audioFiles).map(
        async ([key, config]) => {
          try {
            const response = await fetch(config.path);
            if (!response.ok) throw new Error(`Failed to load ${config.path}`);

            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext?.decodeAudioData(arrayBuffer);
            if (audioBuffer) {
              this.audioBuffers.set(key, audioBuffer);
            }
            return true;
          } catch {
            return false;
          }
        },
      );

      await Promise.all(loadPromises);
      // Use real audio if we successfully loaded at least the engine sounds
      this.useRealAudio =
        this.audioBuffers.has('engineIdle') ||
        this.audioBuffers.has('engineRev') ||
        this.audioBuffers.has('engineHigh');
    } catch {
      this.useRealAudio = false;
    }
  }

  /**
   * Play a real audio buffer
   */
  private playAudioBuffer(key: string, config: AudioFile): void {
    if (!this.audioContext || !this.masterGain) return;

    const buffer = this.audioBuffers.get(key);
    if (!buffer) return;

    // Stop existing instance if playing
    const existing = this.activeAudioSources.get(key);
    if (existing) {
      try {
        existing.stop();
      } catch {
        // Already stopped
      }
      this.activeAudioSources.delete(key);
    }

    // Create new source
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.loop = config.loop;

    // Create gain node for this source
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = config.volume;

    // Connect: source -> gain -> master -> destination
    source.connect(gainNode);
    gainNode.connect(this.masterGain);

    // Play
    source.start(0);
    this.activeAudioSources.set(key, source);

    // Cleanup when finished (for non-looping sounds)
    if (!config.loop) {
      source.onended = () => {
        this.activeAudioSources.delete(key);
      };
    }
  }

  /**
   * Setup engine sound with modulation for realistic motor rumble
   */
  private setupEngineSound(): void {
    if (!this.audioContext || !this.masterGain) return;

    // Create low-frequency modulator for engine rumble (gives it that throaty sound)
    this.modulatorOscillator = this.audioContext.createOscillator();
    this.modulatorOscillator.type = 'sine';
    this.modulatorOscillator.frequency.value = 30; // Deep rumble modulation

    this.modulatorGain = this.audioContext.createGain();
    this.modulatorGain.gain.value = 20; // Modulation depth

    // Connect modulator to control main oscillator frequency
    this.modulatorOscillator.connect(this.modulatorGain);

    // Create main engine oscillator (lower frequency for deeper sound)
    this.engineOscillator = this.audioContext.createOscillator();
    this.engineOscillator.type = 'sawtooth'; // Rich, engine-like sound
    this.engineOscillator.frequency.value = 50; // Lower base frequency (was 80)

    // Connect modulator to main oscillator frequency
    this.modulatorGain.connect(this.engineOscillator.frequency);

    // Create second oscillator for harmonic richness
    this.engineOscillator2 = this.audioContext.createOscillator();
    this.engineOscillator2.type = 'square';
    this.engineOscillator2.frequency.value = 100; // Octave above main

    // Create gain node for engine volume
    this.engineGain = this.audioContext.createGain();
    this.engineGain.gain.value = 0; // Start silent

    // Connect: oscillators -> gain -> master -> destination
    this.engineOscillator.connect(this.engineGain);
    this.engineOscillator2.connect(this.engineGain);
    this.engineGain.connect(this.masterGain);
  }

  /**
   * Start engine sound (real audio or synthesized)
   */
  public startEngine(): void {
    if (!this.audioContext || this.isEngineRunning) return;

    try {
      // Resume audio context if suspended (browser autoplay policy)
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      if (this.useRealAudio) {
        // Use real audio file
        this.playAudioBuffer('engineIdle', this.audioFiles.engineIdle);
        this.engineSource = this.activeAudioSources.get('engineIdle') || null;
      } else {
        // Use synthesized audio - recreate oscillators if they were stopped
        if (
          !this.engineOscillator ||
          !this.engineOscillator2 ||
          !this.modulatorOscillator
        ) {
          this.setupEngineSound();
        }

        // Start oscillators if not already started
        try {
          this.modulatorOscillator?.start();
          this.engineOscillator?.start();
          this.engineOscillator2?.start();
        } catch {
          // Oscillators already started, recreate them
          this.setupEngineSound();
          this.modulatorOscillator?.start();
          this.engineOscillator?.start();
          this.engineOscillator2?.start();
        }
      }
      this.isEngineRunning = true;
    } catch (error) {
      console.warn('Failed to start engine sound:', error);
    }
  }

  /**
   * Stop engine sound
   */
  public stopEngine(): void {
    if (!this.isEngineRunning) return;

    try {
      if (this.useRealAudio) {
        // Stop real audio
        const engineSource = this.activeAudioSources.get('engineIdle');
        if (engineSource) {
          engineSource.stop();
          this.activeAudioSources.delete('engineIdle');
        }
      } else {
        // Fade out synthesized audio
        if (this.audioContext && this.engineGain) {
          this.engineGain.gain.setTargetAtTime(0, this.audioContext.currentTime, 0.1);

          // Stop oscillators after fade
          setTimeout(() => {
            try {
              this.modulatorOscillator?.stop();
              this.engineOscillator?.stop();
              this.engineOscillator2?.stop();
            } catch {
              // Already stopped
            }
            // Clear references so they can be recreated
            this.modulatorOscillator = null;
            this.engineOscillator = null;
            this.engineOscillator2 = null;
          }, 200);
        }
      }
    } catch (error) {
      console.warn('Failed to stop engine sound:', error);
    }

    this.isEngineRunning = false;
  }

  /**
   * Update engine sound based on speed
   *
   * @param speed Current car speed
   */
  public updateEngineSound(speed: number): void {
    if (
      !this.audioContext ||
      !this.engineOscillator ||
      !this.engineOscillator2 ||
      !this.modulatorOscillator ||
      !this.engineGain ||
      !this.isEngineRunning
    ) {
      return;
    }

    const now = this.audioContext.currentTime;

    // Map speed to frequency (lower range for deeper sound: 50Hz idle to 200Hz max)
    const minFreq = 50;
    const maxFreq = 200;
    const frequency = minFreq + (speed / 10) * (maxFreq - minFreq);
    const targetFreq = Math.min(maxFreq, Math.max(minFreq, frequency));

    this.engineOscillator.frequency.setTargetAtTime(targetFreq, now, 0.1);
    this.engineOscillator2.frequency.setTargetAtTime(targetFreq * 2, now, 0.1);

    // Increase modulation rate with speed for more aggressive sound
    const modulationFreq = 30 + (speed / 10) * 20; // 30Hz to 50Hz
    this.modulatorOscillator.frequency.setTargetAtTime(modulationFreq, now, 0.1);

    // Map speed to volume (0.15 idle to 0.6 max for more presence)
    const minVolume = 0.15;
    const maxVolume = 0.6;
    const volume = minVolume + (speed / 10) * (maxVolume - minVolume);
    this.engineGain.gain.setTargetAtTime(
      Math.min(maxVolume, Math.max(minVolume, volume)),
      now,
      0.05,
    );
  }

  /**
   * Play collision sound effect (real audio or synthesized)
   *
   * @param intensity Collision intensity (0-1)
   */
  public playCollisionSound(intensity: number = 0.5): void {
    if (!this.audioContext || !this.masterGain) return;

    try {
      if (this.useRealAudio && this.audioBuffers.has('collision')) {
        // Use real collision sound
        this.playAudioBuffer('collision', this.audioFiles.collision);
      } else {
        // Use synthesized crash sound
        const now = this.audioContext.currentTime;

        // Create noise buffer for crash sound
        const duration = 0.2;
        const sampleRate = this.audioContext.sampleRate;
        const bufferSize = sampleRate * duration;
        const buffer = this.audioContext.createBuffer(1, bufferSize, sampleRate);
        const data = buffer.getChannelData(0);

        // Generate white noise with decay
        for (let i = 0; i < bufferSize; i++) {
          const decay = 1 - i / bufferSize;
          data[i] = (Math.random() * 2 - 1) * decay;
        }

        // Create buffer source
        const noise = this.audioContext.createBufferSource();
        noise.buffer = buffer;

        // Create filter for metallic crash sound
        const filter = this.audioContext.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = 800; // Metallic frequency
        filter.Q.value = 2;

        // Create gain for collision volume
        const collisionGain = this.audioContext.createGain();
        collisionGain.gain.value = Math.min(1, intensity) * 0.8;

        // Connect: noise -> filter -> gain -> master -> destination
        noise.connect(filter);
        filter.connect(collisionGain);
        collisionGain.connect(this.masterGain);

        // Play and cleanup
        noise.start(now);
        noise.stop(now + duration);
      }
    } catch (error) {
      console.warn('Failed to play collision sound:', error);
    }
  }

  /**
   * Play tire screech sound effect
   */
  public playTireScreech(): void {
    if (this.useRealAudio && this.audioBuffers.has('tireScreech')) {
      this.playAudioBuffer('tireScreech', this.audioFiles.tireScreech);
    }
  }

  /**
   * Cleanup and dispose audio resources
   */
  public dispose(): void {
    this.stopEngine();

    // Stop all active audio sources
    this.activeAudioSources.forEach((source) => {
      try {
        source.stop();
      } catch {
        // Already stopped
      }
    });
    this.activeAudioSources.clear();

    if (this.isEngineRunning) {
      try {
        if (this.engineOscillator) this.engineOscillator.stop();
        if (this.engineOscillator2) this.engineOscillator2.stop();
        if (this.modulatorOscillator) this.modulatorOscillator.stop();
      } catch {
        // Already stopped
      }
    }

    if (this.audioContext) {
      try {
        this.audioContext.close();
      } catch {
        // Already closed
      }
    }

    this.audioContext = null;
    this.engineOscillator = null;
    this.engineOscillator2 = null;
    this.modulatorOscillator = null;
    this.modulatorGain = null;
    this.engineGain = null;
    this.masterGain = null;
    this.isEngineRunning = false;
    this.engineSource = null;
    this.engineSourceGain = null;
    this.audioBuffers.clear();
  }

  /**
   * Set master volume
   *
   * @param volume Volume level (0-1)
   */
  public setVolume(volume: number): void {
    if (this.masterGain) {
      this.masterGain.gain.value = Math.max(0, Math.min(1, volume));
    }
  }
}
