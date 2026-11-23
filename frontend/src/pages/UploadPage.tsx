import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DropZone } from '../components/upload/DropZone';
import { FileCard } from '../components/upload/FileCard';
import { apiRequest } from '../api/client';
import { Sliders, ShieldCheck } from 'lucide-react';

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [settingsInfo, setSettingsInfo] = useState<{ version: number; sensitivity: string; criteriaCount: number } | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    apiRequest<{ version: number; sensitivity: string; config: any }>('/settings')
      .then((data) => {
        const enabled = data.config?.tone?.criteria?.filter((c: any) => c.enabled)?.length || 3;
        setSettingsInfo({
          version: data.version,
          sensitivity: data.sensitivity,
          criteriaCount: enabled,
        });
      })
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/calls', {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });

      if (!response.ok) {
        let errData;
        try {
          errData = await response.json();
        } catch {
          errData = { error: { message: response.statusText } };
        }
        throw new Error(errData?.error?.message || 'Upload failed');
      }

      const data = await response.json();
      navigate(`/calls/${data.id}/processing`);
    } catch (err: any) {
      setUploadError(err.message || 'An error occurred during upload.');
      setIsUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, margin: '0 0 8px 0', color: 'var(--color-text-primary)' }}>
          Upload Sales Call Recording
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
          Upload an .m4a audio recording of a customer sales conversation to audit the sales representative's tone
          and track follow-up commitments.
        </p>
      </div>

      {settingsInfo && (
        <div
          style={{
            marginBottom: '20px',
            padding: '12px 16px',
            backgroundColor: 'var(--color-surface)',
            borderRadius: '10px',
            border: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
            <Sliders size={16} color="var(--color-primary)" />
            <span>
              Auditing with Profile <strong>v{settingsInfo.version}</strong> ({settingsInfo.criteriaCount} criteria enabled)
            </span>
          </div>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '12px',
              backgroundColor: 'var(--color-primary-subtle)',
              color: 'var(--color-primary)',
              fontWeight: 600,
              fontSize: '11px',
              textTransform: 'capitalize',
            }}
          >
            {settingsInfo.sensitivity} Sensitivity
          </span>
        </div>
      )}

      <DropZone onFileSelect={setFile} disabled={isUploading} />

      {file && (
        <FileCard
          file={file}
          onRemove={() => setFile(null)}
          onUpload={handleUpload}
          isUploading={isUploading}
        />
      )}

      {uploadError && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px 16px',
            borderRadius: '8px',
            backgroundColor: 'var(--error-bg)',
            color: 'var(--error-fg)',
            border: '1px solid var(--error-border)',
            fontSize: '13px',
          }}
        >
          {uploadError}
        </div>
      )}

      <div
        style={{
          marginTop: '32px',
          padding: '16px',
          borderRadius: '12px',
          backgroundColor: 'var(--color-surface-sunken)',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start',
        }}
      >
        <ShieldCheck size={20} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', lineHeight: 1.5 }}>
          <strong>Zero-Cost & Local Privacy Guarantee:</strong> Audio processing is executed 100% locally on your machine
          using Faster-Whisper and local Ollama models. No audio or transcript data is transmitted to external cloud providers.
        </div>
      </div>
    </div>
  );
};
