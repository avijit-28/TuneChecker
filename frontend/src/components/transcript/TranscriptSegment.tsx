import React from 'react';
import { RoleBadge } from './RoleBadge';

export interface UtteranceItem {
  id: string;
  idx: number;
  speaker_label: string;
  start_ms: number;
  end_ms: number;
  text: string;
  asr_confidence?: number | null;
}

interface TranscriptSegmentProps {
  utterance: UtteranceItem;
  speakerRole?: string;
  isRep: boolean;
  isHighlighted?: boolean;
  searchQuery?: string;
  onSelect?: () => void;
}

function formatMs(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const mins = Math.floor(totalSec / 60);
  const secs = totalSec % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export const TranscriptSegment: React.FC<TranscriptSegmentProps> = ({
  utterance,
  speakerRole = 'unknown',
  isRep,
  isHighlighted = false,
  searchQuery = '',
  onSelect,
}) => {
  const timeLabel = `${formatMs(utterance.start_ms)} - ${formatMs(utterance.end_ms)}`;

  const renderTextWithHighlights = (text: string) => {
    if (!searchQuery) return text;
    const parts = text.split(new RegExp(`(${searchQuery})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === searchQuery.toLowerCase() ? (
        <mark
          key={i}
          style={{
            backgroundColor: 'var(--highlight-search)',
            padding: '1px 3px',
            borderRadius: '2px',
          }}
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div
      id={`utt-${utterance.id}`}
      onClick={onSelect}
      style={{
        display: 'flex',
        gap: '14px',
        padding: '12px 16px',
        borderRadius: '8px',
        backgroundColor: isHighlighted
          ? 'var(--color-primary-subtle)'
          : isRep
          ? 'var(--speaker-rep-bg)'
          : 'var(--speaker-customer-bg)',
        borderLeft: `4px solid ${
          isRep ? 'var(--speaker-rep-bar)' : 'var(--speaker-customer-bar)'
        }`,
        transition: 'background-color 0.15s ease',
        cursor: onSelect ? 'pointer' : 'default',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '6px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '13px',
                fontWeight: 700,
                color: isRep ? 'var(--color-primary)' : 'var(--color-text-primary)',
              }}
            >
              Speaker {utterance.speaker_label}
            </span>
            <RoleBadge role={speakerRole} />
          </div>

          <span
            style={{
              fontSize: '11px',
              color: 'var(--color-text-tertiary)',
              fontFamily: 'monospace',
            }}
          >
            {timeLabel}
          </span>
        </div>

        <p
          style={{
            margin: 0,
            fontSize: '14px',
            lineHeight: 1.5,
            color: 'var(--color-text-primary)',
          }}
        >
          {renderTextWithHighlights(utterance.text)}
        </p>
      </div>
    </div>
  );
};
