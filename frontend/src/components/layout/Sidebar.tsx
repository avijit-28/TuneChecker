import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  UploadCloud, 
  History, 
  Settings as SettingsIcon,
  PhoneCall
} from 'lucide-react';

interface SidebarProps {
  collapsed?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Call', icon: UploadCloud },
    { to: '/history', label: 'Call History', icon: History },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside 
      style={{
        width: '240px',
        backgroundColor: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0
      }}
      aria-label="Main Navigation"
    >
      <div 
        style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--color-divider)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}
      >
        <div 
          style={{
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            borderRadius: '8px',
            width: '36px',
            height: '36px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <PhoneCall size={20} />
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '16px', color: 'var(--color-text-primary)', lineHeight: 1.2 }}>
            TuneChecker
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', letterSpacing: '0.04em' }}>
            SALES CALL AUDITOR
          </div>
        </div>
      </div>

      <nav style={{ padding: '16px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                backgroundColor: isActive ? 'var(--color-primary-subtle)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s ease'
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div 
        style={{ 
          padding: '16px 20px', 
          borderTop: '1px solid var(--color-divider)',
          fontSize: '12px',
          color: 'var(--color-text-tertiary)'
        }}
      >
        <div>Local Zero-Cost Mode</div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-disabled)' }}>Faster-Whisper • Ollama</div>
      </div>
    </aside>
  );
};
