import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { VerdictCard } from '../components/analysis/VerdictCard';
import { EvidencePanel } from '../components/analysis/EvidencePanel';
import { ActionItemsPanel } from '../components/analysis/ActionItemsPanel';
import { AuditorFeedbackCard } from '../components/analysis/AuditorFeedbackCard';
import { AudioQualityReportCard, type AudioReportData } from '../components/analysis/AudioQualityReportCard';
import { TranscriptViewer } from '../components/transcript/TranscriptViewer';
import { SpeakerSwapModal } from '../components/transcript/SpeakerSwapModal';
import { AudioPlayer, type AudioPlayerRef } from '../components/audio/AudioPlayer';
import { 
  Download, 
  Trash2, 
  ArrowLeft, 
  FileText, 
  Clock, 
  HardDrive,
  RotateCcw 
} from 'lucide-react';

export const ResultsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [callDetail, setCallDetail] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [transcript, setTranscript] = useState<any>(null);
  const [report, setReport] = useState<AudioReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [highlightedUtteranceId, setHighlightedUtteranceId] = useState<string | null>(null);
  const [activeQuote, setActiveQuote] = useState<string | null>(null);
  const [activeUtteranceId, setActiveUtteranceId] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [, setIsPlaying] = useState<boolean>(false);
  const [isSwapModalOpen, setIsSwapModalOpen] = useState(false);

  const audioPlayerRef = useRef<AudioPlayerRef | null>(null);
  const prevActiveIdRef = useRef<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    try {
      const detailRes = await apiRequest<any>(`/calls/${id}`);
      setCallDetail(detailRes);

      // If call is still validating, transcribing, analyzing, or re-running, redirect to processing stepper
      if (detailRes.status !== 'complete') {
        navigate(`/calls/${id}/processing`);
        return;
      }

      try {
        const [analysisRes, transcriptRes, reportRes] = await Promise.all([
          apiRequest<any>(`/calls/${id}/analysis`),
          apiRequest<any>(`/calls/${id}/transcript`),
          apiRequest<AudioReportData>(`/calls/${id}/report`).catch(() => null),
        ]);

        setAnalysis(analysisRes);
        setTranscript(transcriptRes);
        setReport(reportRes);
      } catch (innerErr: any) {
        // If analysis is still being calculated or re-queued (409 Conflict), gracefully redirect to processing stepper
        if (
          innerErr?.statusCode === 409 || 
          innerErr?.status === 409 || 
          innerErr?.message?.toLowerCase().includes('not ready')
        ) {
          navigate(`/calls/${id}/processing`);
          return;
        }
        throw innerErr;
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load call audit data.');
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle audio time update & active utterance synchronization
  const handleTimeUpdate = (timeMs: number) => {
    if (!transcript?.utterances) return;
    const roundedMs = Math.round(timeMs);
    const active = transcript.utterances.find(
      (u: any) => roundedMs >= u.start_ms && roundedMs <= u.end_ms
    );
    setActiveUtteranceId(active ? active.id : null);
  };

  // Smoothly scroll active utterance into view when activeUtteranceId changes
  useEffect(() => {
    if (!autoScroll || !activeUtteranceId) return;
    if (prevActiveIdRef.current === activeUtteranceId) return;
    prevActiveIdRef.current = activeUtteranceId;
    const el = document.getElementById(`utt-${activeUtteranceId}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [activeUtteranceId, autoScroll]);

  const handleSelectEvidenceOrAction = (utteranceId: string, quote?: string) => {
    setHighlightedUtteranceId(utteranceId);
    setActiveQuote(quote || null);
    const utt = transcript?.utterances?.find((u: any) => u.id === utteranceId);
    if (utt && audioPlayerRef.current) {
      audioPlayerRef.current.seekTo(utt.start_ms / 1000, true);
    }
    const element = document.getElementById(`utt-${utteranceId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  const handleSeekToUtterance = (utterance: any) => {
    setHighlightedUtteranceId(utterance.id);
    setActiveQuote(null);
    if (audioPlayerRef.current) {
      audioPlayerRef.current.seekTo(utterance.start_ms / 1000, true);
    }
  };

  const handlePlayFromTimestamp = (timeSec: number) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.seekTo(timeSec, true);
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

  const handleReanalyze = async () => {
    if (!id) return;
    if (!window.confirm('Re-run full analysis with surgical audio enhancements?')) return;
    try {
      await apiRequest(`/calls/${id}/reanalyze`, { method: 'POST' });
      navigate(`/calls/${id}/processing`);
    } catch (err: any) {
      alert(`Re-analysis failed: ${err.message}`);
    }
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
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button
            type="button"
            onClick={() => navigate(`/calls/${id}/processing`)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              backgroundColor: 'var(--color-primary)',
              color: '#FFFFFF',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Check Progress & Retry
          </button>
          <button
            type="button"
            onClick={() => navigate('/history')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              backgroundColor: 'var(--color-surface-sunken)',
              color: 'var(--color-text-secondary)',
              border: '1px solid var(--color-border)',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Return to History
          </button>
        </div>
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
            onClick={handleReanalyze}
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
            title="Re-run transcription and analysis with deep audio enhancements"
          >
            <RotateCcw size={15} color="var(--color-primary)" />
            Re-analyze
          </button>

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

      {/* Supervisory Ambiguity Banner */}
      {analysis && (analysis.verdict === 'NEEDS_REVIEW' || analysis.confidence?.level === 'low' || analysis.limited_evidence_reason) && (
        <div
          style={{
            marginBottom: '20px',
            padding: '14px 18px',
            borderRadius: '10px',
            backgroundColor: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--color-text-primary)' }}>
            <span style={{ fontSize: '18px' }}>⚠️</span>
            <div>
              <strong>Supervisory Review Recommended:</strong> {analysis.limited_evidence_reason || 'Short call snippet or ambiguous speaker attribution detected.'}
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsSwapModalOpen(true)}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              border: '1px solid rgba(234, 179, 8, 0.6)',
              backgroundColor: 'rgba(234, 179, 8, 0.25)',
              color: 'var(--color-text-primary)',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Swap Speaker Roles
          </button>
        </div>
      )}

      {/* Synchronized Audio Player */}
      <div style={{ marginBottom: '24px' }}>
        <AudioPlayer
          ref={audioPlayerRef}
          callId={id!}
          durationMs={callDetail?.duration_ms}
          onTimeUpdate={handleTimeUpdate}
          onPlayStateChange={setIsPlaying}
          autoScroll={autoScroll}
          onToggleAutoScroll={() => setAutoScroll((prev) => !prev)}
        />
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
          <AuditorFeedbackCard
            callId={id!}
            analysisId={analysis.id}
            currentVerdict={analysis.verdict || 'GREEN'}
            calibratedModel={analysis.calibrated_model}
          />
          {report && <AudioQualityReportCard report={report} />}
        </div>
      )}

      {/* Main Analysis & Transcript Grid */}
      <div
        className="results-grid"
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
                coachingRecommendations={analysis.coaching_recommendations || []}
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
              activeQuote={activeQuote}
              activeUtteranceId={activeUtteranceId}
              onChangeRolesClick={() => setIsSwapModalOpen(true)}
              onSeekToUtterance={handleSeekToUtterance}
              onPlayFromTimestamp={handlePlayFromTimestamp}
              autoScroll={autoScroll}
              onToggleAutoScroll={() => setAutoScroll((prev) => !prev)}
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
