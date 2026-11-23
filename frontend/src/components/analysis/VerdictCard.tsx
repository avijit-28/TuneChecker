import React from 'react';
import { AlertOctagon, CheckCircle2, ShieldAlert, UserCheck } from 'lucide-react';

interface VerdictCardProps {
  verdict: 'RED' | 'GREEN' | null;
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

  const badgeBg = isRed
    ? 'var(--tone-red-bg)'
    : isGreen
    ? 'var(--tone-green-bg)'
    : 'var(--tone-none-bg)';
  const badgeFg = isRed
    ? 'var(--tone-red-fg)'
    : isGreen
    ? 'var(--tone-green-fg)'
    : 'var(--tone-none-solid)';
  const badgeBorder = isRed
    ? 'var(--tone-red-border)'
    : isGreen
    ? 'var(--tone-green-border)'
    : 'var(--tone-none-border)';

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: '16px',
        padding: '24px',
        border: `1px solid ${isRed ? 'var(--tone-red-border)' : 'var(--color-border)'}`,
        boxShadow: isRed ? 'var(--shadow-md)' : 'var(--shadow-sm)',
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
            {isRed ? <AlertOctagon size={20} /> : isGreen ? <CheckCircle2 size={20} /> : null}
            <span>{verdict ? `${verdict} TONE VERDICT` : 'NOT ANALYZED'}</span>
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
          backgroundColor: isRed ? 'rgba(180, 35, 24, 0.04)' : 'var(--color-surface-sunken)',
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
