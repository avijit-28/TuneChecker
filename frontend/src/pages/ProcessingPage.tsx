import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Stepper } from '../components/processing/Stepper';
import type { StageInfo } from '../components/processing/Stepper';
import { apiRequest } from '../api/client';
import { AlertOctagon, ArrowLeft, ArrowRight, FileAudio, Clock, HardDrive, Activity, CheckCircle2, Sparkles } from 'lucide-react';

interface CallStatusData {
  call_id: string;
  filename?: string | null;
  size_bytes?: number | null;
  duration_ms?: number | null;
  current_activity?: string | null;
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

export const ProcessingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [statusData, setStatusData] = useState<CallStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    if (!id) return;

    let isMounted = true;
    let timerId: any = null;

    const pollStatus = async () => {
      try {
        const data = await apiRequest<CallStatusData>(`/calls/${id}/status`);
        if (!isMounted) return;

        setStatusData(data);

        // Terminal status: redirect to results only if complete or partial with finished analysis
        if (data.status === 'complete' || (data.status === 'partial' && !data.failure)) {
          setTimeout(() => {
            navigate(`/calls/${id}`);
          }, 800);
          return;
        }

        // If still in progress, poll again in 2 seconds
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

  const handleRetry = async (stageName: string) => {
    if (!id) return;
    setIsRetrying(true);
    try {
      await apiRequest(`/calls/${id}/retry`, {
        method: 'POST',
        body: JSON.stringify({ stage: stageName }),
      });
      // Restart polling
      const data = await apiRequest<CallStatusData>(`/calls/${id}/status`);
      setStatusData(data);
    } catch (err: any) {
      setError(err?.message || 'Retry failed');
    } finally {
      setIsRetrying(false);
    }
  };

  const progressPct = statusData && statusData.total_stages > 0
    ? Math.round((statusData.completed_stages / statusData.total_stages) * 100)
    : 0;
  const isComplete = statusData?.status === 'complete' || statusData?.status === 'partial';

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <h1 style={{ fontSize: '26px', fontWeight: 800, margin: 0, color: 'var(--color-text-primary)', letterSpacing: '-0.02em' }}>
              Auditing Sales Call
            </h1>
            {statusData && (
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  padding: '3px 10px',
                  borderRadius: '999px',
                  backgroundColor: isComplete ? 'var(--success-bg)' : statusData.status === 'failed' ? 'var(--error-bg)' : 'rgba(59, 130, 246, 0.12)',
                  color: isComplete ? 'var(--success-fg)' : statusData.status === 'failed' ? 'var(--error-fg)' : 'var(--color-primary)',
                  border: `1px solid ${isComplete ? 'var(--success-border)' : statusData.status === 'failed' ? 'var(--error-border)' : 'rgba(59, 130, 246, 0.3)'}`,
                }}
              >
                {statusData.status}
              </span>
            )}
          </div>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-text-tertiary)' }}>
            Call ID: <code style={{ backgroundColor: 'var(--color-surface-sunken)', padding: '2px 6px', borderRadius: '4px' }}>{id}</code>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={() => navigate('/history')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              padding: '8px 14px',
              borderRadius: '8px',
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
                gap: '6px',
                background: 'var(--color-primary)',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '8px',
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
        <div style={{ marginBottom: '24px' }}>
          {/* Hero File & Progress Card */}
          <div
            style={{
              padding: '20px 24px',
              borderRadius: '14px',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)',
              marginBottom: '14px',
            }}
          >
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <FileAudio size={22} color="var(--color-primary)" />
                </div>
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {statusData.filename || 'Audio Recording'}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
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
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--color-primary)', fontWeight: 600 }}>
                      <Sparkles size={12} /> 2-Layer Text + Voice Acoustics
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '22px', fontWeight: 800, color: isComplete ? 'var(--success-fg)' : 'var(--color-primary)', lineHeight: 1 }}>
                  {progressPct}%
                </div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
                  {statusData.completed_stages} of {statusData.total_stages} stages
                </div>
              </div>
            </div>

            {/* Linear Progress Bar */}
            <div style={{ height: '8px', borderRadius: '999px', backgroundColor: 'var(--color-surface-sunken)', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${progressPct}%`,
                  height: '100%',
                  borderRadius: '999px',
                  backgroundColor: isComplete ? 'var(--success-fg)' : statusData.status === 'failed' ? 'var(--error-fg)' : 'var(--color-primary)',
                  transition: 'width 0.4s ease',
                }}
              />
            </div>
          </div>

          {/* Live Current Activity or Completion Banner */}
          {statusData.status_group === 'in_progress' && statusData.current_activity && (
            <div
              style={{
                padding: '13px 18px',
                borderRadius: '10px',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <Activity size={18} color="var(--color-primary)" className="animate-pulse" />
              <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                <strong>Live Activity:</strong> {statusData.current_activity}
              </div>
            </div>
          )}

          {isComplete && (
            <div
              style={{
                padding: '13px 18px',
                borderRadius: '10px',
                backgroundColor: 'var(--success-bg)',
                border: '1px solid var(--success-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--success-fg)', fontWeight: 600 }}>
                <CheckCircle2 size={18} />
                <span>Audit complete! Redirecting to full transcript & tone evidence report...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {statusData && (
        <Stepper
          stages={statusData.stages}
          completedCount={statusData.completed_stages}
          totalStages={statusData.total_stages}
          onRetry={handleRetry}
          isRetrying={isRetrying}
        />
      )}
    </div>
  );
};
