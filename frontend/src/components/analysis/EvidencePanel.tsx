import React from 'react';

export interface EvidenceItemData {
  id: string;
  ref: string;
  utterance_id: string;
  speaker_label: string;
  quote: string;
  char_start: number;
  char_end: number;
  criterion_id: string;
  severity: number;
  rationale: string;
  start_ms: number;
}

interface EvidencePanelProps {
  evidence: EvidenceItemData[];
  onSelectEvidence?: (utteranceId: string) => void;
  selectedUtteranceId?: string | null;
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  evidence,
  onSelectEvidence,
  selectedUtteranceId,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: '12px',
        border: '1px solid var(--color-border)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-divider)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Verified Tone Evidence ({evidence.length})
        </h3>
        <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
          Exact Transcript Spans
        </span>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {evidence.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '13px' }}>
            No negative behavior evidence found in the representative's utterances.
          </div>
        ) : (
          evidence.map((ev) => {
            const isSelected = selectedUtteranceId === ev.utterance_id;
            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvidence && onSelectEvidence(ev.utterance_id)}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  backgroundColor: isSelected ? 'var(--color-primary-subtle)' : 'var(--color-surface-sunken)',
                  border: `1px solid ${isSelected ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
                  cursor: onSelectEvidence ? 'pointer' : 'default',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--tone-red-bg)',
                        color: 'var(--tone-red-fg)',
                        border: '1px solid var(--tone-red-border)',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}
                    >
                      {ev.ref}
                    </span>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '10px',
                        backgroundColor: 'var(--color-surface)',
                        color: 'var(--color-text-secondary)',
                        fontSize: '11px',
                        fontWeight: 600,
                        textTransform: 'capitalize',
                      }}
                    >
                      {ev.criterion_id} • Severity {ev.severity}
                    </span>
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontFamily: 'monospace' }}>
                    {formatMs(ev.start_ms)}
                  </span>
                </div>

                <div
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--color-text-primary)',
                    fontStyle: 'italic',
                    marginBottom: '6px',
                  }}
                >
                  "{ev.quote}"
                </div>

                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.4 }}>
                  {ev.rationale}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
