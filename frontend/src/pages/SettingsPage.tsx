import React, { useState, useEffect } from 'react';
import { apiRequest } from '../api/client';
import { 
  RotateCcw, 
  Save, 
  Plus, 
  Trash2, 
  Check, 
  AlertCircle,
  Info
} from 'lucide-react';

interface Criterion {
  id?: string;
  label: string;
  description?: string;
  enabled: boolean;
  custom: boolean;
}

interface SettingsPayload {
  tone: {
    criteria: Criterion[];
    sensitivity: 'low' | 'medium' | 'high';
    guidance: string;
  };
  actions: {
    types: {
      commitments: boolean;
      follow_ups: boolean;
      information_promised: boolean;
      customer_tasks: boolean;
    };
    include_tentative: boolean;
    owner_rule: 'explicit_or_committing_speaker' | 'explicit_only';
    capture_relative_deadlines: boolean;
    guidance: string;
  };
}

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<SettingsPayload | null>(null);
  const [version, setVersion] = useState<number>(1);
  const [source, setSource] = useState<string>('default');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // New custom criterion state
  const [newLabel, setNewLabel] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await apiRequest<{ version: number; source: string; config: SettingsPayload }>('/settings');
      setConfig(res.config);
      setVersion(res.version);
      setSource(res.source);
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to load settings', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setMessage(null);

    try {
      const res = await apiRequest<{ version: number; source: string; config: SettingsPayload }>('/settings', {
        method: 'PUT',
        body: JSON.stringify(config),
      });
      setConfig(res.config);
      setVersion(res.version);
      setSource(res.source);
      setMessage({ text: `Settings saved successfully as version ${res.version}.`, type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to save settings', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset all analysis settings to default values?')) return;
    setSaving(true);
    setMessage(null);

    try {
      const res = await apiRequest<{ version: number; source: string; config: SettingsPayload }>('/settings/reset', {
        method: 'POST',
      });
      setConfig(res.config);
      setVersion(res.version);
      setSource(res.source);
      setMessage({ text: `Settings reset to defaults (now version ${res.version}).`, type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message || 'Failed to reset settings', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const toggleCriterion = (idx: number) => {
    if (!config) return;
    const updated = [...config.tone.criteria];
    updated[idx].enabled = !updated[idx].enabled;
    setConfig({
      ...config,
      tone: { ...config.tone, criteria: updated },
    });
  };

  const removeCustomCriterion = (idx: number) => {
    if (!config) return;
    const updated = config.tone.criteria.filter((_, i) => i !== idx);
    setConfig({
      ...config,
      tone: { ...config.tone, criteria: updated },
    });
  };

  const addCustomCriterion = () => {
    if (!config || !newLabel.trim()) return;
    const newCriterion: Criterion = {
      label: newLabel.trim(),
      description: newLabel.trim(),
      enabled: true,
      custom: true,
    };
    setConfig({
      ...config,
      tone: { ...config.tone, criteria: [...config.tone.criteria, newCriterion] },
    });
    setNewLabel('');
    setShowAddModal(false);
  };

  if (loading || !config) {
    return <div style={{ padding: '60px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>Loading settings...</div>;
  }

  const customCriteriaCount = config.tone.criteria.filter((c) => c.custom).length;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div style={{ minWidth: 0, flex: '1 1 240px' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--color-text-primary)' }}>
            Analysis Settings & Criteria
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Configure tone evaluation criteria, detection sensitivity, and follow-up tracking rules.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <button
            type="button"
            onClick={handleReset}
            disabled={saving}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            Reset Defaults
          </button>

          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              backgroundColor: 'var(--color-primary)',
              color: 'var(--color-on-primary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: saving ? 'not-allowed' : 'pointer',
            }}
          >
            <Save size={14} />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Version Banner */}
      <div
        style={{
          padding: '12px 16px',
          borderRadius: '10px',
          backgroundColor: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
          fontSize: '13px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
          <Info size={16} color="var(--color-primary)" />
          <span>Active Profile: <strong>Version {version}</strong> ({source})</span>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
          Changes apply to subsequent analyses (past results stay immutable).
        </span>
      </div>

      {message && (
        <div
          style={{
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            backgroundColor: message.type === 'success' ? 'var(--success-bg)' : 'var(--error-bg)',
            color: message.type === 'success' ? 'var(--success-fg)' : 'var(--error-fg)',
            border: `1px solid ${message.type === 'success' ? 'var(--success-border)' : 'var(--error-border)'}`,
            fontSize: '13px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {message.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Section 1: Sensitivity */}
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          padding: '20px',
          marginBottom: '20px',
        }}
      >
        <h3 style={{ margin: '0 0 6px 0', fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Detection Sensitivity
        </h3>
        <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
          Determines the severity threshold required for representative behavior to trigger a RED verdict.
        </p>

        <div className="settings-sensitivity-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
          {(['low', 'medium', 'high'] as const).map((level) => {
            const isSelected = config.tone.sensitivity === level;
            const descriptions: Record<string, string> = {
              low: 'Only flag severe violations (Severity 3). Tolerates minor pushback.',
              medium: 'Flag moderate and severe violations (Severity ≥ 2). Recommended standard.',
              high: 'Strict threshold. Any impolite or dismissive remark (Severity ≥ 1) flags RED.',
            };

            return (
              <button
                key={level}
                type="button"
                onClick={() =>
                  setConfig({
                    ...config,
                    tone: { ...config.tone, sensitivity: level },
                  })
                }
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  border: `2px solid ${isSelected ? 'var(--color-primary)' : 'var(--color-border)'}`,
                  backgroundColor: isSelected ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, textTransform: 'capitalize', color: isSelected ? 'var(--color-primary)' : 'var(--color-text-primary)' }}>
                    {level} Sensitivity
                  </span>
                  {isSelected && <Check size={16} color="var(--color-primary)" />}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', lineHeight: 1.4 }}>
                  {descriptions[level]}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Section 1b: Minimum Confidence Slider */}
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          padding: '20px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Minimum Evaluation Confidence Threshold
          </h3>
          <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--color-primary)' }}>
            {Math.round(((config.tone as any).min_confidence ?? 0.70) * 100)}%
          </span>
        </div>
        <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
          Calls with evaluation confidence below this threshold will be flagged as NEEDS_REVIEW / Ambiguous instead of issuing a final RED verdict.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>50%</span>
          <input
            type="range"
            min="0.50"
            max="0.95"
            step="0.05"
            value={(config.tone as any).min_confidence ?? 0.70}
            onChange={(e) =>
              setConfig({
                ...config,
                tone: { ...config.tone, min_confidence: parseFloat(e.target.value) } as any,
              })
            }
            style={{ flex: 1, accentColor: 'var(--color-primary)', cursor: 'pointer' }}
          />
          <span style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>95%</span>
        </div>
      </div>

      {/* Section 2: Tone Criteria */}
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          padding: '20px',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Tone Evaluation Criteria
            </h3>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              Select which behavioral criteria are actively flagged during audit.
            </p>
          </div>

          {customCriteriaCount < 5 && (
            <button
              type="button"
              onClick={() => setShowAddModal(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '6px',
                border: '1px solid var(--color-primary-border)',
                backgroundColor: 'var(--color-primary-subtle)',
                color: 'var(--color-primary)',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Plus size={14} /> Add Custom Criterion
            </button>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {config.tone.criteria.map((c, idx) => (
            <div
              key={c.id || idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: 'var(--color-surface-sunken)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <input
                  type="checkbox"
                  checked={c.enabled}
                  onChange={() => toggleCriterion(idx)}
                  style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
                />
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                    {c.label} {c.custom && <span style={{ fontSize: '11px', color: 'var(--color-primary)', fontWeight: 500 }}>(Custom)</span>}
                  </div>
                  {c.description && (
                    <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
                      {c.description}
                    </div>
                  )}
                </div>
              </div>

              {c.custom && (
                <button
                  type="button"
                  onClick={() => removeCustomCriterion(idx)}
                  style={{ background: 'none', border: 'none', color: 'var(--error-fg)', cursor: 'pointer', padding: '4px' }}
                  title="Remove custom criterion"
                >
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Section 3: Action Item Tracking */}
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          padding: '20px',
        }}
      >
        <h3 style={{ margin: '0 0 6px 0', fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
          Action Item & Commitment Tracking
        </h3>
        <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
          Configure extraction rules for promises and follow-up commitments.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={config.actions.include_tentative}
              onChange={(e) =>
                setConfig({
                  ...config,
                  actions: { ...config.actions, include_tentative: e.target.checked },
                })
              }
              style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
            />
            <span>Include tentative commitments ("we might", "maybe", non-binding remarks)</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={config.actions.types.customer_tasks}
              onChange={(e) =>
                setConfig({
                  ...config,
                  actions: {
                    ...config.actions,
                    types: { ...config.actions.types, customer_tasks: e.target.checked },
                  },
                })
              }
              style={{ width: '16px', height: '16px', accentColor: 'var(--color-primary)' }}
            />
            <span>Track customer tasks (commitments made by the customer)</span>
          </label>

          <div style={{ marginTop: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Owner Attribution Policy:
            </span>
            <div style={{ display: 'flex', gap: '12px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="owner_rule"
                  checked={config.actions.owner_rule === 'explicit_or_committing_speaker'}
                  onChange={() =>
                    setConfig({
                      ...config,
                      actions: { ...config.actions, owner_rule: 'explicit_or_committing_speaker' },
                    })
                  }
                  style={{ accentColor: 'var(--color-primary)' }}
                />
                <span>Explicit name or committing speaker role</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                <input
                  type="radio"
                  name="owner_rule"
                  checked={config.actions.owner_rule === 'explicit_only'}
                  onChange={() =>
                    setConfig({
                      ...config,
                      actions: { ...config.actions, owner_rule: 'explicit_only' },
                    })
                  }
                  style={{ accentColor: 'var(--color-primary)' }}
                />
                <span>Explicit names only (null if no person named)</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Add Custom Criterion Modal */}
      {showAddModal && (
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
              maxWidth: '420px',
              padding: '24px',
              boxShadow: 'var(--shadow-lg)',
            }}
          >
            <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 700 }}>Add Custom Criterion</h3>
            <p style={{ margin: '0 0 16px 0', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
              Specify a behavioral criterion to evaluate (e.g. "Condescending", "Impatient", "Defensive").
            </p>

            <input
              type="text"
              placeholder="Criterion label (e.g. Condescending)..."
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                border: '1px solid var(--color-border-strong)',
                fontSize: '14px',
                marginBottom: '20px',
                boxSizing: 'border-box',
              }}
              autoFocus
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid var(--color-border)',
                  backgroundColor: 'var(--color-surface)',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={addCustomCriterion}
                disabled={!newLabel.trim()}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: 'var(--color-primary)',
                  color: 'var(--color-on-primary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: !newLabel.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                Add Criterion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
