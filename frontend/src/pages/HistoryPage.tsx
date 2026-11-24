import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api/client';
import { Search, AlertOctagon, CheckCircle2, ArrowRight } from 'lucide-react';

interface CallListItemData {
  id: string;
  name: string;
  status: string;
  status_group: string;
  tone: 'RED' | 'GREEN' | null;
  duration_ms: number | null;
  size_bytes: number;
  is_synthetic: boolean;
  created_at: string;
}

export const HistoryPage: React.FC = () => {
  const [calls, setCalls] = useState<CallListItemData[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [toneFilter, setToneFilter] = useState<'all' | 'red' | 'green' | 'none'>('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchCalls = async () => {
    try {
      let url = `/calls?page=${page}&page_size=20`;
      if (search.trim()) url += `&q=${encodeURIComponent(search.trim())}`;
      if (toneFilter !== 'all') url += `&tone=${toneFilter}`;

      const res = await apiRequest<{ items: CallListItemData[]; total: number }>(url);
      setCalls(res.items);
      setTotal(res.total);
    } catch {
      // Keep existing calls on transient poll error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();

    // Auto-poll if any call is in progress
    const timer = setInterval(() => {
      fetchCalls();
    }, 5000);

    return () => clearInterval(timer);
  }, [page, toneFilter, search]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 6px 0', color: 'var(--color-text-primary)' }}>
            Call Audit History ({total})
          </h1>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary)' }}>
            Search, filter, and inspect previously audited sales call recordings.
          </p>
        </div>

        <Link
          to="/upload"
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            fontWeight: 600,
            fontSize: '13px',
            textDecoration: 'none',
          }}
        >
          Upload New Call
        </Link>
      </div>

      {/* Filters & Search Bar */}
      <div
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          padding: '14px 18px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '16px',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {(['all', 'red', 'green', 'none'] as const).map((filter) => {
            const isSelected = toneFilter === filter;
            const labels: Record<string, string> = {
              all: 'All Calls',
              red: 'RED Verdicts',
              green: 'GREEN Verdicts',
              none: 'Not Analyzed',
            };
            return (
              <button
                key={filter}
                type="button"
                onClick={() => {
                  setToneFilter(filter);
                  setPage(1);
                }}
                style={{
                  padding: '6px 12px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: isSelected ? 700 : 500,
                  border: isSelected
                    ? '1px solid var(--color-primary)'
                    : '1px solid var(--color-border)',
                  backgroundColor: isSelected
                    ? 'var(--color-primary-subtle)'
                    : 'var(--color-surface)',
                  color: isSelected ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {labels[filter]}
              </button>
            );
          })}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--color-surface-sunken)',
            padding: '6px 12px',
            borderRadius: '8px',
            border: '1px solid var(--color-border)',
            width: '240px',
          }}
        >
          <Search size={14} color="var(--color-text-tertiary)" />
          <input
            type="text"
            placeholder="Search by call name..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '13px',
              color: 'var(--color-text-primary)',
              outline: 'none',
              width: '100%',
            }}
          />
        </div>
      </div>

      {/* Table */}
      <div
        className="responsive-table-container"
        style={{
          backgroundColor: 'var(--color-surface)',
          borderRadius: '12px',
          border: '1px solid var(--color-border)',
          overflowX: 'auto',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr
              style={{
                backgroundColor: 'var(--color-surface-sunken)',
                borderBottom: '1px solid var(--color-border)',
                color: 'var(--color-text-tertiary)',
                fontWeight: 600,
              }}
            >
              <th style={{ padding: '12px 20px' }}>Call Name</th>
              <th style={{ padding: '12px 16px' }}>Tone Verdict</th>
              <th style={{ padding: '12px 16px' }}>Duration</th>
              <th style={{ padding: '12px 16px' }}>Uploaded At</th>
              <th style={{ padding: '12px 16px' }}>Status</th>
              <th style={{ padding: '12px 20px', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {calls.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-tertiary)' }}>
                  {loading ? 'Loading calls...' : 'No calls match the current search and filters.'}
                </td>
              </tr>
            ) : (
              calls.map((c) => {
                const durationSec = c.duration_ms ? `${(c.duration_ms / 1000).toFixed(0)}s` : '—';
                const uploadDate = new Date(c.created_at).toLocaleDateString(undefined, {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                });

                const isRed = c.tone === 'RED';
                const isGreen = c.tone === 'GREEN';

                const targetLink =
                  c.status_group === 'in_progress' ? `/calls/${c.id}/processing` : `/calls/${c.id}`;

                return (
                  <tr
                    key={c.id}
                    style={{
                      borderBottom: '1px solid var(--color-divider)',
                      transition: 'background-color 0.1s ease',
                    }}
                  >
                    <td style={{ padding: '14px 20px', fontWeight: 600 }}>
                      <Link
                        to={targetLink}
                        style={{ color: 'var(--color-text-primary)', textDecoration: 'none' }}
                      >
                        {c.name}
                      </Link>
                    </td>

                    <td style={{ padding: '14px 16px' }}>
                      {isRed ? (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '3px 10px',
                            borderRadius: '12px',
                            backgroundColor: 'var(--tone-red-bg)',
                            color: 'var(--tone-red-fg)',
                            border: '1px solid var(--tone-red-border)',
                            fontWeight: 700,
                            fontSize: '11px',
                          }}
                        >
                          <AlertOctagon size={13} /> RED
                        </span>
                      ) : isGreen ? (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '5px',
                            padding: '3px 10px',
                            borderRadius: '12px',
                            backgroundColor: 'var(--tone-green-bg)',
                            color: 'var(--tone-green-fg)',
                            border: '1px solid var(--tone-green-border)',
                            fontWeight: 700,
                            fontSize: '11px',
                          }}
                        >
                          <CheckCircle2 size={13} /> GREEN
                        </span>
                      ) : (
                        <span
                          style={{
                            padding: '3px 10px',
                            borderRadius: '12px',
                            backgroundColor: 'var(--color-surface-sunken)',
                            color: 'var(--color-text-tertiary)',
                            fontSize: '11px',
                            fontWeight: 600,
                          }}
                        >
                          Not analyzed
                        </span>
                      )}
                    </td>

                    <td style={{ padding: '14px 16px', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                      {durationSec}
                    </td>

                    <td style={{ padding: '14px 16px', color: 'var(--color-text-tertiary)' }}>
                      {uploadDate}
                    </td>

                    <td style={{ padding: '14px 16px' }}>
                      <span
                        style={{
                          fontSize: '12px',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          color:
                            c.status === 'complete'
                              ? 'var(--success-fg)'
                              : c.status === 'failed'
                              ? 'var(--error-fg)'
                              : 'var(--color-primary)',
                        }}
                      >
                        {c.status.replace('_', ' ')}
                      </span>
                    </td>

                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <Link
                        to={targetLink}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          color: 'var(--color-primary)',
                          fontWeight: 600,
                          fontSize: '12px',
                          textDecoration: 'none',
                        }}
                      >
                        <span>View</span>
                        <ArrowRight size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
