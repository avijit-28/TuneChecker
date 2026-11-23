import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertOctagon, 
  Clock, 
  ArrowRight,
  User,
  Calendar
} from 'lucide-react';

interface DashboardData {
  generated_at: string;
  kpis: {
    total_calls: number;
    total_analyzed: number;
    red: number;
    green: number;
    awaiting_analysis: number;
    needs_attention: number;
  };
  tone_distribution: {
    red: number;
    green: number;
    not_analyzed: number;
  };
  recent_calls: any[];
  recent_action_items: any[];
}

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchSummary = async () => {
    try {
      const res = await apiRequest<DashboardData>('/dashboard/summary');
      setData(res);
    } catch {
      // Keep existing data on transient error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const kpis = data?.kpis || {
    total_calls: 0,
    total_analyzed: 0,
    red: 0,
    green: 0,
    awaiting_analysis: 0,
    needs_attention: 0,
  };

  if (loading && !data) {
    return (
      <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '15px' }}>
        Loading sales call analytics...
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--color-text-primary)' }}>
            Sales Call Quality Dashboard
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Real-time sales representative tone evaluations and verified follow-up commitments.
          </p>
        </div>

        <Link
          to="/upload"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            padding: '10px 18px',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '14px',
            textDecoration: 'none',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <UploadCloud size={18} />
          Upload New Call
        </Link>
      </div>

      {/* KPI Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '20px',
          marginBottom: '32px',
        }}
      >
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid var(--color-border)',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>
            Total Calls Audited
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '8px' }}>
            {kpis.total_calls}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Across all active recordings
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid var(--tone-green-border)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 700,
              color: 'var(--tone-green-fg)',
              textTransform: 'uppercase',
            }}
          >
            <CheckCircle2 size={16} /> GREEN Verdicts
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--tone-green-fg)', marginTop: '8px' }}>
            {kpis.green}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            No negative rep behavior detected
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid var(--tone-red-border)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 700,
              color: 'var(--tone-red-fg)',
              textTransform: 'uppercase',
            }}
          >
            <AlertOctagon size={16} /> RED Verdicts
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--tone-red-fg)', marginTop: '8px' }}>
            {kpis.red}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Unprofessional rep tone flagged
          </div>
        </div>

        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid var(--color-border)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              fontWeight: 600,
              color: 'var(--color-text-tertiary)',
              textTransform: 'uppercase',
            }}
          >
            <Clock size={16} /> Tracked Actions
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'var(--color-text-primary)', marginTop: '8px' }}>
            {data?.recent_action_items?.length || 0}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-text-tertiary)', marginTop: '4px' }}>
            Recent follow-ups identified
          </div>
        </div>
      </div>

      {/* Grid: Recent Calls & Recent Action Items */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Recent Calls */}
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--color-border)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--color-divider)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Recent Audited Calls
            </h3>
            <Link
              to="/history"
              style={{
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                textDecoration: 'none',
              }}
            >
              View all <ArrowRight size={14} />
            </Link>
          </div>

          <div style={{ padding: '8px 0' }}>
            {(!data?.recent_calls || data.recent_calls.length === 0) ? (
              <div style={{ padding: '32px', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '13px' }}>
                No calls uploaded yet. Upload a recording to begin.
              </div>
            ) : (
              data.recent_calls.map((c) => {
                const isRed = c.tone === 'RED';
                const isGreen = c.tone === 'GREEN';
                return (
                  <Link
                    key={c.id}
                    to={`/calls/${c.id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 20px',
                      borderBottom: '1px solid var(--color-divider)',
                      textDecoration: 'none',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <div>
                      <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {c.name}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', marginTop: '2px' }}>
                        {c.duration_ms ? `${(c.duration_ms / 1000).toFixed(0)}s` : '—'} • {new Date(c.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div>
                      {isRed ? (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '10px',
                            backgroundColor: 'var(--tone-red-bg)',
                            color: 'var(--tone-red-fg)',
                            border: '1px solid var(--tone-red-border)',
                            fontWeight: 700,
                            fontSize: '11px',
                          }}
                        >
                          RED
                        </span>
                      ) : isGreen ? (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '10px',
                            backgroundColor: 'var(--tone-green-bg)',
                            color: 'var(--tone-green-fg)',
                            border: '1px solid var(--tone-green-border)',
                            fontWeight: 700,
                            fontSize: '11px',
                          }}
                        >
                          GREEN
                        </span>
                      ) : (
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '10px',
                            backgroundColor: 'var(--color-surface-sunken)',
                            color: 'var(--color-text-tertiary)',
                            fontSize: '11px',
                          }}
                        >
                          {c.status}
                        </span>
                      )}
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </div>

        {/* Recent Action Items */}
        <div
          style={{
            backgroundColor: 'var(--color-surface)',
            borderRadius: '12px',
            border: '1px solid var(--color-border)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              padding: '16px 20px',
              borderBottom: '1px solid var(--color-divider)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text-primary)' }}>
              Recent Tracked Commitments
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>
              Across All Calls
            </span>
          </div>

          <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(!data?.recent_action_items || data.recent_action_items.length === 0) ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '13px' }}>
                No action items tracked yet.
              </div>
            ) : (
              data.recent_action_items.map((act) => (
                <div
                  key={act.id}
                  style={{
                    padding: '12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--color-surface-sunken)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: '6px' }}>
                    {act.task}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '14px', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <User size={12} color="var(--color-text-tertiary)" /> {act.owner_text || 'Not specified'}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                      <Calendar size={12} color="var(--color-text-tertiary)" /> {act.deadline_text || 'Not specified'}
                    </span>
                    <Link
                      to={`/calls/${act.call_id}`}
                      style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 600 }}
                    >
                      {act.call_name}
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
