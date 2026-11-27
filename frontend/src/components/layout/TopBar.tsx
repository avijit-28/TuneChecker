import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Search, Bell } from 'lucide-react';

interface TopBarProps {
  onToggleMobileNav?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onToggleMobileNav }) => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/history?q=${encodeURIComponent(trimmed)}`);
    } else {
      navigate('/history');
    }
  };

  return (
    <header
      className="topbar-container"
      style={{
        height: '62px',
        backgroundColor: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 10,
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '0 0 auto' }}>
        <button
          type="button"
          onClick={onToggleMobileNav}
          className="mobile-nav-toggle"
          aria-label="Toggle navigation menu"
          style={{
            background: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            padding: '7px',
            color: 'var(--color-text-primary)',
            cursor: 'pointer',
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Global Search Bar */}
      <form
        onSubmit={handleSearchSubmit}
        className="topbar-search-form"
        style={{
          flex: '1 1 0%',
          minWidth: 0,
          maxWidth: '460px',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <Search
          size={15}
          style={{
            position: 'absolute',
            left: '14px',
            color: 'var(--color-text-tertiary)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search calls, reports, or representatives..."
          aria-label="Search calls"
          style={{
            width: '100%',
            padding: '8px 14px 8px 38px',
            borderRadius: '999px',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface-sunken)',
            color: 'var(--color-text-primary)',
            fontSize: '13px',
            outline: 'none',
          }}
        />
      </form>

      {/* Right Profile & Notifications */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: '0 0 auto' }}>
        <button
          type="button"
          onClick={() => navigate('/history')}
          aria-label="Recent notifications"
          style={{
            background: 'var(--color-surface-sunken)',
            border: '1px solid var(--color-border)',
            borderRadius: '999px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-text-secondary)',
            cursor: 'pointer',
          }}
        >
          <Bell size={16} />
        </button>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '9px',
            padding: '4px 10px 4px 4px',
            borderRadius: '999px',
            border: '1px solid var(--color-border)',
            backgroundColor: 'var(--color-surface)',
          }}
        >
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '999px',
              background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            A
          </div>
          <div className="topbar-user-meta" style={{ lineHeight: 1.15 }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Avijit Pakhira
            </div>
            <div style={{ fontSize: '10px', color: 'var(--color-text-tertiary)' }}>
              Auditor
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
