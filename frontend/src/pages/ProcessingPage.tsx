import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Stepper } from '../components/processing/Stepper';
import type { StageInfo } from '../components/processing/Stepper';
import { apiRequest } from '../api/client';
import {
  AlertOctagon,
  ArrowLeft,
  ArrowRight,
  FileAudio,
  Clock,
  HardDrive,
  Sparkles,
  CheckCircle2,
  Play,
  Pause,
  Volume2,
  Info,
  Terminal,
  Headphones,
} from 'lucide-react';

interface CallStatusData {
  call_id: string;
  filename?: string | null;
  size_bytes?: number | null;
  duration_ms?: number | null;
  current_activity?: string | null;
  started_at?: string | null;
  status: string;
  status_group: string;
  current_stage: string | null;
  completed_stages: number;
  total_stages: number;
  stages: StageInfo[];
  failure?: {
    stage: string;
    code: string;
    message: string;
    retryable: boolean;
  } | null;
}

const WAVEFORM_BARS = [
  24, 42, 65, 38, 82, 54, 70, 92, 48, 60, 88, 35, 76, 62, 95, 50, 40, 74, 86, 44,
  58, 78, 34, 68, 90, 52, 62, 46, 80, 56, 42, 70, 36, 64, 48, 30,
];

function formatTimeSec(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

function formatHMS(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const rem = s % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
}

function formatLogTime(iso?: string | null): string {
  if (!iso) return '--:--:--';
  const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return '--:--:--';
  return d.toTimeString().slice(0, 8);
}

export const ProcessingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [statusData, setStatusData] = useState<CallStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [elapsedSec, setElapsedSec] = useState(0);

  // Audio playback state
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(0.85);

  useEffect(() => {
    if (!id) return;

    let isMounted = true;
    let timerId: any = null;

    const pollStatus = async () => {
      try {
        const data = await apiRequest<CallStatusData>(`/calls/${id}/status`);
        if (!isMounted) return;

        setStatusData(data);

        if (data.status === 'complete' || (data.status === 'partial' && !data.failure)) {
          setTimeout(() => {
            navigate(`/calls/${id}`);
          }, 1000);
          return;
        }

        if (data.status_group === 'in_progress') {
          timerId = setTimeout(pollStatus, 2000);
        }
      } catch (err: any) {
        if (!isMounted) return;
        setError(err.message || 'Failed to poll processing status.');
      }
    };

    pollStatus();

    return () => {
      isMounted = false;
      if (timerId) clearTimeout(timerId);
    };
  }, [id, navigate]);

  // Live elapsed timer while in progress
  useEffect(() => {
    if (!statusData || statusData.status_group !== 'in_progress') return;
    const tick = setInterval(() => {
      setElapsedSec((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(tick);
  }, [statusData?.status_group]);

  const handleRetry = async (stageName: string) => {
    if (!id) return;
    setIsRetrying(true);
    try {
      await apiRequest(`/calls/${id}/retry`, {
        method: 'POST',
        body: JSON.stringify({ stage: stageName }),
      });
      const data = await apiRequest<CallStatusData>(`/calls/${id}/status`);
      setStatusData(data);
    } catch (err: any) {
      setError(err?.message || 'Retry failed');
    } finally {
      setIsRetrying(false);
    }
  };

  const togglePlay = () => {
    const el = audioRef.current;
    if (!el) return;
    if (isPlaying) {
      el.pause();
    } else {
      el.play().catch(() => {});
    }
  };

  const cycleSpeed = () => {
    const speeds = [1, 1.25, 1.5, 2];
    const next = speeds[(speeds.indexOf(playbackRate) + 1) % speeds.length];
    setPlaybackRate(next);
    if (audioRef.current) audioRef.current.playbackRate = next;
  };

  const progressPct =
    statusData && statusData.total_stages > 0
      ? Math.round((statusData.completed_stages / statusData.total_stages) * 100)
      : 0;
  const isComplete = statusData?.status === 'complete' || statusData?.status === 'partial';

  const totalDurSec =
    audioDuration > 0
      ? audioDuration
      : statusData?.duration_ms
      ? statusData.duration_ms / 1000
      : 0;
  const playProgressRatio = totalDurSec > 0 ? Math.min(1, currentTime / totalDurSec) : 0;

  const fileExt = useMemo(() => {
    const name = statusData?.filename || '';
    const dot = name.lastIndexOf('.');
    return dot >= 0 ? name.slice(dot + 1).toUpperCase() : 'AUDIO';
  }, [statusData?.filename]);

  const liveLogs = useMemo(() => {
    if (!statusData) return [];
    const entries: { time: string; text: string; tone: 'success' | 'active' | 'error' }[] = [
      {
        time: formatLogTime(statusData.started_at),
        text: 'File uploaded successfully.',
        tone: 'success',
      },
    ];
    for (const st of statusData.stages) {
      if (st.status === 'succeeded') {
        entries.push({
          time: formatLogTime(st.finished_at || st.started_at),
          text: st.message || `${st.stage.replace('_', ' ')} completed.`,
          tone: 'success',
        });
      } else if (st.status === 'running') {
        entries.push({
          time: formatLogTime(st.started_at),
          text: statusData.current_activity || `Running ${st.stage.replace('_', ' ')}...`,
          tone: 'active',
        });
      } else if (st.status === 'failed') {
        entries.push({
          time: formatLogTime(st.finished_at || st.started_at),
          text: st.message || `${st.stage.replace('_', ' ')} failed.`,
          tone: 'error',
        });
      }
    }
    return entries.slice(-6);
  }, [statusData]);

  return (
    <div style={{ maxWidth: '100%', margin: '0 auto' }}>
      {/* Top Header */}
      <div
        style={{
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15))',
              border: '1px solid rgba(99, 102, 241, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6366F1',
              flexShrink: 0,
            }}
          >
            <Headphones size={22} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h1
                style={{
                  fontSize: '24px',
                  fontWeight: 800,
                  margin: 0,
                  color: 'var(--color-text-primary)',
                  letterSpacing: '-0.02em',
                }}
              >
                Auditing Sales Call
              </h1>
              {statusData && (
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    padding: '3px 10px',
                    borderRadius: '999px',
                    backgroundColor: isComplete
                      ? 'var(--success-bg)'
                      : statusData.status === 'failed'
                      ? 'var(--error-bg)'
                      : 'rgba(99, 102, 241, 0.12)',
                    color: isComplete
                      ? 'var(--success-fg)'
                      : statusData.status === 'failed'
                      ? 'var(--error-fg)'
                      : '#4F46E5',
                    border: `1px solid ${
                      isComplete
                        ? 'var(--success-border)'
                        : statusData.status === 'failed'
                        ? 'var(--error-border)'
                        : 'rgba(99, 102, 241, 0.3)'
                    }`,
                  }}
                >
                  {statusData.status}
                </span>
              )}
            </div>
            <p
              style={{
                margin: '3px 0 0 0',
                fontSize: '12.5px',
                color: 'var(--color-text-tertiary)',
                wordBreak: 'break-all',
              }}
            >
              Call ID:{' '}
              <code
                style={{
                  backgroundColor: 'var(--color-surface-sunken)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}
              >
                {id}
              </code>
            </p>
          </div>
        </div>

        <div className="results-header-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={() => navigate('/history')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              padding: '8px 14px',
              borderRadius: '9px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft size={15} />
            History
          </button>
          {isComplete && (
            <button
              type="button"
              onClick={() => navigate(`/calls/${id}`)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                background: 'linear-gradient(90deg, #5B5CE6 0%, #8B5CF6 100%)',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '9px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              View Report
              <ArrowRight size={15} />
            </button>
          )}
        </div>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '14px',
            borderRadius: '10px',
            backgroundColor: 'var(--error-bg)',
            color: 'var(--error-fg)',
            border: '1px solid var(--error-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '13px',
          }}
        >
          <AlertOctagon size={18} />
          <span>{error}</span>
        </div>
      )}

      {statusData && (
        <div
          className="processing-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.5fr) minmax(260px, 0.95fr)',
            gap: '18px',
            alignItems: 'start',
          }}
        >
          {/* LEFT COLUMN: Hero Progress + Live Activity + Timeline Stepper */}
          <div style={{ minWidth: 0 }}>
            {/* Hero File & Progress Card */}
            <div
              style={{
                padding: '20px 22px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, var(--color-surface) 0%, rgba(99, 102, 241, 0.04) 100%)',
                border: '1px solid var(--color-border)',
                boxShadow: '0 4px 16px rgba(15, 23, 42, 0.04)',
                marginBottom: '14px',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '14px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
                  <div
                    style={{
                      width: '46px',
                      height: '46px',
                      borderRadius: '12px',
                      backgroundColor: 'rgba(99, 102, 241, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <FileAudio size={22} color="#6366F1" />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: '15.5px',
                        fontWeight: 700,
                        color: 'var(--color-text-primary)',
                        wordBreak: 'break-word',
                      }}
                    >
                      {statusData.filename || 'Audio Recording'}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '12px',
                        fontSize: '12px',
                        color: 'var(--color-text-tertiary)',
                        marginTop: '4px',
                      }}
                    >
                      {statusData.duration_ms != null && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={12} /> {(statusData.duration_ms / 1000).toFixed(1)}s
                        </span>
                      )}
                      {statusData.size_bytes != null && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <HardDrive size={12} /> {(statusData.size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </span>
                      )}
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: '#5B5CE6',
                          fontWeight: 600,
                        }}
                      >
                        <Sparkles size={12} /> 2-Layer Text + Voice Acoustics
                      </span>
                    </div>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div
                    style={{
                      fontSize: '26px',
                      fontWeight: 800,
                      color: isComplete ? '#10B981' : '#5B5CE6',
                      lineHeight: 1,
                    }}
                  >
                    {progressPct}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
                    {statusData.completed_stages} of {statusData.total_stages} stages
                  </div>
                  <div
                    style={{
                      marginTop: '6px',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      fontSize: '11.5px',
                      fontWeight: 700,
                      color: '#4F46E5',
                      backgroundColor: 'rgba(99, 102, 241, 0.12)',
                      padding: '2px 8px',
                      borderRadius: '999px',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    <Clock size={11} />
                    {elapsedSec}s elapsed
                  </div>
                </div>
              </div>

              <div
                style={{
                  height: '8px',
                  borderRadius: '999px',
                  backgroundColor: 'var(--color-surface-sunken)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${progressPct}%`,
                    height: '100%',
                    borderRadius: '999px',
                    background: isComplete
                      ? 'linear-gradient(90deg, #10B981 0%, #34D399 100%)'
                      : statusData.status === 'failed'
                      ? 'var(--error-fg)'
                      : 'linear-gradient(90deg, #5B5CE6 0%, #8B5CF6 100%)',
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </div>

            {/* Live Activity or Completion Banner */}
            {statusData.status_group === 'in_progress' && statusData.current_activity && (
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: '11px',
                  backgroundColor: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  marginBottom: '18px',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--color-text-primary)' }}>
                  <Sparkles size={16} color="#6366F1" className="animate-pulse" />
                  <span>
                    <strong>Live Activity:</strong> {statusData.current_activity}
                  </span>
                </div>
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#4F46E5',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                >
                  <Clock size={13} />
                  {formatHMS(elapsedSec)}
                </span>
              </div>
            )}

            {isComplete && (
              <div
                style={{
                  padding: '12px 16px',
                  borderRadius: '11px',
                  backgroundColor: 'var(--success-bg)',
                  border: '1px solid var(--success-border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '13px',
                  color: 'var(--success-fg)',
                  fontWeight: 600,
                  marginBottom: '18px',
                }}
              >
                <CheckCircle2 size={18} />
                <span>Audit complete! Redirecting to full transcript & tone evidence report...</span>
              </div>
            )}

            <Stepper
              stages={statusData.stages}
              completedCount={statusData.completed_stages}
              totalStages={statusData.total_stages}
              onRetry={handleRetry}
              isRetrying={isRetrying}
            />
          </div>

          {/* RIGHT COLUMN: Call Playback + Call Details + Live Logs */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>
            {/* Call Playback Card */}
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '14px',
                padding: '18px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Play size={16} color="#6366F1" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  Call Playback
                </span>
              </div>

              <audio
                ref={audioRef}
                src={`/api/v1/calls/${id}/audio`}
                preload="metadata"
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onEnded={() => setIsPlaying(false)}
                onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
                onLoadedMetadata={(e) => setAudioDuration(e.currentTarget.duration)}
              />

              {/* Waveform Visualizer */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '3px',
                  height: '46px',
                  padding: '6px 4px',
                  marginBottom: '12px',
                }}
              >
                {WAVEFORM_BARS.map((h, i) => {
                  const barPct = i / WAVEFORM_BARS.length;
                  const active = barPct <= playProgressRatio;
                  return (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        height: `${h}%`,
                        borderRadius: '999px',
                        backgroundColor: active ? '#6366F1' : '#CBD5E1',
                        transition: 'background-color 0.15s ease',
                      }}
                    />
                  );
                })}
              </div>

              {/* Player Controls */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={togglePlay}
                    aria-label={isPlaying ? 'Pause audio' : 'Play audio'}
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '999px',
                      border: 'none',
                      background: 'linear-gradient(135deg, #5B5CE6 0%, #8B5CF6 100%)',
                      color: '#fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                  >
                    {isPlaying ? <Pause size={15} /> : <Play size={15} style={{ marginLeft: '2px' }} />}
                  </button>
                  <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                    {formatTimeSec(currentTime)} / {formatTimeSec(totalDurSec)}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={cycleSpeed}
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '4px 8px',
                      borderRadius: '6px',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-surface-sunken)',
                      color: 'var(--color-text-primary)',
                      cursor: 'pointer',
                    }}
                  >
                    {playbackRate}x
                  </button>
                  <Volume2 size={14} color="var(--color-text-tertiary)" />
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={volume}
                    aria-label="Playback volume"
                    onChange={(e) => {
                      const v = parseFloat(e.target.value);
                      setVolume(v);
                      if (audioRef.current) audioRef.current.volume = v;
                    }}
                    style={{ width: '62px', accentColor: '#6366F1', cursor: 'pointer' }}
                  />
                </div>
              </div>
            </div>

            {/* Call Details Card */}
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '14px',
                padding: '18px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Info size={16} color="#6366F1" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  Call Details
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12.5px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                  <span style={{ color: 'var(--color-text-tertiary)' }}>File Name</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-text-primary)', textAlign: 'right', wordBreak: 'break-all' }}>
                    {statusData.filename || 'Recording'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                  <span style={{ color: 'var(--color-text-tertiary)' }}>Duration</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {statusData.duration_ms != null
                      ? `${formatTimeSec(statusData.duration_ms / 1000)} (${(statusData.duration_ms / 1000).toFixed(1)}s)`
                      : 'Detecting...'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                  <span style={{ color: 'var(--color-text-tertiary)' }}>File Size</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {statusData.size_bytes != null ? `${(statusData.size_bytes / (1024 * 1024)).toFixed(2)} MB` : '--'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                  <span style={{ color: 'var(--color-text-tertiary)' }}>Format</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{fileExt}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
                  <span style={{ color: 'var(--color-text-tertiary)' }}>Analysis Mode</span>
                  <span style={{ fontWeight: 600, color: '#5B5CE6', textAlign: 'right' }}>
                    2-Layer Text + Voice Acoustics
                  </span>
                </div>
              </div>
            </div>

            {/* Live Logs Card */}
            <div
              style={{
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '14px',
                padding: '18px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Terminal size={16} color="#6366F1" />
                <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  Live Logs
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '9px', fontSize: '12px' }}>
                {liveLogs.map((log, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    <span
                      style={{
                        color: 'var(--color-text-tertiary)',
                        fontFamily: 'monospace',
                        fontSize: '11px',
                        flexShrink: 0,
                        marginTop: '1px',
                      }}
                    >
                      {log.time}
                    </span>
                    <span
                      style={{
                        width: '7px',
                        height: '7px',
                        borderRadius: '999px',
                        marginTop: '5px',
                        flexShrink: 0,
                        backgroundColor:
                          log.tone === 'success'
                            ? '#10B981'
                            : log.tone === 'error'
                            ? '#EF4444'
                            : '#6366F1',
                      }}
                    />
                    <span
                      style={{
                        color: log.tone === 'active' ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                        fontWeight: log.tone === 'active' ? 600 : 400,
                        lineHeight: 1.35,
                        wordBreak: 'break-word',
                      }}
                    >
                      {log.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
