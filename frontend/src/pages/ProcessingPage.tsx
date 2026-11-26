import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Stepper } from '../components/processing/Stepper';
import type { StageInfo } from '../components/processing/Stepper';
import { apiRequest } from '../api/client';
import { AlertOctagon, ArrowLeft, FileAudio, Clock, HardDrive, Activity } from 'lucide-react';

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

  return (
    <div>
      <div style={{ marginBottom: '28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--color-text-primary)' }}>
            Auditing Sales Call
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Processing ID: <code style={{ backgroundColor: 'var(--color-surface-sunken)', padding: '2px 6px', borderRadius: '4px' }}>{id}</code>
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/history')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'none',
            border: '1px solid var(--color-border)',
            padding: '8px 14px',
            borderRadius: '8px',
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} />
          View in History
        </button>
      </div>

      {error && (
        <div
          style={{
            marginBottom: '20px',
            padding: '14px',
            borderRadius: '8px',
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
        <div style={{ maxWidth: '680px', margin: '0 auto 24px auto' }}>
          {/* File Metadata Overview Card */}
          <div
            style={{
              padding: '16px 20px',
              borderRadius: '12px',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              marginBottom: '16px',
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <FileAudio size={22} color="var(--color-primary)" />
              <div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  {statusData.filename || 'Audio Recording'}
                </div>
                <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
                  {statusData.duration_ms && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={12} /> {(statusData.duration_ms / 1000).toFixed(1)}s duration
                    </span>
                  )}
                  {statusData.size_bytes && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <HardDrive size={12} /> {(statusData.size_bytes / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  )}
                  <span>Status: <strong style={{ color: 'var(--color-primary)' }}>{statusData.status}</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* Live Current Activity Banner */}
          {statusData.status_group === 'in_progress' && statusData.current_activity && (
            <div
              style={{
                padding: '14px 18px',
                borderRadius: '10px',
                backgroundColor: 'rgba(59, 130, 246, 0.08)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <Activity size={18} color="var(--color-primary)" className="animate-pulse" />
              <div style={{ fontSize: '13px', color: 'var(--color-text-primary)' }}>
                <strong>Current Stage Activity:</strong> {statusData.current_activity}
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
