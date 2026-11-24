import React, {
  useEffect,
  useRef,
  useState,
  useImperativeHandle,
  forwardRef,
  useCallback,
} from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  RotateCw,
  Volume2,
  VolumeX,
  Radio,
  SlidersHorizontal,
  Check,
} from 'lucide-react';

export interface AudioPlayerRef {
  seekTo: (timeSec: number, autoPlay?: boolean) => void;
  play: () => void;
  pause: () => void;
  getCurrentTime: () => number;
}

export interface AudioPlayerProps {
  callId: string;
  durationMs?: number;
  onTimeUpdate?: (currentTimeMs: number) => void;
  onPlayStateChange?: (isPlaying: boolean) => void;
  autoScroll?: boolean;
  onToggleAutoScroll?: () => void;
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return '00:00';
  const totalSec = Math.floor(seconds);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const AudioPlayer = forwardRef<AudioPlayerRef, AudioPlayerProps>(
  (
    {
      callId,
      durationMs,
      onTimeUpdate,
      onPlayStateChange,
      autoScroll = true,
      onToggleAutoScroll,
    },
    ref
  ) => {
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(durationMs ? durationMs / 1000 : 0);
    const [playbackRate, setPlaybackRate] = useState(1);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [isLoaded, setIsLoaded] = useState(false);
    const [audioError, setAudioError] = useState<string | null>(null);

    const audioUrl = `/api/v1/calls/${callId}/audio`;

    // Expose imperative control handle
    useImperativeHandle(ref, () => ({
      seekTo: (timeSec: number, autoPlay: boolean = true) => {
        if (!audioRef.current) return;
        audioRef.current.currentTime = timeSec;
        setCurrentTime(timeSec);
        if (autoPlay) {
          audioRef.current
            .play()
            .then(() => {
              setIsPlaying(true);
              onPlayStateChange?.(true);
            })
            .catch(() => {});
        }
      },
      play: () => {
        audioRef.current?.play().then(() => {
          setIsPlaying(true);
          onPlayStateChange?.(true);
        });
      },
      pause: () => {
        audioRef.current?.pause();
        setIsPlaying(false);
        onPlayStateChange?.(false);
      },
      getCurrentTime: () => audioRef.current?.currentTime || 0,
    }));

    // Sync external durationMs if provided
    useEffect(() => {
      if (durationMs && durationMs > 0 && duration === 0) {
        setDuration(durationMs / 1000);
      }
    }, [durationMs, duration]);

    // Handle play / pause toggle
    const togglePlay = () => {
      const audio = audioRef.current;
      if (!audio) return;
      if (isPlaying) {
        audio.pause();
      } else {
        audio
          .play()
          .then(() => {
            setIsPlaying(true);
            onPlayStateChange?.(true);
          })
          .catch((err) => {
            console.error('Playback error:', err);
          });
      }
    };

    // Seek helper
    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
      const targetTime = parseFloat(e.target.value);
      setCurrentTime(targetTime);
      if (audioRef.current) {
        audioRef.current.currentTime = targetTime;
      }
    };

    // Skip forward or backward by seconds
    const skipTime = (deltaSec: number) => {
      const audio = audioRef.current;
      if (!audio) return;
      const newTime = Math.max(0, Math.min(duration || audio.duration || 0, audio.currentTime + deltaSec));
      audio.currentTime = newTime;
      setCurrentTime(newTime);
    };

    // Speed change
    const handleSpeedChange = (speed: number) => {
      setPlaybackRate(speed);
      if (audioRef.current) {
        audioRef.current.playbackRate = speed;
      }
    };

    // Volume change
    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newVol = parseFloat(e.target.value);
      setVolume(newVol);
      setIsMuted(newVol === 0);
      if (audioRef.current) {
        audioRef.current.volume = newVol;
        audioRef.current.muted = newVol === 0;
      }
    };

    const toggleMute = () => {
      const audio = audioRef.current;
      if (!audio) return;
      if (isMuted) {
        audio.muted = false;
        audio.volume = volume || 1;
        setIsMuted(false);
      } else {
        audio.muted = true;
        setIsMuted(true);
      }
    };

    // HTML5 audio event handlers
    const onLoadedMetadata = () => {
      const audio = audioRef.current;
      if (!audio) return;
      if (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) {
        setDuration(audio.duration);
      }
      setIsLoaded(true);
      setAudioError(null);
    };

    const onTimeUpdateHandler = useCallback(() => {
      const audio = audioRef.current;
      if (!audio) return;
      const current = audio.currentTime;
      setCurrentTime(current);
      onTimeUpdate?.(current * 1000);
    }, [onTimeUpdate]);

    const onPlayHandler = () => {
      setIsPlaying(true);
      onPlayStateChange?.(true);
    };

    const onPauseHandler = () => {
      setIsPlaying(false);
      onPlayStateChange?.(false);
    };

    const onEndedHandler = () => {
      setIsPlaying(false);
      onPlayStateChange?.(false);
    };

    const onErrorHandler = () => {
      setAudioError('Failed to load audio stream from server.');
      setIsPlaying(false);
      onPlayStateChange?.(false);
    };

    const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

    return (
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-sm)',
          padding: '16px 20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        {/* Hidden Audio Element */}
        <audio
          ref={audioRef}
          src={audioUrl}
          preload="metadata"
          onLoadedMetadata={onLoadedMetadata}
          onTimeUpdate={onTimeUpdateHandler}
          onPlay={onPlayHandler}
          onPause={onPauseHandler}
          onEnded={onEndedHandler}
          onError={onErrorHandler}
        />

        {audioError ? (
          <div
            style={{
              padding: '10px 14px',
              backgroundColor: 'var(--error-bg)',
              color: 'var(--error-fg)',
              border: '1px solid var(--error-border)',
              borderRadius: '8px',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <span>{audioError}</span>
            <button
              type="button"
              onClick={() => {
                setAudioError(null);
                if (audioRef.current) {
                  audioRef.current.load();
                }
              }}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--error-fg)',
                fontWeight: 700,
                textDecoration: 'underline',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        ) : null}

        {/* Top Row: Track & Status Info */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '12px',
            color: 'var(--color-text-secondary)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '2px 8px',
                borderRadius: '6px',
                backgroundColor: isPlaying ? 'var(--color-primary-subtle)' : 'var(--color-surface-sunken)',
                color: isPlaying ? 'var(--color-primary)' : 'var(--color-text-tertiary)',
                fontWeight: 600,
                fontSize: '11px',
              }}
            >
              <Radio size={12} className={isPlaying ? 'pulse-icon' : ''} />
              {isPlaying ? 'PLAYING' : isLoaded ? 'READY' : 'LOADING AUDIO'}
            </span>
            <span style={{ color: 'var(--color-text-tertiary)' }}>
              Call Audio Stream (Byte-Range Supported)
            </span>
          </div>

          {onToggleAutoScroll && (
            <button
              type="button"
              onClick={onToggleAutoScroll}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '6px',
                border: `1px solid ${autoScroll ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
                backgroundColor: autoScroll ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
                color: autoScroll ? 'var(--color-primary)' : 'var(--color-text-tertiary)',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              title="Automatically scroll transcript to follow active playback"
            >
              {autoScroll && <Check size={12} />}
              Auto-scroll Transcript: {autoScroll ? 'ON' : 'OFF'}
            </button>
          )}
        </div>

        {/* Middle Row: Progress Slider Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span
            style={{
              fontSize: '13px',
              fontWeight: 600,
              fontFamily: 'monospace',
              color: 'var(--color-text-primary)',
              minWidth: '45px',
            }}
          >
            {formatTime(currentTime)}
          </span>

          <div style={{ position: 'relative', flex: 1, display: 'flex', alignItems: 'center' }}>
            <input
              type="range"
              min={0}
              max={duration || 100}
              step={0.05}
              value={currentTime}
              onChange={handleSeek}
              aria-label="Audio scrubber"
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                cursor: 'pointer',
                accentColor: 'var(--color-primary)',
                background: `linear-gradient(to right, var(--color-primary) 0%, var(--color-primary) ${progressPercent}%, var(--color-surface-sunken) ${progressPercent}%, var(--color-surface-sunken) 100%)`,
              }}
            />
          </div>

          <span
            style={{
              fontSize: '13px',
              fontWeight: 500,
              fontFamily: 'monospace',
              color: 'var(--color-text-tertiary)',
              minWidth: '45px',
              textAlign: 'right',
            }}
          >
            {formatTime(duration)}
          </span>
        </div>

        {/* Bottom Row: Control Buttons */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          {/* Main Playback Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => skipTime(-5)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
              }}
              title="Rewind 5 seconds"
            >
              <RotateCcw size={15} />
            </button>

            <button
              type="button"
              onClick={togglePlay}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                border: 'none',
                backgroundColor: 'var(--color-primary)',
                color: '#FFFFFF',
                cursor: 'pointer',
                boxShadow: 'var(--shadow-sm)',
                transition: 'transform 0.1s ease',
              }}
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: '2px' }} />}
            </button>

            <button
              type="button"
              onClick={() => skipTime(5)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-secondary)',
                cursor: 'pointer',
              }}
              title="Forward 5 seconds"
            >
              <RotateCw size={15} />
            </button>
          </div>

          {/* Speed Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <SlidersHorizontal size={13} color="var(--color-text-tertiary)" />
            <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginRight: '2px' }}>
              Speed:
            </span>
            {[0.75, 1, 1.25, 1.5, 2].map((speed) => {
              const isActive = playbackRate === speed;
              return (
                <button
                  key={speed}
                  type="button"
                  onClick={() => handleSpeedChange(speed)}
                  style={{
                    padding: '3px 8px',
                    borderRadius: '6px',
                    border: `1px solid ${isActive ? 'var(--color-primary)' : 'var(--color-border)'}`,
                    backgroundColor: isActive ? 'var(--color-primary)' : 'var(--color-surface-sunken)',
                    color: isActive ? '#FFFFFF' : 'var(--color-text-secondary)',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {speed}x
                </button>
              );
            })}
          </div>

          {/* Volume Control */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={toggleMute}
              style={{
                background: 'none',
                border: 'none',
                padding: '4px',
                cursor: 'pointer',
                color: isMuted ? 'var(--error-fg)' : 'var(--color-text-secondary)',
              }}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              aria-label="Volume slider"
              style={{
                width: '70px',
                height: '4px',
                borderRadius: '2px',
                accentColor: 'var(--color-primary)',
                cursor: 'pointer',
              }}
            />
          </div>
        </div>
      </div>
    );
  }
);
