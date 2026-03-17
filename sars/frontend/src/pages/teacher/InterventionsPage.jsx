// frontend/src/pages/teacher/InterventionsPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const TYPE_COLORS = {
  'Counseling':        { bg: '#e8f4fd', color: '#2980b9' },
  'Tutoring':          { bg: '#e8fdf4', color: '#27ae60' },
  'Parent Meeting':    { bg: '#fef9e7', color: '#d69e2e' },
  'Written Warning':   { bg: '#fef0e7', color: '#dd6b20' },
  'Academic Probation':{ bg: '#fde8e8', color: '#c0392b' },
  'Other':             { bg: '#f0f0f0', color: '#666' },
};

export default function InterventionsPage() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');
  const [filter, setFilter]   = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    const url = filter === 'all'
      ? '/teacher/interventions'
      : `/teacher/interventions?status=${filter}`;
    setLoading(true);
    setError('');
    api.get(url)
      .then(r => setData(r.data))
      .catch(() => setError('Could not load interventions. Please try again.'))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <div style={{ maxWidth: 900 }}>
      <h2 style={{ color: '#f1f5f9', margin: '0 0 4px' }}>
        🔔 Interventions
      </h2>
      <p style={{ color: '#64748b', fontSize: 13, marginBottom: 20 }}>
        All logged interventions across every student.
        Click a student name to view their full profile.
      </p>

      {/* Summary tiles */}
      {data && (
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Total',    value: data.total,    bg: '#1e293b', color: '#f1f5f9' },
            { label: 'Open',     value: data.open,     bg: '#f0fff4', color: '#27ae60' },
            { label: 'Resolved', value: data.resolved, bg: '#0f172a', color: '#64748b'  },
          ].map(c => (
            <div key={c.label} style={{
              background: c.bg, border: '1px solid #334155',
              borderRadius: 10, padding: '14px 22px',
              textAlign: 'center', minWidth: 100,
            }}>
              <div style={{ fontSize: 26, fontWeight: 900, color: c.color }}>{c.value}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['all', 'open', 'resolved'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '7px 16px', borderRadius: 7,
              border: 'none', fontSize: 13, fontWeight: 600,
              cursor: 'pointer', textTransform: 'capitalize',
              background: filter === f ? '#1e3a5f' : '#334155',
              color: filter === f ? '#fff' : '#94a3b8',
            }}>
            {f}
          </button>
        ))}
      </div>

      {loading && <p style={{ color: '#64748b' }}>Loading...</p>}

      {!loading && error && (
        <div style={{
          background: 'rgba(248,113,113,0.08)', border: '1px solid #f87171',
          borderRadius: 8, padding: '12px 16px', color: '#f87171', fontSize: 13,
        }}>
          {error}
        </div>
      )}

      {!loading && data?.interventions?.length === 0 && (
        <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
          No interventions found.
        </div>
      )}

      {!loading && data?.interventions?.map(item => {
        const tc = TYPE_COLORS[item.intervention_type] || TYPE_COLORS['Other'];
        return (
          <div key={item.id} style={{
            background: '#1e293b', border: '1px solid #334155',
            borderRadius: 12, padding: 16, marginBottom: 10,
          }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'flex-start', marginBottom: 8,
            }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                <button
                  onClick={() => navigate(`/teacher/students/${item.student_id}`)}
                  style={{
                    background: 'none', border: 'none',
                    color: '#f1f5f9', cursor: 'pointer',
                    fontWeight: 700, fontSize: 14,
                    padding: 0, textDecoration: 'underline',
                  }}>
                  {item.student_name}
                </button>
                <span style={{ fontSize: 12, color: '#64748b' }}>{item.roll_number}</span>
                <span style={{
                  background: tc.bg, color: tc.color,
                  padding: '3px 10px', borderRadius: 12,
                  fontSize: 12, fontWeight: 700,
                }}>
                  {item.intervention_type}
                </span>
                <span style={{
                  fontSize: 12, fontWeight: 700,
                  color: item.status === 'open' ? '#27ae60' : '#64748b',
                  background: item.status === 'open' ? '#f0fff4' : '#334155',
                  padding: '2px 8px', borderRadius: 8,
                }}>
                  {item.status === 'open' ? '● Open' : '✓ Resolved'}
                </span>
              </div>
              <span style={{ fontSize: 12, color: '#64748b', whiteSpace: 'nowrap' }}>
                {item.created_at
                  ? new Date(item.created_at).toLocaleDateString('en-IN', {
                      day: '2-digit', month: 'short', year: 'numeric',
                    })
                  : '—'}
              </span>
            </div>
            <p style={{ margin: 0, fontSize: 13, color: '#94a3b8', lineHeight: 1.5 }}>
              {item.notes}
            </p>
            {item.outcome && (
              <div style={{
                marginTop: 8, padding: '6px 12px',
                background: '#0f172a', borderRadius: 8,
                fontSize: 12, color: '#94a3b8',
              }}>
                <strong>Outcome:</strong> {item.outcome}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
