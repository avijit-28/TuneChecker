import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppShell: React.FC = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div 
      style={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg)',
        color: 'var(--color-text-primary)',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
      }}
    >
      {mobileNavOpen && (
        <div 
          className="sidebar-backdrop"
          onClick={() => setMobileNavOpen(false)}
        />
      )}

      <Sidebar 
        mobileOpen={mobileNavOpen} 
        onClose={() => setMobileNavOpen(false)} 
      />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <TopBar onToggleMobileNav={() => setMobileNavOpen(!mobileNavOpen)} />
        <main 
          className="app-shell-main"
          style={{
            flex: 1,
            padding: '32px',
            maxWidth: '1280px',
            width: '100%',
            margin: '0 auto',
            boxSizing: 'border-box'
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};
