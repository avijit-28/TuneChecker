import React from 'react';
import { Play, Volume2 } from 'lucide-react';
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
  isPlaying?: boolean;
  searchQuery?: string;
  activeQuote?: string | null;
  onSelect?: () => void;
  onPlayFromTimestamp?: (timeSec: number) => void;
}

function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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
  isPlaying = false,
  searchQuery = '',
  activeQuote = null,
  onSelect,
  onPlayFromTimestamp,
}) => {
  const timeLabel = `${formatMs(utterance.start_ms)} - ${formatMs(utterance.end_ms)}`;

  const renderSearchHighlights = (text: string) => {
    if (!searchQuery.trim()) return text;
    const escaped = escapeRegExp(searchQuery.trim());
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === searchQuery.trim().toLowerCase() ? (
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

  const renderTextWithHighlights = (text: string) => {
    if (isHighlighted && activeQuote && activeQuote.trim()) {
      const cleanQuote = activeQuote.trim();
      const escapedQuote = escapeRegExp(cleanQuote);
      const regex = new RegExp(`(${escapedQuote})`, 'i');
      const match = text.match(regex);
      if (match && match.index !== undefined) {
        const start = match.index;
        const end = start + match[0].length;
        const before = text.slice(0, start);
        const highlightedSpan = text.slice(start, end);
        const after = text.slice(end);
        return (
          <>
            {renderSearchHighlights(before)}
            <mark
              className="bg-amber-100 text-amber-900 px-0.5 rounded"
              style={{
                backgroundColor: 'var(--tone-amber-bg, #FEF3C7)',
                color: 'var(--tone-amber-fg, #B45309)',
                border: '1px solid var(--tone-amber-border, #FCD34D)',
                padding: '1px 4px',
                borderRadius: '4px',
                fontWeight: 600,
              }}
            >
              {renderSearchHighlights(highlightedSpan)}
            </mark>
            {renderSearchHighlights(after)}
          </>
        );
      }
    }
    return renderSearchHighlights(text);
  };

  const handleClick = () => {
    if (onPlayFromTimestamp) {
      onPlayFromTimestamp(utterance.start_ms / 1000);
    }
    if (onSelect) {
      onSelect();
    }
  };

  return (
    <div
      id={`utt-${utterance.id}`}
      onClick={handleClick}
      style={{
        display: 'flex',
        gap: '14px',
        padding: '12px 16px',
        borderRadius: '8px',
        backgroundColor: isPlaying
          ? 'var(--color-primary-subtle)'
          : isHighlighted
          ? 'var(--color-primary-subtle)'
          : isRep
          ? 'var(--speaker-rep-bg)'
          : 'var(--speaker-customer-bg)',
        borderLeft: `4px solid ${
          isPlaying
            ? 'var(--color-primary)'
            : isRep
            ? 'var(--speaker-rep-bar)'
            : 'var(--speaker-customer-bar)'
        }`,
        boxShadow: isPlaying
          ? '0 0 0 2px var(--color-primary), var(--shadow-sm)'
          : isHighlighted
          ? '0 0 0 1px var(--color-primary-border)'
          : undefined,
        transition: 'all 0.15s ease',
        cursor: 'pointer',
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
                color: isPlaying
                  ? 'var(--color-primary)'
                  : isRep
                  ? 'var(--color-primary)'
                  : 'var(--color-text-primary)',
              }}
            >
              Speaker {utterance.speaker_label}
            </span>
            <RoleBadge role={speakerRole} />
            {isPlaying && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                  fontSize: '10px',
                  fontWeight: 700,
                  color: 'var(--color-primary)',
                  backgroundColor: 'var(--color-surface)',
                  padding: '1px 6px',
                  borderRadius: '4px',
                  border: '1px solid var(--color-primary-border)',
                }}
              >
                <Volume2 size={11} /> PLAYING
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onPlayFromTimestamp?.(utterance.start_ms / 1000);
              onSelect?.();
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '2px 6px',
              borderRadius: '4px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              fontSize: '11px',
              color: isPlaying ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              fontFamily: 'monospace',
              cursor: 'pointer',
              fontWeight: 500,
            }}
            title={`Seek and play from ${formatMs(utterance.start_ms)}`}
          >
            <Play size={10} fill="currentColor" />
            {timeLabel}
          </button>
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
