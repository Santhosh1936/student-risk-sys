import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const LEVEL_CFG = {
  HIGH:     { color: '#c0392b', bg: '#fff0f0', icon: '🔴' },
  MODERATE: { color: '#dd6b20', bg: '#fff5f0', icon: '🟠' },
  WATCH:    { color: '#d69e2e', bg: '#fffff0', icon: '🟡' },
  LOW:      { color: '#27ae60', bg: '#f0fff4', icon: '🟢' },
  UNKNOWN:  { color: '#999',    bg: '#f5f5f5', icon: '⚪' },
};

export default function RiskMonitorPage() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [filter, setFilter]     = useState('ALL');

  useEffect(() => {
    api.get('/teacher/risk-overview')
      .then(r => setStudents(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const levels = ['ALL', 'HIGH', 'MODERATE', 'WATCH', 'LOW'];

  const filtered = filter === 'ALL'
    ? students
    : students.filter(s => s.risk_level === filter);

  // Summary counts
  const counts = levels.slice(1).reduce((acc, l) => {
    acc[l] = students.filter(s => s.risk_level === l).length;
    return acc;
  }, {});

  if (loading) return (
    <p style={{ color: '#666', padding: 40 }}>
      Loading risk data...
    </p>
  );

  return (
    <div>
      <h2 style={{ color: '#1e3a5f', marginBottom: 4 }}>
        Risk Monitor
      </h2>
      <p style={{ color: '#666', fontSize: 14, marginBottom: 24 }}>
        All students ranked by SARS risk score (highest risk first)
      </p>

      {/* -- Summary tiles --------------------------------------------------- */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24,
                    flexWrap: 'wrap' }}>
        {levels.slice(1).map(l => {
          const cfg = LEVEL_CFG[l];
          return (
            <div key={l}
              onClick={() => setFilter(filter === l ? 'ALL' : l)}
              style={{ background: cfg.bg, border: `2px solid ${
                         filter === l ? cfg.color : 'transparent'}`,
                       borderRadius: 10, padding: '12px 20px',
                       textAlign: 'center', cursor: 'pointer',
                       minWidth: 100 }}>
              <div style={{ fontSize: 22 }}>{cfg.icon}</div>
              <div style={{ fontSize: 22, fontWeight: 800,
                            color: cfg.color }}>
                {counts[l]}
              </div>
              <div style={{ fontSize: 11, color: '#666' }}>{l}</div>
            </div>
          );
        })}
        <div style={{ background: '#f0f4f8', borderRadius: 10,
                      padding: '12px 20px', textAlign: 'center',
                      minWidth: 100 }}>
          <div style={{ fontSize: 22 }}>👥</div>
          <div style={{ fontSize: 22, fontWeight: 800,
                        color: '#1e3a5f' }}>
            {students.length}
          </div>
          <div style={{ fontSize: 11, color: '#666' }}>TOTAL</div>
        </div>
      </div>

      {/* -- Filter bar ------------------------------------------------------ */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {levels.map(l => (
          <button key={l} onClick={() => setFilter(l)}
            style={{ padding: '6px 14px', borderRadius: 6, border: 'none',
                     background: filter === l ? '#1e3a5f' : '#f0f4f8',
                     color: filter === l ? '#fff' : '#555',
                     fontWeight: filter === l ? 700 : 400,
                     cursor: 'pointer', fontSize: 13 }}>
            {l}
          </button>
        ))}
      </div>

      {/* -- Student table --------------------------------------------------- */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
          No students in {filter} category.
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 12,
                      border: '1px solid #e0e8f0', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#1e3a5f', color: '#fff' }}>
                {['Student', 'Roll No', 'Branch', 'Sem', 'CGPA',
                  'SARS Score', 'Risk Level', 'Advisory'].map(h => (
                  <th key={h} style={{ padding: '12px 14px',
                                       textAlign: 'left', fontSize: 12,
                                       fontWeight: 600 }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => {
                const cfg = LEVEL_CFG[s.risk_level] || LEVEL_CFG.UNKNOWN;
                return (
                  <tr key={s.student_id}
                    style={{ background: i % 2 === 0 ? '#f8fafd' : '#fff',
                             borderBottom: '1px solid #eef2f7' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600,
                                 fontSize: 13 }}>
                      {s.full_name}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12,
                                 color: '#666' }}>
                      {s.roll_number || '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12 }}>
                      {s.branch || '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 13,
                                 textAlign: 'center' }}>
                      {s.current_semester}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700,
                                 color: '#1e3a5f', fontSize: 14 }}>
                      {s.cgpa?.toFixed(2) ?? '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 800,
                                 color: cfg.color, fontSize: 16 }}>
                      {s.sars_score != null
                        ? s.sars_score.toFixed(1)
                        : '—'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span style={{
                        background: cfg.bg, color: cfg.color,
                        border: `1px solid ${cfg.color}`,
                        padding: '3px 10px', borderRadius: 12,
                        fontSize: 12, fontWeight: 700
                      }}>
                        {cfg.icon} {s.risk_level}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12,
                                 color: '#555', maxWidth: 220 }}>
                      {s.advisory_text
                        ? s.advisory_text.substring(0, 80) + '...'
                        : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
