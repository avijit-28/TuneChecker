import React, { useState } from 'react';
import { Calendar, User, CheckSquare, Sparkles, AlertCircle, Info, Flame } from 'lucide-react';
import type { ActionItemData, CoachingRecommendationData } from '../../types';

export type { ActionItemData, CoachingRecommendationData };

interface ActionItemsPanelProps {
  actionItems: ActionItemData[];
  coachingRecommendations?: CoachingRecommendationData[];
  onSelectAction?: (utteranceId: string, quote?: string) => void;
  selectedUtteranceId?: string | null;
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const ActionItemsPanel: React.FC<ActionItemsPanelProps> = ({
  actionItems = [],
  coachingRecommendations = [],
  onSelectAction,
  selectedUtteranceId,
}) => {
  const [activeTab, setActiveTab] = useState<'all' | 'commitments' | 'coaching'>('all');

  const explicitCommitments = actionItems.filter(
    (item) => item.type !== 'coaching' && item.type !== 'recommendation'
  );

  const derivedCoaching: CoachingRecommendationData[] = [
    ...coachingRecommendations,
    ...actionItems
      .filter((item) => item.type === 'coaching' || item.type === 'recommendation')
      .map((item) => ({
        id: item.id,
        ref: item.ref.startsWith('C') ? item.ref : `C${item.ref.replace(/\D/g, '') || '1'}`,
        category: (item as any).category || 'sales_technique',
        recommendation: item.task,
        context_quote: item.quote,
        severity: ((item as any).severity as any) || 'important',
        utterance_id: item.utterance_id,
        start_ms: item.start_ms,
      })),
  ];

  const totalCount = explicitCommitments.length + derivedCoaching.length;

  const renderSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '10px',
              backgroundColor: 'var(--tone-red-bg)',
              color: 'var(--tone-red-fg)',
              border: '1px solid var(--tone-red-border)',
              fontSize: '11px',
              fontWeight: 700,
              textTransform: 'uppercase',
            }}
          >
            <Flame size={11} /> Critical
          </span>
        );
      case 'important':
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '10px',
              backgroundColor: 'var(--tone-amber-bg, #FEF3C7)',
              color: 'var(--tone-amber-fg, #B45309)',
              border: '1px solid var(--tone-amber-border, #FCD34D)',
              fontSize: '11px',
              fontWeight: 700,
              textTransform: 'uppercase',
            }}
          >
            <AlertCircle size={11} /> Important
          </span>
        );
      default:
        return (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 8px',
              borderRadius: '10px',
              backgroundColor: 'var(--color-primary-subtle)',
              color: 'var(--color-primary)',
              border: '1px solid var(--color-primary-border)',
              fontSize: '11px',
              fontWeight: 600,
              textTransform: 'capitalize',
            }}
          >
            <Info size={11} /> Suggestion
          </span>
        );
    }
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: '12px',
        border: '1px solid var(--color-border)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-divider)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Action Items & Coaching ({totalCount})
          </h3>
          <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
            Explicit Commitments & Rep Coaching Recommendations
          </span>
        </div>

        {/* View Toggle Tabs */}
        <div style={{ display: 'flex', gap: '6px' }}>
          {(
            [
              { id: 'all', label: `All (${totalCount})` },
              { id: 'commitments', label: `Commitments (${explicitCommitments.length})` },
              { id: 'coaching', label: `Coaching (${derivedCoaching.length})` },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '4px 10px',
                borderRadius: '16px',
                fontSize: '11px',
                fontWeight: activeTab === tab.id ? 700 : 500,
                border: activeTab === tab.id
                  ? '1px solid var(--color-primary)'
                  : '1px solid var(--color-border)',
                backgroundColor: activeTab === tab.id
                  ? 'var(--color-primary-subtle)'
                  : 'var(--color-surface)',
                color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                cursor: 'pointer',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Section 1: Explicit Commitments & Promises */}
        {(activeTab === 'all' || activeTab === 'commitments') && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '12px',
                paddingBottom: '6px',
                borderBottom: '1px solid var(--color-divider)',
              }}
            >
              <CheckSquare size={15} color="var(--color-primary)" />
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Explicit Commitments & Promises ({explicitCommitments.length})
              </h4>
            </div>

            {explicitCommitments.length === 0 ? (
              <div
                style={{
                  padding: '16px',
                  textAlign: 'center',
                  color: 'var(--color-text-tertiary)',
                  fontSize: '12px',
                  backgroundColor: 'var(--color-surface-sunken)',
                  borderRadius: '8px',
                }}
              >
                No explicit commitments or promise deliverables were identified.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {explicitCommitments.map((act) => {
                  const isSelected = selectedUtteranceId === act.utterance_id;
                  const ownerDisplay = act.owner?.text || 'Not specified';
                  const deadlineDisplay = act.deadline || 'Not specified';

                  return (
                    <div
                      key={act.id}
                      onClick={() => onSelectAction && onSelectAction(act.utterance_id, act.quote)}
                      style={{
                        padding: '12px 14px',
                        borderRadius: '8px',
                        backgroundColor: isSelected
                          ? 'var(--color-primary-subtle)'
                          : 'var(--color-surface-sunken)',
                        border: `1px solid ${
                          isSelected ? 'var(--color-primary-border)' : 'var(--color-border)'
                        }`,
                        cursor: onSelectAction ? 'pointer' : 'default',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '8px',
                        }}
                      >
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

                        <span
                          style={{
                            fontSize: '11px',
                            color: 'var(--color-text-tertiary)',
                            fontFamily: 'monospace',
                          }}
                        >
                          {formatMs(act.start_ms)}
                        </span>
                      </div>

                      <div
                        style={{
                          fontSize: '13px',
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
                          gap: '14px',
                          fontSize: '12px',
                          color: 'var(--color-text-secondary)',
                          marginBottom: '8px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <User size={13} color="var(--color-text-tertiary)" />
                          <span>
                            Owner: <strong>{ownerDisplay}</strong>
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Calendar size={13} color="var(--color-text-tertiary)" />
                          <span>
                            Deadline: <strong>{deadlineDisplay}</strong>
                          </span>
                        </div>
                      </div>

                      {act.quote && (
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
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Section 2: Coaching Recommendations & Opportunities */}
        {(activeTab === 'all' || activeTab === 'coaching') && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginBottom: '12px',
                paddingBottom: '6px',
                borderBottom: '1px solid var(--color-divider)',
              }}
            >
              <Sparkles size={15} color="var(--tone-amber-solid, #D97706)" />
              <h4 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Coaching Recommendations & Opportunities ({derivedCoaching.length})
              </h4>
            </div>

            {derivedCoaching.length === 0 ? (
              <div
                style={{
                  padding: '16px',
                  textAlign: 'center',
                  color: 'var(--color-text-tertiary)',
                  fontSize: '12px',
                  backgroundColor: 'var(--color-surface-sunken)',
                  borderRadius: '8px',
                }}
              >
                No specific coaching recommendations flagged for this conversation.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {derivedCoaching.map((coach) => {
                  const isSelected = Boolean(coach.utterance_id && selectedUtteranceId === coach.utterance_id);

                  return (
                    <div
                      key={coach.id || coach.ref}
                      onClick={() =>
                        coach.utterance_id &&
                        onSelectAction &&
                        onSelectAction(coach.utterance_id, coach.context_quote || undefined)
                      }
                      style={{
                        padding: '12px 14px',
                        borderRadius: '8px',
                        backgroundColor: isSelected
                          ? 'var(--color-primary-subtle)'
                          : 'var(--color-surface-sunken)',
                        border: `1px solid ${
                          isSelected ? 'var(--color-primary-border)' : 'var(--color-border)'
                        }`,
                        cursor: coach.utterance_id && onSelectAction ? 'pointer' : 'default',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: '8px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span
                            style={{
                              padding: '2px 6px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--tone-amber-bg, #FEF3C7)',
                              color: 'var(--tone-amber-fg, #B45309)',
                              border: '1px solid var(--tone-amber-border, #FCD34D)',
                              fontSize: '11px',
                              fontWeight: 700,
                            }}
                          >
                            {coach.ref}
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
                            {coach.category.replace('_', ' ')}
                          </span>
                          {renderSeverityBadge(coach.severity)}
                        </div>

                        {coach.start_ms !== undefined && coach.start_ms !== null && (
                          <span
                            style={{
                              fontSize: '11px',
                              color: 'var(--color-text-tertiary)',
                              fontFamily: 'monospace',
                            }}
                          >
                            {formatMs(coach.start_ms)}
                          </span>
                        )}
                      </div>

                      <div
                        style={{
                          fontSize: '13px',
                          fontWeight: 600,
                          color: 'var(--color-text-primary)',
                          marginBottom: '8px',
                          lineHeight: 1.5,
                        }}
                      >
                        {coach.recommendation}
                      </div>

                      {coach.context_quote && (
                        <div
                          style={{
                            fontSize: '12px',
                            fontStyle: 'italic',
                            color: 'var(--color-text-tertiary)',
                            borderLeft: '2px solid var(--tone-amber-border, #FCD34D)',
                            paddingLeft: '8px',
                          }}
                        >
                          "{coach.context_quote}"
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
