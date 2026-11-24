import React, { useState, useRef, useEffect } from 'react';
import { UploadCloud, AlertCircle, Mic, Square, Trash2, CheckCircle2 } from 'lucide-react';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export const DropZone: React.FC<DropZoneProps> = ({ onFileSelect, disabled }) => {
  const [activeTab, setActiveTab] = useState<'upload' | 'record'>('upload');
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Live recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (recordedUrl) URL.revokeObjectURL(recordedUrl);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, [recordedUrl]);

  const validateAndSelect = (file: File) => {
    setError(null);
    const validExts = ['.m4a', '.mp4', '.mp3', '.wav', '.mpeg', '.mpg', '.mpga', '.webm'];
    const lowerName = file.name.toLowerCase();
    if (!validExts.some((ext) => lowerName.endsWith(ext))) {
      setError('Only .m4a, .mp4, .mp3, .wav, .webm, and .mpeg/.mpg audio recordings are accepted.');
      return;
    }
    const maxMb = 50;
    if (file.size > maxMb * 1024 * 1024) {
      setError(`File size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds the 50 MB limit.`);
      return;
    }
    if (file.size === 0) {
      setError('File is empty (0 bytes).');
      return;
    }
    onFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      if (e.dataTransfer.files.length > 1) {
        setError('Please upload one recording at a time.');
        return;
      }
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  // Start live microphone recording
  const startRecording = async () => {
    setError(null);
    setRecordedBlob(null);
    if (recordedUrl) URL.revokeObjectURL(recordedUrl);
    setRecordedUrl(null);
    setRecordDuration(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: mimeType });
        setRecordedBlob(blob);
        const url = URL.createObjectURL(blob);
        setRecordedUrl(url);

        // Turn blob into a File object for the pipeline
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const recordedFile = new File([blob], `mic_recording_${timestamp}.webm`, { type: mimeType });
        validateAndSelect(recordedFile);

        // Stop all audio tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start(250); // Slice chunks every 250ms
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordDuration((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setError(err?.message || 'Could not access microphone. Please grant browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRecording(false);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div>
      {/* Mode Toggle: File Upload vs Live Mic */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button
          type="button"
          onClick={() => { setActiveTab('upload'); setError(null); }}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 16px',
            borderRadius: '10px',
            border: activeTab === 'upload' ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
            backgroundColor: activeTab === 'upload' ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
            color: activeTab === 'upload' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <UploadCloud size={16} />
          Upload Audio/Video File
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('record'); setError(null); }}
          style={{
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '10px 16px',
            borderRadius: '10px',
            border: activeTab === 'record' ? '2px solid var(--color-primary)' : '1px solid var(--color-border)',
            backgroundColor: activeTab === 'record' ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
            color: activeTab === 'record' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <Mic size={16} />
          Record Live Microphone
        </button>
      </div>

      {activeTab === 'upload' ? (
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="Upload call recording: drop .m4a, .mp4, .mp3, .wav, or .mpeg file or press Enter to browse"
          onClick={() => !disabled && inputRef.current?.click()}
          onKeyDown={(e) => {
            if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${
              error
                ? 'var(--error-border)'
                : isDragOver
                ? 'var(--color-primary)'
                : 'var(--color-border-strong)'
            }`,
            borderRadius: '16px',
            padding: '48px 24px',
            textAlign: 'center',
            backgroundColor: isDragOver
              ? 'var(--color-primary-subtle)'
              : 'var(--color-surface)',
            cursor: disabled ? 'not-allowed' : 'pointer',
            transition: 'all 0.15s ease',
            outline: 'none',
          }}
        >
          <input
            type="file"
            ref={inputRef}
            accept=".m4a,.mp4,.mp3,.wav,.mpeg,.mpg,.mpga,.webm,audio/mp4,video/mp4,audio/mpeg,audio/wav,video/mpeg,audio/x-m4a,audio/webm,video/webm"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                validateAndSelect(e.target.files[0]);
              }
            }}
            disabled={disabled}
          />

          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              backgroundColor: isDragOver
                ? 'var(--color-primary)'
                : 'var(--color-surface-sunken)',
              color: isDragOver ? '#FFFFFF' : 'var(--color-primary)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
            }}
          >
            <UploadCloud size={24} />
          </div>

          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Drop your call recording here (.mp4, .m4a, .mp3, .wav, .webm), or{' '}
            <span style={{ color: 'var(--color-primary)', textDecoration: 'underline' }}>browse</span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--color-text-tertiary)', marginTop: '6px' }}>
            .mp4, .m4a, .mp3, .wav, .mpeg, .webm • 10 seconds to 30 minutes • Up to 50 MB
          </div>
        </div>
      ) : (
        /* Live Microphone Recording Pane */
        <div
          style={{
            border: '2px dashed var(--color-border-strong)',
            borderRadius: '16px',
            padding: '36px 24px',
            textAlign: 'center',
            backgroundColor: 'var(--color-surface)',
          }}
        >
          {!isRecording && !recordedBlob && (
            <div>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '28px',
                  backgroundColor: 'var(--color-primary-subtle)',
                  color: 'var(--color-primary)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '16px',
                }}
              >
                <Mic size={28} />
              </div>
              <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                Record a Live Sales Pitch or Practice Call
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
                Speak clearly into your microphone. TuneChecker will transcribe and evaluate your sales tone.
              </div>
              <button
                type="button"
                onClick={startRecording}
                disabled={disabled}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  borderRadius: '10px',
                  backgroundColor: 'var(--color-primary)',
                  color: '#FFFFFF',
                  border: 'none',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                }}
              >
                <Mic size={18} />
                Start Recording
              </button>
            </div>
          )}

          {isRecording && (
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 18px',
                  borderRadius: '20px',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  color: '#ef4444',
                  fontWeight: 700,
                  fontSize: '16px',
                  marginBottom: '18px',
                }}
              >
                <span
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '6px',
                    backgroundColor: '#ef4444',
                    animation: 'pulse 1s infinite alternate',
                  }}
                />
                Recording: {formatTime(recordDuration)}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
                Microphone is active. Speak your sales pitch, customer responses, or roleplay call.
              </div>
              <button
                type="button"
                onClick={stopRecording}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  borderRadius: '10px',
                  backgroundColor: '#ef4444',
                  color: '#FFFFFF',
                  border: 'none',
                  fontWeight: 600,
                  fontSize: '14px',
                  cursor: 'pointer',
                  boxShadow: '0 2px 8px rgba(239,68,68,0.3)',
                }}
              >
                <Square size={16} fill="#FFFFFF" />
                Stop & Review
              </button>
            </div>
          )}

          {!isRecording && recordedBlob && (
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '6px 14px',
                  borderRadius: '16px',
                  backgroundColor: 'var(--success-bg)',
                  color: 'var(--success-fg)',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: '16px',
                }}
              >
                <CheckCircle2 size={16} />
                Recording Captured ({formatTime(recordDuration)})
              </div>

              {recordedUrl && (
                <div style={{ marginBottom: '20px' }}>
                  <audio controls src={recordedUrl} style={{ width: '100%', maxWidth: '400px' }} />
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={startRecording}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface-sunken)',
                    color: 'var(--color-text-secondary)',
                    fontWeight: 600,
                    fontSize: '13px',
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={15} />
                  Re-record
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: '12px',
            padding: '10px 14px',
            borderRadius: '8px',
            backgroundColor: 'var(--error-bg)',
            color: 'var(--error-fg)',
            border: '1px solid var(--error-border)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
            fontWeight: 500,
          }}
          role="alert"
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
