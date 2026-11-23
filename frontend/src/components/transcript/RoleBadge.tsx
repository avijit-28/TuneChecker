import React from 'react';
import { UserCheck, User, HelpCircle } from 'lucide-react';

interface RoleBadgeProps {
  role: 'sales_rep' | 'customer' | 'unknown' | string;
  source?: 'auto' | 'user';
  status?: string;
  level?: string | null;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role, source, level }) => {
  const isRep = role === 'sales_rep';
  const isCustomer = role === 'customer';

  const label = isRep ? 'Sales Rep' : isCustomer ? 'Customer' : 'Unknown Role';
  const bgColor = isRep ? 'var(--speaker-rep-bg)' : 'var(--speaker-customer-bg)';
  const fgColor = isRep ? 'var(--color-primary)' : 'var(--color-text-secondary)';
  const borderColor = isRep ? 'var(--color-primary-border)' : 'var(--color-border)';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: '12px',
        backgroundColor: bgColor,
        color: fgColor,
        border: `1px solid ${borderColor}`,
        fontSize: '11px',
        fontWeight: 600,
        letterSpacing: '0.02em',
      }}
      title={level ? `Attribution confidence: ${level} (${source})` : ''}
    >
      {isRep ? <UserCheck size={12} /> : isCustomer ? <User size={12} /> : <HelpCircle size={12} />}
      {label}
      {source === 'user' && <span style={{ fontSize: '9px', opacity: 0.8 }}>(User)</span>}
    </span>
  );
};
