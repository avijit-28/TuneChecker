import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  History,
  Settings as SettingsIcon,
  AudioWaveform,
  Headphones,
  X,
} from 'lucide-react';

interface SidebarProps {
  collapsed?: boolean;
  mobileOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onClose }) => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/upload', label: 'Upload Call', icon: UploadCloud },
    { to: '/history', label: 'Call History', icon: History },
    { to: '/settings', label: 'Settings', icon: SettingsIcon },
  ];

  return (
    <aside
      className={`sidebar-desktop ${mobileOpen ? 'mobile-open' : ''}`}
      style={{
        width: '248px',
        background: 'linear-gradient(180deg, #14112B 0%, #1C183D 100%)',
        borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        overflowY: 'auto',
        flexShrink: 0,
      }}
      aria-label="Main Navigation"
    >
      {/* Brand Header */}
      <div
        style={{
          padding: '20px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
              color: '#ffffff',
              borderRadius: '10px',
              width: '38px',
              height: '38px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(99, 102, 241, 0.45)',
              flexShrink: 0,
            }}
          >
            <AudioWaveform size={20} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px', color: '#ffffff', lineHeight: 1.2 }}>
              TuneChecker
            </div>
            <div style={{ fontSize: '10px', color: '#9F9AC8', letterSpacing: '0.06em', marginTop: '2px' }}>
              SALES CALL AUDITOR
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => onClose?.()}
          className="mobile-nav-close"
          aria-label="Close navigation menu"
          style={{
            background: 'rgba(255, 255, 255, 0.08)',
            border: 'none',
            borderRadius: '8px',
            padding: '6px',
            color: '#E2E0F5',
            cursor: 'pointer',
            display: 'none',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Navigation Links */}
      <nav style={{ padding: '18px 14px', flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={() => onClose?.()}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '11px 14px',
                borderRadius: '10px',
                fontSize: '14px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : '#B2AED4',
                background: isActive
                  ? 'linear-gradient(90deg, #5B5CE6 0%, #8B5CF6 100%)'
                  : 'transparent',
                boxShadow: isActive ? '0 6px 18px rgba(99, 102, 241, 0.35)' : 'none',
                textDecoration: 'none',
                transition: 'all 0.18s ease',
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom AI Call Audit Promo Card */}
      <div style={{ padding: '16px 14px' }}>
        <div
          style={{
            borderRadius: '14px',
            padding: '16px 14px',
            background: 'linear-gradient(145deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.16) 100%)',
            border: '1px solid rgba(167, 139, 250, 0.28)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: '40px',
              height: '40px',
              margin: '0 auto 10px auto',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #6366F1 0%, #A855F7 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              boxShadow: '0 4px 16px rgba(139, 92, 246, 0.45)',
            }}
          >
            <Headphones size={20} />
          </div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#ffffff' }}>
            AI Call Audit
          </div>
          <div style={{ fontSize: '11px', color: '#C4C0E8', marginTop: '4px', lineHeight: 1.4 }}>
            Transcribe • Analyze • Audit with Voice AI
          </div>
        </div>
      </div>
    </aside>
  );
};
