import React from 'react';
import { FileAudio, X, ArrowRight } from 'lucide-react';

interface FileCardProps {
  file: File;
  onRemove: () => void;
  onUpload: () => void;
  isUploading: boolean;
}

export const FileCard: React.FC<FileCardProps> = ({
  file,
  onRemove,
  onUpload,
  isUploading,
}) => {
  const sizeMb = (file.size / (1024 * 1024)).toFixed(2);

  return (
    <div
      style={{
        marginTop: '20px',
        padding: '16px 20px',
        backgroundColor: 'var(--color-surface)',
        borderRadius: '12px',
        border: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0 }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            backgroundColor: 'var(--color-primary-subtle)',
            color: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <FileAudio size={22} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={file.name}
          >
            {file.name}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
            {sizeMb} MB • Ready for audit
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <button
          type="button"
          onClick={onRemove}
          disabled={isUploading}
          style={{
            background: 'none',
            border: 'none',
            padding: '8px',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            color: 'var(--color-text-tertiary)',
            borderRadius: '6px',
          }}
          title="Remove file"
        >
          <X size={18} />
        </button>

        <button
          type="button"
          onClick={onUpload}
          disabled={isUploading}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: isUploading ? 'var(--color-text-disabled)' : 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '14px',
            cursor: isUploading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.15s ease',
          }}
        >
          <span>{isUploading ? 'Uploading...' : 'Start Audit'}</span>
          {!isUploading && <ArrowRight size={16} />}
        </button>
      </div>
    </div>
  );
};
