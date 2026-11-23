import React, { useState } from 'react';
import { X, UserCheck, AlertCircle } from 'lucide-react';
import type { SpeakerInfo } from './TranscriptViewer';

interface SpeakerSwapModalProps {
  speakers: SpeakerInfo[];
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (roles: Record<string, string>) => Promise<void>;
}

export const SpeakerSwapModal: React.FC<SpeakerSwapModalProps> = ({
  speakers,
  isOpen,
  onClose,
  onConfirm,
}) => {
  const currentRep = speakers.find((s) => s.role === 'sales_rep')?.label || speakers[0]?.label || 'A';
  const [selectedRep, setSelectedRep] = useState<string>(currentRep);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    const rolesPayload: Record<string, string> = {};
    speakers.forEach((s) => {
      rolesPayload[s.label] = s.label === selectedRep ? 'sales_rep' : 'customer';
    });

    try {
      await onConfirm(rolesPayload);
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Failed to update speaker roles.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'var(--color-scrim)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '16px',
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-surface-elevated)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '460px',
          padding: '24px',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--color-border)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Confirm Sales Representative
          </h3>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-tertiary)' }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ margin: '0 0 20px 0', fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
          Tone auditing evaluates <strong>only</strong> the Sales Representative. Select which speaker is the sales rep.
          Updating roles will re-run the tone evaluation stages.
        </p>

        {error && (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: '8px',
              backgroundColor: 'var(--error-bg)',
              color: 'var(--error-fg)',
              border: '1px solid var(--error-border)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '13px',
              marginBottom: '16px',
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
            {speakers.map((s) => {
              const isSelected = selectedRep === s.label;
              return (
                <label
                  key={s.label}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: '10px',
                    border: `1px solid ${
                      isSelected ? 'var(--color-primary)' : 'var(--color-border)'
                    }`,
                    backgroundColor: isSelected
                      ? 'var(--color-primary-subtle)'
                      : 'var(--color-surface)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <input
                      type="radio"
                      name="sales_rep_choice"
                      value={s.label}
                      checked={isSelected}
                      onChange={() => setSelectedRep(s.label)}
                      style={{ accentColor: 'var(--color-primary)' }}
                    />
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        Speaker {s.label}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                        Turn count: {s.turn_count} • Talk time: {(s.talk_time_ms / 1000).toFixed(1)}s
                      </div>
                    </div>
                  </div>
                  {isSelected && (
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        color: 'var(--color-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <UserCheck size={14} /> Assigned Rep
                    </span>
                  )}
                </label>
              );
            })}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-secondary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'var(--color-primary)',
                color: 'var(--color-on-primary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {isSubmitting ? 'Updating...' : 'Save & Re-evaluate'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
