import React from 'react';
import { 
  CheckCircle2, 
  Loader2, 
  Circle, 
  AlertOctagon,
  RefreshCw
} from 'lucide-react';

export interface StageInfo {
  stage: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped';
  attempt?: number | null;
  started_at?: string | null;
  finished_at?: string | null;
  elapsed_ms?: number | null;
  message?: string | null;
  error_code?: string | null;
}

interface StepperProps {
  stages: StageInfo[];
  completedCount: number;
  totalStages: number;
  onRetry?: (stageName: string) => void;
  isRetrying?: boolean;
}

const STAGE_TITLES: Record<string, string> = {
  validation: '1. Audio Validation & Format Verification',
  transcription: '2. Faster-Whisper Transcription',
  speaker_identification: '3. Speaker Identification & Role Attribution',
  tone_analysis: '4. Sales Representative Tone Analysis',
  evidence_extraction: '5. Verbatim Evidence Verification',
  action_items: '6. Action Item & Follow-up Tracking',
  completion: '7. Finalizing Call Audit Report',
};

const STAGE_DESCRIPTIONS: Record<string, string> = {
  validation: 'Validating container format, duration limits, and normalizing to lossless 16kHz mono PCM.',
  transcription: 'Decoding speech to text using Faster-Whisper ASR with native Hinglish/Hindi support.',
  speaker_identification: 'Diarizing speech turns and classifying Sales Representative vs Customer roles.',
  tone_analysis: '2-layer evaluation: Voice Acoustics (volume spike, pitch F0, sharpness) + Text intent.',
  evidence_extraction: 'Matching exact transcript quote spans and verifying severity thresholds.',
  action_items: 'Detecting commitments, follow-ups, modality, and calendar deadlines.',
  completion: 'Compiling final audit report, speech recovery metrics, and coaching guidance.',
};

export const Stepper: React.FC<StepperProps> = ({
  stages,
  completedCount,
  totalStages,
  onRetry,
  isRetrying,
}) => {
  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      <div style={{ marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--color-text-secondary)' }}>
          Pipeline Stages ({completedCount}/{totalStages})
        </span>
        <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
          Zero-Cost Local Pipeline
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {stages.map((st) => {
          const title = STAGE_TITLES[st.stage] || st.stage;
          const isSuccess = st.status === 'succeeded';
          const isRunning = st.status === 'running';
          const isFailed = st.status === 'failed';
          const isPending = st.status === 'pending';

          const elapsedSec = st.elapsed_ms ? (st.elapsed_ms / 1000).toFixed(1) : null;

          return (
            <div
              key={st.stage}
              style={{
                backgroundColor: 'var(--color-surface)',
                borderRadius: '12px',
                padding: '16px 20px',
                border: `1px solid ${
                  isFailed
                    ? 'var(--error-border)'
                    : isRunning
                    ? 'var(--color-primary-border)'
                    : isSuccess
                    ? 'var(--success-border)'
                    : 'var(--color-border)'
                }`,
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ marginTop: '2px', flexShrink: 0 }}>
                {isSuccess && <CheckCircle2 size={20} color="var(--success-fg)" />}
                {isRunning && <Loader2 size={20} color="var(--color-primary)" className="animate-spin" />}
                {isFailed && <AlertOctagon size={20} color="var(--error-fg)" />}
                {isPending && <Circle size={20} color="var(--color-text-disabled)" />}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div
                    style={{
                      fontSize: '14px',
                      fontWeight: isRunning ? 700 : 600,
                      color: isFailed
                        ? 'var(--error-fg)'
                        : isRunning
                        ? 'var(--color-primary)'
                        : 'var(--color-text-primary)',
                    }}
                  >
                    {title}
                  </div>
                  {elapsedSec && (
                    <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                      {elapsedSec}s
                    </span>
                  )}
                </div>

                <div
                  style={{
                    fontSize: '13px',
                    color: isFailed
                      ? 'var(--error-fg)'
                      : isRunning
                      ? 'var(--color-primary)'
                      : isSuccess
                      ? 'var(--color-text-secondary)'
                      : 'var(--color-text-tertiary)',
                    marginTop: '4px',
                    lineHeight: 1.4,
                  }}
                >
                  {st.message ? (
                    <span><strong>Result:</strong> {st.message}</span>
                  ) : isRunning ? (
                    <span><strong>In Progress:</strong> {STAGE_DESCRIPTIONS[st.stage]}</span>
                  ) : (
                    <span>{STAGE_DESCRIPTIONS[st.stage]}</span>
                  )}
                </div>

                {isFailed && onRetry && (
                  <div style={{ marginTop: '10px' }}>
                    <button
                      type="button"
                      onClick={() => onRetry(st.stage)}
                      disabled={isRetrying}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        fontSize: '12px',
                        fontWeight: 600,
                        backgroundColor: 'var(--color-surface)',
                        color: 'var(--error-fg)',
                        border: '1px solid var(--error-border)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        cursor: isRetrying ? 'not-allowed' : 'pointer',
                      }}
                    >
                      <RefreshCw size={12} className={isRetrying ? 'animate-spin' : ''} />
                      Retry This Stage
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
