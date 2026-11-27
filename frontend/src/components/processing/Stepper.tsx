import React from 'react';
import {
  CheckCircle2,
  Loader2,
  Circle,
  AlertOctagon,
  RefreshCw,
  FileCheck2,
  AudioLines,
  Users,
  BarChart3,
  ShieldCheck,
  CheckSquare,
  FileText,
  Layers,
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
  transcription: '2. Speech-to-Text Transcription',
  speaker_identification: '3. Speaker Identification & Role Attribution',
  tone_analysis: '4. Sales Representative Tone Analysis',
  evidence_extraction: '5. Verbatim Evidence Verification',
  action_items: '6. Action Item & Follow-up Tracking',
  completion: '7. Finalizing Call Audit Report',
};

const STAGE_DESCRIPTIONS: Record<string, string> = {
  validation: 'Validating container format, duration limits, and normalizing to lossless 16kHz mono PCM.',
  transcription: 'Decoding speech to text with native Hinglish/Hindi support.',
  speaker_identification: 'Diarizing speech turns and classifying Sales Representative vs Customer roles.',
  tone_analysis: '2-layer evaluation: Voice Acoustics (volume spike, pitch F0, sharpness) + Text intent.',
  evidence_extraction: 'Matching exact transcript quote spans and verifying severity thresholds.',
  action_items: 'Detecting commitments, follow-ups, modality, and calendar deadlines.',
  completion: 'Compiling final audit report, speech recovery metrics, and coaching guidance.',
};

const STAGE_ICONS: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  validation: FileCheck2,
  transcription: AudioLines,
  speaker_identification: Users,
  tone_analysis: BarChart3,
  evidence_extraction: ShieldCheck,
  action_items: CheckSquare,
  completion: FileText,
};

export const Stepper: React.FC<StepperProps> = ({
  stages,
  completedCount,
  totalStages,
  onRetry,
  isRetrying,
}) => {
  return (
    <div>
      <div
        style={{
          marginBottom: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px',
            fontWeight: 700,
            color: 'var(--color-text-primary)',
          }}
        >
          <Layers size={16} color="#6366F1" />
          Pipeline Stages ({completedCount}/{totalStages})
        </span>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 600,
            color: '#059669',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            padding: '3px 10px',
            borderRadius: '999px',
          }}
        >
          ● Automated Voice Audit
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', position: 'relative' }}>
        {stages.map((st, idx) => {
          const title = STAGE_TITLES[st.stage] || st.stage;
          const StageIcon = STAGE_ICONS[st.stage] || FileText;
          const isSuccess = st.status === 'succeeded';
          const isRunning = st.status === 'running';
          const isFailed = st.status === 'failed';
          const elapsedSec = st.elapsed_ms != null ? (st.elapsed_ms / 1000).toFixed(1) : null;
          const isLast = idx === stages.length - 1;

          return (
            <div key={st.stage} style={{ display: 'flex', alignItems: 'stretch', gap: '12px' }}>
              {/* Vertical Timeline Rail */}
              <div
                className="stepper-rail-col"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  width: '24px',
                  flexShrink: 0,
                  paddingTop: '16px',
                }}
              >
                {isSuccess ? (
                  <CheckCircle2 size={20} color="#10B981" />
                ) : isRunning ? (
                  <div
                    style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '999px',
                      border: '2px solid #6366F1',
                      backgroundColor: 'rgba(99, 102, 241, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <div
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '999px',
                        backgroundColor: '#6366F1',
                      }}
                    />
                  </div>
                ) : isFailed ? (
                  <AlertOctagon size={20} color="var(--error-fg)" />
                ) : (
                  <Circle size={18} color="#CBD5E1" />
                )}

                {!isLast && (
                  <div
                    style={{
                      width: '2px',
                      flex: 1,
                      minHeight: '16px',
                      marginTop: '6px',
                      backgroundColor: isSuccess ? '#10B981' : '#E2E8F0',
                    }}
                  />
                )}
              </div>

              {/* Stage Card */}
              <div
                style={{
                  flex: 1,
                  minWidth: 0,
                  backgroundColor: isSuccess
                    ? 'rgba(16, 185, 129, 0.06)'
                    : isRunning
                    ? 'rgba(99, 102, 241, 0.06)'
                    : 'var(--color-surface)',
                  borderRadius: '12px',
                  padding: '14px 16px',
                  border: `1px solid ${
                    isFailed
                      ? 'var(--error-border)'
                      : isRunning
                      ? 'rgba(99, 102, 241, 0.4)'
                      : isSuccess
                      ? 'rgba(16, 185, 129, 0.35)'
                      : 'var(--color-border)'
                  }`,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  transition: 'all 0.2s ease',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    backgroundColor: isSuccess
                      ? 'rgba(16, 185, 129, 0.12)'
                      : isRunning
                      ? 'rgba(99, 102, 241, 0.14)'
                      : 'var(--color-surface-sunken)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '1px',
                  }}
                >
                  {isRunning ? (
                    <Loader2 size={16} color="#6366F1" className="animate-spin" />
                  ) : (
                    <StageIcon
                      size={16}
                      color={isSuccess ? '#059669' : isFailed ? '#DC2626' : '#64748B'}
                    />
                  )}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      gap: '8px',
                      flexWrap: 'wrap',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '14px',
                        fontWeight: 700,
                        color: isFailed
                          ? 'var(--error-fg)'
                          : isRunning
                          ? '#4F46E5'
                          : 'var(--color-text-primary)',
                      }}
                    >
                      {title}
                    </div>

                    {isSuccess && elapsedSec && (
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: '#059669',
                          backgroundColor: 'rgba(16, 185, 129, 0.14)',
                          padding: '2px 9px',
                          borderRadius: '999px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        ✓ {elapsedSec}s
                      </span>
                    )}

                    {isRunning && (
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: '#4F46E5',
                          backgroundColor: 'rgba(99, 102, 241, 0.14)',
                          padding: '2px 10px',
                          borderRadius: '999px',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        Processing...
                      </span>
                    )}
                  </div>

                  <div
                    style={{
                      fontSize: '12.5px',
                      color: isFailed
                        ? 'var(--error-fg)'
                        : isRunning
                        ? '#4338CA'
                        : isSuccess
                        ? 'var(--color-text-secondary)'
                        : 'var(--color-text-tertiary)',
                      marginTop: '4px',
                      lineHeight: 1.4,
                    }}
                  >
                    {st.message ? (
                      <span>
                        <strong style={{ color: '#059669' }}>Result:</strong> {st.message}
                      </span>
                    ) : isRunning ? (
                      <span>
                        <strong>In Progress:</strong> {STAGE_DESCRIPTIONS[st.stage]}
                      </span>
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
            </div>
          );
        })}
      </div>
    </div>
  );
};
