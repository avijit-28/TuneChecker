import React, { useState } from 'react';
import { Activity, Waves, Volume2, ShieldCheck, ChevronDown, ChevronUp, Cpu, CheckCircle2 } from 'lucide-react';

export interface AudioReportData {
  call_id: string;
  filename: string;
  duration_ms: number;
  status: string;
  verdict: string | null;
  audio_rectification: {
    algorithm: string;
    filter_string: string;
    max_gain_boost_db: number;
    measured_rms_gain_db: number;
    snr_improvement_db: number;
    dynamic_range_compressed: boolean;
    vad_sensitivity_threshold: number;
    vad_speech_pad_ms: number;
  };
  speech_recovery: {
    rectified_utterances: number;
    baseline_unnormalized_utterances: number;
    recovered_utterances: number;
    speech_recovery_rate_pct: number;
    rectified_word_count: number;
    baseline_word_count: number;
    recovered_word_count: number;
    word_recovery_rate_pct: number;
  };
  accuracy_and_confidence: {
    transcription_confidence_pct: number;
    diarization_confidence_pct: number;
    language_detected: string;
    language_confidence_pct: number;
    acoustic_clustering_method: string;
    speaker_attribution?: {
      sales_rep: string;
      customer: string;
      confidence: string;
    };
  };
  findings_summary: {
    tone_verdict: string;
    verified_tone_evidence_count: number;
    commitments_and_actions_count: number;
    calibrator_status: string;
  };
}

interface AudioQualityReportCardProps {
  report: AudioReportData | null;
}

export const AudioQualityReportCard: React.FC<AudioQualityReportCardProps> = ({ report }) => {
  const [expanded, setExpanded] = useState(false);

  if (!report) return null;

  const { audio_rectification, speech_recovery, accuracy_and_confidence, findings_summary } = report;

  return (
    <div
      style={{
        marginTop: '24px',
        backgroundColor: 'var(--color-surface)',
        borderRadius: '16px',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--color-divider)',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px',
          background: 'linear-gradient(180deg, var(--color-surface) 0%, var(--color-surface-sunken) 100%)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              backgroundColor: 'var(--color-primary-subtle)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Activity size={20} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Audio Rectification & Quality Report
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              Adaptive Telephone Speech Enhancement & Transcription Precision
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '12px',
              backgroundColor: 'var(--success-bg)',
              color: 'var(--success-fg)',
              border: '1px solid var(--success-border)',
              fontSize: '11px',
              fontWeight: 700,
            }}
          >
            <CheckCircle2 size={13} />
            +{audio_rectification.measured_rms_gain_db} dB Dynamic Gain
          </span>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-secondary)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            {expanded ? 'Less Info' : 'Full Diagnostics'}
          </button>
        </div>
      </div>

      {/* 4 Metric KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          padding: '20px 24px',
        }}
      >
        {/* Metric 1 */}
        <div
          style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-primary)' }}>
            <Waves size={16} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Speech Recovery Rate
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            +{speech_recovery.speech_recovery_rate_pct}%
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            <strong>{speech_recovery.rectified_utterances}</strong> turns captured (vs {speech_recovery.baseline_unnormalized_utterances} unnormalized, +{speech_recovery.recovered_utterances} turns restored)
          </div>
        </div>

        {/* Metric 2 */}
        <div
          style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#10B981' }}>
            <ShieldCheck size={16} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Transcription Accuracy
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            {accuracy_and_confidence.transcription_confidence_pct}%
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Faster-Whisper Silero VAD tuned • <strong>{speech_recovery.rectified_word_count}</strong> words converted (+{speech_recovery.word_recovery_rate_pct}%)
          </div>
        </div>

        {/* Metric 3 */}
        <div
          style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#8B5CF6' }}>
            <Cpu size={16} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Acoustic Diarization
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            {accuracy_and_confidence.diarization_confidence_pct}%
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Spectral Clustering: Rep ({accuracy_and_confidence.speaker_attribution?.sales_rep}) vs Customer ({accuracy_and_confidence.speaker_attribution?.customer})
          </div>
        </div>

        {/* Metric 4 */}
        <div
          style={{
            padding: '16px',
            borderRadius: '12px',
            backgroundColor: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#F59E0B' }}>
            <Volume2 size={16} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              Audio SNR Enhancement
            </span>
          </div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--color-text-primary)' }}>
            +{audio_rectification.snr_improvement_db} dB
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Faint telephone earpiece compression (-32 dBFS leveling to -14 dBFS)
          </div>
        </div>
      </div>

      {/* Expanded Diagnostics Details */}
      {expanded && (
        <div
          style={{
            padding: '20px 24px',
            borderTop: '1px solid var(--color-divider)',
            backgroundColor: 'var(--color-surface)',
          }}
        >
          <h4 style={{ margin: '0 0 14px 0', fontSize: '13px', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Deep Pipeline Processing Parameters
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              <div><strong>Audio Normalizer:</strong> {audio_rectification.algorithm}</div>
              <div><strong>Filter Pipeline:</strong> <code>{audio_rectification.filter_string}</code></div>
              <div><strong>Max Dynamic Gain Boost:</strong> +{audio_rectification.max_gain_boost_db} dB</div>
              <div><strong>VAD Sensitivity Threshold:</strong> {audio_rectification.vad_sensitivity_threshold} (400ms padding)</div>
            </div>

            <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
              <div><strong>Language Detected:</strong> {accuracy_and_confidence.language_detected.toUpperCase()} (Confidence: {accuracy_and_confidence.language_confidence_pct}%)</div>
              <div><strong>Verified Tone Violations:</strong> {findings_summary.verified_tone_evidence_count} evidence item(s)</div>
              <div><strong>Commitments Extracted:</strong> {findings_summary.commitments_and_actions_count} action item(s)</div>
              <div><strong>Feedback Calibrator:</strong> {findings_summary.calibrator_status}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
