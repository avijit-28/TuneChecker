import React, { useState } from 'react';
import { Search, UserCog, AlertTriangle } from 'lucide-react';
import { TranscriptSegment } from './TranscriptSegment';
import type { UtteranceItem } from './TranscriptSegment';

export type { UtteranceItem };

export interface SpeakerInfo {
  label: string;
  role: string;
  source: 'auto' | 'user';
  status: string;
  level?: string | null;
  talk_time_ms: number;
  turn_count: number;
}

interface TranscriptViewerProps {
  utterances: UtteranceItem[];
  speakers: SpeakerInfo[];
  highlightedUtteranceId?: string | null;
  activeUtteranceId?: string | null;
  onChangeRolesClick?: () => void;
  onSeekToUtterance?: (utterance: UtteranceItem) => void;
  onPlayFromTimestamp?: (timeSec: number) => void;
  autoScroll?: boolean;
  onToggleAutoScroll?: () => void;
  activeQuote?: string | null;
}

export const TranscriptViewer: React.FC<TranscriptViewerProps> = ({
  utterances,
  speakers,
  highlightedUtteranceId,
  activeUtteranceId,
  onChangeRolesClick,
  onSeekToUtterance,
  onPlayFromTimestamp,
  autoScroll,
  onToggleAutoScroll,
  activeQuote,
}) => {
  const [search, setSearch] = useState('');

  const roleMap: Record<string, string> = {};
  speakers.forEach((s) => {
    roleMap[s.label] = s.role;
  });

  const isUncertain = speakers.some((s) => s.status === 'uncertain' || s.status === 'unresolved');

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: '12px',
        border: '1px solid var(--color-border)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}
    >
      {/* Header & Search */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-divider)',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--color-text-primary)' }}>
            Full Call Transcript
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
            ({utterances.length} utterances)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'var(--color-surface-sunken)',
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
            }}
          >
            <Search size={14} color="var(--color-text-tertiary)" />
            <input
              type="text"
              placeholder="Search transcript..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '13px',
                color: 'var(--color-text-primary)',
                outline: 'none',
                width: '130px',
              }}
            />
          </div>

          {onToggleAutoScroll && (
            <button
              type="button"
              onClick={onToggleAutoScroll}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '6px 10px',
                borderRadius: '8px',
                border: `1px solid ${autoScroll ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
                backgroundColor: autoScroll ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
                color: autoScroll ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
              title="Toggle automatic transcript scrolling during audio playback"
            >
              Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
            </button>
          )}

          {onChangeRolesClick && (
            <button
              type="button"
              onClick={onChangeRolesClick}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--color-primary)',
                backgroundColor: 'var(--color-primary-subtle)',
                border: '1px solid var(--color-primary-border)',
                borderRadius: '8px',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <UserCog size={14} />
              Change Roles
            </button>
          )}
        </div>
      </div>

      {/* Uncertainty Notice */}
      {isUncertain && (
        <div
          style={{
            padding: '10px 16px',
            backgroundColor: 'var(--warning-bg)',
            borderBottom: '1px solid var(--warning-border)',
            color: 'var(--warning-fg)',
            fontSize: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={15} />
            <span>Speaker roles were assigned with low confidence. Please verify who is the Sales Rep.</span>
          </div>
          {onChangeRolesClick && (
            <button
              type="button"
              onClick={onChangeRolesClick}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--warning-fg)',
                fontWeight: 700,
                cursor: 'pointer',
                textDecoration: 'underline',
                fontSize: '12px',
              }}
            >
              Confirm Roles
            </button>
          )}
        </div>
      )}

      {/* Utterances list */}
      <div
        style={{
          padding: '16px',
          overflowY: 'auto',
          maxHeight: '600px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {utterances.map((u) => {
          const role = roleMap[u.speaker_label] || 'unknown';
          const isRep = role === 'sales_rep';
          return (
            <TranscriptSegment
              key={u.id}
              utterance={u}
              speakerRole={role}
              isRep={isRep}
              isHighlighted={highlightedUtteranceId === u.id}
              activeQuote={highlightedUtteranceId === u.id ? activeQuote : null}
              isPlaying={activeUtteranceId === u.id}
              searchQuery={search}
              onSelect={() => onSeekToUtterance?.(u)}
              onPlayFromTimestamp={onPlayFromTimestamp}
            />
          );
        })}
      </div>
    </div>
  );
};
