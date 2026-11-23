import React from 'react';
import { Calendar, User } from 'lucide-react';

export interface ActionItemData {
  id: string;
  ref: string;
  type: string;
  task: string;
  modality: 'definite' | 'tentative';
  owner: {
    text: string | null;
    basis: string;
  };
  deadline: string | null;
  quote: string;
  utterance_id: string;
  start_ms: number;
}

interface ActionItemsPanelProps {
  actionItems: ActionItemData[];
  onSelectAction?: (utteranceId: string) => void;
  selectedUtteranceId?: string | null;
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const ActionItemsPanel: React.FC<ActionItemsPanelProps> = ({
  actionItems,
  onSelectAction,
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
          Commitments & Action Items ({actionItems.length})
        </h3>
        <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
          Follow-up Tracking
        </span>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {actionItems.length === 0 ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '13px' }}>
            No explicit commitments or follow-up items were identified in this call.
          </div>
        ) : (
          actionItems.map((act) => {
            const isSelected = selectedUtteranceId === act.utterance_id;
            const ownerDisplay = act.owner.text || 'Not specified';
            const deadlineDisplay = act.deadline || 'Not specified';

            return (
              <div
                key={act.id}
                onClick={() => onSelectAction && onSelectAction(act.utterance_id)}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  backgroundColor: isSelected ? 'var(--color-primary-subtle)' : 'var(--color-surface-sunken)',
                  border: `1px solid ${isSelected ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
                  cursor: onSelectAction ? 'pointer' : 'default',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--color-primary-subtle)',
                        color: 'var(--color-primary)',
                        border: '1px solid var(--color-primary-border)',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}
                    >
                      {act.ref}
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
                      {act.type.replace('_', ' ')} • {act.modality}
                    </span>
                  </div>

                  <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', fontFamily: 'monospace' }}>
                    {formatMs(act.start_ms)}
                  </span>
                </div>

                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: 700,
                    color: 'var(--color-text-primary)',
                    marginBottom: '8px',
                  }}
                >
                  {act.task}
                </div>

                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '16px',
                    fontSize: '12px',
                    color: 'var(--color-text-secondary)',
                    marginBottom: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <User size={13} color="var(--color-text-tertiary)" />
                    <span>Owner: <strong>{ownerDisplay}</strong></span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Calendar size={13} color="var(--color-text-tertiary)" />
                    <span>Deadline: <strong>{deadlineDisplay}</strong></span>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '12px',
                    fontStyle: 'italic',
                    color: 'var(--color-text-tertiary)',
                    borderLeft: '2px solid var(--color-border-strong)',
                    paddingLeft: '8px',
                  }}
                >
                  "{act.quote}"
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
