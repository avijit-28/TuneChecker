import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle } from 'lucide-react';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export const DropZone: React.FC<DropZoneProps> = ({ onFileSelect, disabled }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = (file: File) => {
    setError(null);
    if (!file.name.toLowerCase().endsWith('.m4a')) {
      setError('Only .m4a audio recordings are accepted.');
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

  return (
    <div>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Upload call recording: drop .m4a file or press Enter to browse"
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
          accept=".m4a,audio/mp4,audio/x-m4a"
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
          Drop your .m4a call recording here, or{' '}
          <span style={{ color: 'var(--color-primary)', textDecoration: 'underline' }}>browse</span>
        </div>
        <div style={{ fontSize: '13px', color: 'var(--color-text-tertiary)', marginTop: '6px' }}>
          AAC encoded .m4a audio • 10 seconds to 30 minutes • Up to 50 MB
        </div>
      </div>

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
