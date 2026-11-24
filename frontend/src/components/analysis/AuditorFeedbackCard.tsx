import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../api/client';
import { CheckCircle2, ThumbsUp, ThumbsDown, Sparkles, MessageSquare, RefreshCw } from 'lucide-react';

interface AuditorFeedbackCardProps {
  callId: string;
  analysisId?: string;
  currentVerdict: string;
  calibratedModel?: {
    calibrated_verdict: string;
    red_probability: number;
    confidence: string;
  } | null;
}

export const AuditorFeedbackCard: React.FC<AuditorFeedbackCardProps> = ({
  callId,
  analysisId,
  currentVerdict,
  calibratedModel,
}) => {
  const [agreed, setAgreed] = useState<boolean>(true);
  const [auditorVerdict, setAuditorVerdict] = useState<string>(currentVerdict);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [trainingResult, setTrainingResult] = useState<any>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [existingFeedback, setExistingFeedback] = useState<any[]>([]);

  useEffect(() => {
    // Fetch any prior feedback
    apiRequest<any[]>(`/calls/${callId}/feedback`)
      .then((data) => {
        if (data && data.length > 0) {
          setExistingFeedback(data);
          setSubmitted(true);
        }
      })
      .catch(() => {});
  }, [callId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest(`/calls/${callId}/feedback`, {
        method: 'POST',
        body: JSON.stringify({
          analysis_id: analysisId,
          agreed,
          auditor_verdict: agreed ? currentVerdict : auditorVerdict,
          notes,
          auditor_name: 'Sales Quality Auditor',
        }),
      });
      setSubmitted(true);
      const updated = await apiRequest<any[]>(`/calls/${callId}/feedback`);
      setExistingFeedback(updated);
    } catch (err: any) {
      alert(`Feedback submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTrainModel = async () => {
    setIsTraining(true);
    try {
      const res = await apiRequest<any>('/calls/feedback/train', { method: 'POST' });
      setTrainingResult(res);
    } catch (err: any) {
      alert(`Model training error: ${err.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div
      style={{
        marginTop: '24px',
        padding: '20px',
        borderRadius: '12px',
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={18} color="var(--color-primary)" />
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Auditor Review & Continuous Learning
          </h3>
        </div>

        {calibratedModel && (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '12px',
              backgroundColor: 'var(--color-primary-subtle)',
              color: 'var(--color-primary)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            <Sparkles size={14} />
            Calibrated Model: {calibratedModel.calibrated_verdict} ({(calibratedModel.red_probability * 100).toFixed(0)}% RED)
          </div>
        )}
      </div>

      <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
        SpeechGuard active learning loop: Validate or correct this audit verdict. Verified human corrections train a local TF-IDF classifier to continuously calibrate future tone judgments.
      </p>

      {submitted ? (
        <div
          style={{
            padding: '14px',
            borderRadius: '8px',
            backgroundColor: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            color: 'var(--success-fg)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            fontSize: '13px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
            <CheckCircle2 size={16} />
            Auditor verdict saved to local training dataset.
          </div>
          {existingFeedback.length > 0 && (
            <div style={{ fontSize: '12px', opacity: 0.9 }}>
              Latest Decision: <strong>{existingFeedback[0].auditor_verdict}</strong> ({existingFeedback[0].agreed ? 'Agreed with AI' : 'Corrected'})
              {existingFeedback[0].notes && ` — "${existingFeedback[0].notes}"`}
            </div>
          )}
          <div style={{ marginTop: '6px', display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={() => setSubmitted(false)}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                textDecoration: 'underline',
                fontSize: '12px',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              Update your feedback
            </button>
            <button
              type="button"
              onClick={handleTrainModel}
              disabled={isTraining}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                background: 'none',
                border: 'none',
                color: 'var(--color-primary)',
                fontWeight: 600,
                fontSize: '12px',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              <RefreshCw size={13} className={isTraining ? 'spin' : ''} />
              {isTraining ? 'Training...' : 'Retrain Calibrator'}
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '14px' }}>
            <button
              type="button"
              onClick={() => {
                setAgreed(true);
                setAuditorVerdict(currentVerdict);
              }}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '10px 14px',
                borderRadius: '8px',
                border: agreed ? '2px solid var(--success-border)' : '1px solid var(--color-border)',
                backgroundColor: agreed ? 'var(--success-bg)' : 'var(--color-surface-sunken)',
                color: agreed ? 'var(--success-fg)' : 'var(--color-text-secondary)',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <ThumbsUp size={16} />
              Agree with AI Verdict ({currentVerdict})
            </button>

            <button
              type="button"
              onClick={() => {
                setAgreed(false);
                setAuditorVerdict(currentVerdict === 'RED' ? 'GREEN' : 'RED');
              }}
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                padding: '10px 14px',
                borderRadius: '8px',
                border: !agreed ? '2px solid var(--error-border)' : '1px solid var(--color-border)',
                backgroundColor: !agreed ? 'var(--error-bg)' : 'var(--color-surface-sunken)',
                color: !agreed ? 'var(--error-fg)' : 'var(--color-text-secondary)',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <ThumbsDown size={16} />
              Disagree / Correct Verdict
            </button>
          </div>

          {!agreed && (
            <div style={{ marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                Corrected Verdict:
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                {['GREEN', 'RED'].map((v) => (
                  <button
                    key={v}
                    type="button"
                    onClick={() => setAuditorVerdict(v)}
                    style={{
                      padding: '4px 12px',
                      borderRadius: '6px',
                      border: auditorVerdict === v ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
                      backgroundColor: auditorVerdict === v ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
                      color: auditorVerdict === v ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginBottom: '14px' }}>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional context note (e.g. rep was polite despite objections)"
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface-sunken)',
                color: 'var(--color-text-primary)',
                fontSize: '13px',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              type="submit"
              disabled={submitting}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                backgroundColor: 'var(--color-primary)',
                color: '#FFFFFF',
                border: 'none',
                fontWeight: 600,
                fontSize: '13px',
                cursor: submitting ? 'not-allowed' : 'pointer',
              }}
            >
              {submitting ? 'Saving...' : 'Save Auditor Review'}
            </button>
          </div>
        </form>
      )}

      {trainingResult && (
        <div
          style={{
            marginTop: '14px',
            padding: '12px',
            borderRadius: '8px',
            backgroundColor: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
            fontSize: '12px',
            color: 'var(--color-text-secondary)',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '4px' }}>
            Training Status: {trainingResult.status} ({trainingResult.message})
          </div>
          {trainingResult.metrics && (
            <div>
              Macro-F1: <strong>{trainingResult.metrics.macro_f1?.toFixed(3)}</strong> • Accuracy: <strong>{trainingResult.metrics.accuracy?.toFixed(3)}</strong> • Counts: GREEN={trainingResult.metrics.counts?.GREEN}, RED={trainingResult.metrics.counts?.RED}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
