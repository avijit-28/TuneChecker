import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { VerdictCard } from '../components/analysis/VerdictCard';
import { EvidencePanel } from '../components/analysis/EvidencePanel';
import { ActionItemsPanel } from '../components/analysis/ActionItemsPanel';
import { TranscriptViewer } from '../components/transcript/TranscriptViewer';
import { SpeakerSwapModal } from '../components/transcript/SpeakerSwapModal';
import { 
  Download, 
  Trash2, 
  ArrowLeft, 
  FileText, 
  Clock, 
  HardDrive 
} from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [callDetail, setCallDetail] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [transcript, setTranscript] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [highlightedUtteranceId, setHighlightedUtteranceId] = useState<string | null>(null);
  const [isSwapModalOpen, setIsSwapModalOpen] = useState(false);

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    try {
      const [detailRes, analysisRes, transcriptRes] = await Promise.all([
        apiRequest<any>(`/calls/${id}`),
        apiRequest<any>(`/calls/${id}/analysis`),
        apiRequest<any>(`/calls/${id}/transcript`),
      ]);

      setCallDetail(detailRes);
      setAnalysis(analysisRes);
      setTranscript(transcriptRes);
    } catch (err: any) {
      setError(err?.message || 'Failed to load call audit data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleSelectEvidenceOrAction = (utteranceId: string) => {
    setHighlightedUtteranceId(utteranceId);
    const element = document.getElementById(`utt-${utteranceId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleSpeakerRolesConfirm = async (roles: Record<string, string>) => {
    if (!id) return;
    await apiRequest(`/calls/${id}/speaker-roles`, {
      method: 'PUT',
      body: JSON.stringify({ roles }),
    });
    // Redirect to processing page to show re-evaluation stepper
    navigate(`/calls/${id}/processing`);
  };

  const handleDelete = async () => {
    if (!id) return;
    if (!window.confirm('Are you sure you want to delete this call and its audit findings permanently?')) {
      return;
    }
    try {
      await apiRequest(`/calls/${id}`, { method: 'DELETE' });
      navigate('/history');
    } catch (err: any) {
      alert(`Deletion failed: ${err.message}`);
    }
  };

  const handleExport = (format: 'markdown' | 'json') => {
    window.open(`/api/v1/calls/${id}/export?format=${format}`, '_blank');
  };

  if (loading) {
    return (
      <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Loading call audit results...
      </div>
    );
  }

  if (error || !callDetail) {
    return (
      <div style={{ maxWidth: '600px', margin: '40px auto', textAlign: 'center' }}>
        <h2 style={{ color: 'var(--error-fg)', marginBottom: '8px' }}>Failed to Load Analysis</h2>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>{error}</p>
        <button
          type="button"
          onClick={() => navigate('/history')}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            border: 'none',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Return to History
        </button>
      </div>
    );
  }

  const durationSec = callDetail.duration_ms ? (callDetail.duration_ms / 1000).toFixed(1) : 'N/A';
  const sizeMb = (callDetail.size_bytes / (1024 * 1024)).toFixed(1);

  return (
    <div>
      {/* Top Header */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '24px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <button
              type="button"
              onClick={() => navigate('/history')}
              style={{
                background: 'none',
                border: 'none',
                padding: '4px',
                cursor: 'pointer',
                color: 'var(--color-text-tertiary)',
              }}
              title="Back to History"
            >
              <ArrowLeft size={18} />
            </button>
            <h1 style={{ fontSize: '22px', fontWeight: 800, margin: 0, color: 'var(--color-text-primary)' }}>
              {callDetail.name}
            </h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '12px', color: 'var(--color-text-tertiary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={13} /> {durationSec}s duration
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <HardDrive size={13} /> {sizeMb} MB
            </span>
            <span>ID: {callDetail.id.slice(0, 8)}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={() => handleExport('markdown')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <FileText size={15} color="var(--color-primary)" />
            Export Markdown
          </button>

          <button
            type="button"
            onClick={() => handleExport('json')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Download size={15} color="var(--color-primary)" />
            Export JSON
          </button>

          <button
            type="button"
            onClick={handleDelete}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              border: '1px solid var(--error-border)',
              backgroundColor: 'var(--error-bg)',
              color: 'var(--error-fg)',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Trash2 size={15} />
            Delete
          </button>
        </div>
      </div>

      {/* Verdict Card */}
      {analysis && (
        <div style={{ marginBottom: '24px' }}>
          <VerdictCard
            verdict={analysis.verdict}
            confidenceLevel={analysis.confidence?.level || 'low'}
            explanation={analysis.explanation || 'No explanation available.'}
            repLabel={analysis.sales_rep?.label}
            limitedEvidenceReason={analysis.limited_evidence_reason}
            settingsSnapshot={analysis.settings_snapshot}
          />
        </div>
      )}

      {/* Main Analysis & Transcript Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
          alignItems: 'start',
        }}
      >
        {/* Left Column: Evidence & Action Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {analysis && (
            <>
              <EvidencePanel
                evidence={analysis.evidence || []}
                onSelectEvidence={handleSelectEvidenceOrAction}
                selectedUtteranceId={highlightedUtteranceId}
              />
              <ActionItemsPanel
                actionItems={analysis.action_items || []}
                onSelectAction={handleSelectEvidenceOrAction}
                selectedUtteranceId={highlightedUtteranceId}
              />
            </>
          )}
        </div>

        {/* Right Column: Full Transcript */}
        <div>
          {transcript && (
            <TranscriptViewer
              utterances={transcript.utterances || []}
              speakers={transcript.speakers || []}
              highlightedUtteranceId={highlightedUtteranceId}
              onChangeRolesClick={() => setIsSwapModalOpen(true)}
            />
          )}
        </div>
      </div>

      {/* Speaker Swap Modal */}
      {transcript && (
        <SpeakerSwapModal
          speakers={transcript.speakers || []}
          isOpen={isSwapModalOpen}
          onClose={() => setIsSwapModalOpen(false)}
          onConfirm={handleSpeakerRolesConfirm}
        />
      )}
    </div>
  );
};
