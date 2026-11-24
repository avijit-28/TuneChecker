import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import { ShieldCheck, ShieldAlert, Cpu, Menu } from 'lucide-react';

interface TopBarProps {
  onToggleMobileNav?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleMobileNav }) => {
  const [health, setHealth] = useState<{ status: string; checks: Record<string, string> } | null>(null);

  useEffect(() => {
    apiRequest<{ status: string; checks: Record<string, string> }>('/health')
      .then(setHealth)
      .catch(() => setHealth({ status: 'unavailable', checks: { system: 'offline' } }));
  }, []);

  const isHealthy = health?.status === 'ok';

  return (
    <header
      className="topbar-container"
      style={{
        height: '60px',
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 10
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          type="button"
          onClick={onToggleMobileNav}
          className="mobile-nav-toggle"
          aria-label="Toggle navigation menu"
          style={{
            background: 'none',
            border: '1px solid var(--color-border)',
            borderRadius: '6px',
            padding: '6px',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Menu size={20} />
        </button>

        <span className="system-engine-label" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          System Engine:
        </span>
        <span 
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            padding: '4px 10px',
            borderRadius: '12px',
            backgroundColor: 'var(--color-surface-sunken)',
            color: 'var(--color-text-secondary)',
            fontWeight: 500
          }}
        >
          <Cpu size={14} /> CPU / 16GB
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div 
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 500,
            padding: '4px 10px',
            borderRadius: '12px',
            backgroundColor: isHealthy ? 'var(--success-bg)' : 'var(--error-bg)',
            color: isHealthy ? 'var(--success-fg)' : 'var(--error-fg)',
            border: `1px solid ${isHealthy ? 'var(--success-border)' : 'var(--error-border)'}`
          }}
          title={health ? JSON.stringify(health.checks) : 'Checking readiness...'}
        >
          {isHealthy ? <ShieldCheck size={14} /> : <ShieldAlert size={14} />}
          <span>{isHealthy ? 'Pipeline Ready' : 'Service Check Required'}</span>
        </div>
      </div>
    </header>
  );
};
