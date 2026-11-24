import React from 'react';
import { AlertOctagon, CheckCircle2, AlertTriangle, ShieldAlert, UserCheck } from 'lucide-react';

interface VerdictCardProps {
  verdict: 'RED' | 'GREEN' | 'NEEDS_REVIEW' | null;
  confidenceLevel: string;
  explanation: string;
  repLabel?: string | null;
  limitedEvidenceReason?: string | null;
  settingsSnapshot?: { version: number; sensitivity: string };
}

export const VerdictCard: React.FC<VerdictCardProps> = ({
  verdict,
  confidenceLevel,
  explanation,
  repLabel,
  limitedEvidenceReason,
  settingsSnapshot,
}) => {
  const isRed = verdict === 'RED';
  const isGreen = verdict === 'GREEN';
  const isNeedsReview = verdict === 'NEEDS_REVIEW';

  const badgeBg = isRed
    ? 'var(--tone-red-bg)'
    : isGreen
    ? 'var(--tone-green-bg)'
    : isNeedsReview
    ? 'var(--tone-amber-bg, #FEF3C7)'
    : 'var(--tone-none-bg)';

  const badgeFg = isRed
    ? 'var(--tone-red-fg)'
    : isGreen
    ? 'var(--tone-green-fg)'
    : isNeedsReview
    ? 'var(--tone-amber-fg, #B45309)'
    : 'var(--tone-none-solid)';

  const badgeBorder = isRed
    ? 'var(--tone-red-border)'
    : isGreen
    ? 'var(--tone-green-border)'
    : isNeedsReview
    ? 'var(--tone-amber-border, #FCD34D)'
    : 'var(--tone-none-border)';

  const containerBorder = isRed
    ? 'var(--tone-red-border)'
    : isNeedsReview
    ? 'var(--tone-amber-border, #FCD34D)'
    : 'var(--color-border)';

  const containerShadow = isRed
    ? 'var(--shadow-md)'
    : isNeedsReview
    ? '0 1px 3px rgba(217, 119, 6, 0.12)'
    : 'var(--shadow-sm)';

  const verdictLabel = isRed
    ? 'RED TONE VERDICT'
    : isGreen
    ? 'GREEN TONE VERDICT'
    : isNeedsReview
    ? 'NEEDS REVIEW TONE VERDICT'
    : 'NOT ANALYZED';

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: '16px',
        padding: '24px',
        border: `1px solid ${containerBorder}`,
        boxShadow: containerShadow,
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              borderRadius: '24px',
              backgroundColor: badgeBg,
              color: badgeFg,
              border: `1px solid ${badgeBorder}`,
              fontSize: '16px',
              fontWeight: 800,
              letterSpacing: '0.04em',
            }}
          >
            {isRed ? (
              <AlertOctagon size={20} />
            ) : isGreen ? (
              <CheckCircle2 size={20} />
            ) : isNeedsReview ? (
              <AlertTriangle size={20} />
            ) : null}
            <span>{verdictLabel}</span>
          </div>

          <span
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--color-text-secondary)',
              backgroundColor: 'var(--color-surface-sunken)',
              padding: '4px 10px',
              borderRadius: '12px',
            }}
          >
            Confidence: <strong style={{ textTransform: 'capitalize' }}>{confidenceLevel}</strong>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
          {repLabel && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <UserCheck size={14} /> Rep: <strong>Speaker {repLabel}</strong>
            </span>
          )}
          {settingsSnapshot && (
            <span>
              Settings v{settingsSnapshot.version} ({settingsSnapshot.sensitivity} sensitivity)
            </span>
          )}
        </div>
      </div>

      <div
        style={{
          padding: '16px',
          borderRadius: '10px',
          backgroundColor: isRed
            ? 'rgba(180, 35, 24, 0.04)'
            : isNeedsReview
            ? 'rgba(217, 119, 6, 0.05)'
            : 'var(--color-surface-sunken)',
          fontSize: '14px',
          lineHeight: 1.6,
          color: 'var(--color-text-primary)',
        }}
      >
        {explanation}
      </div>

      {limitedEvidenceReason && (
        <div
          style={{
            marginTop: '12px',
            fontSize: '12px',
            color: 'var(--warning-fg)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <ShieldAlert size={14} />
          <span>Note: {limitedEvidenceReason}</span>
        </div>
      )}
    </div>
  );
};
