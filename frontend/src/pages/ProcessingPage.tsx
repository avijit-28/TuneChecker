import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Stepper } from '../components/processing/Stepper';
import type { StageInfo } from '../components/processing/Stepper';
import { apiRequest } from '../api/client';
import { AlertOctagon, ArrowLeft } from 'lucide-react';

interface CallStatusData {
  call_id: string;
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
