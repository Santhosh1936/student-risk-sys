import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
  const [error, setError]       = useState('');
  const [filter, setFilter]     = useState('ALL');
  const [hoveredRow, setHoveredRow] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/teacher/risk-overview')
      .then(r => setStudents(r.data))
      .catch(() => setError('Could not load risk data. Please try again.'))
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

  const downloadCSV = () => {
    const headers = ['Name','Roll No','Branch','Semester','CGPA','SARS Score','Risk Level','Advisory'];
    const rows = students.map(s => [
      s.full_name || '',
      s.roll_number || '',
      s.branch || '',
      s.current_semester || '',
      s.cgpa?.toFixed(2) || '',
      s.sars_score?.toFixed(1) || '',
      s.risk_level || '',
      (s.advisory_text || '').replace(/,/g, ';'),
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sars_risk_report_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return (
    <p style={{ color: '#64748b', padding: 40 }}>
      Loading risk data...
    </p>
  );

  if (error) return (
    <div style={{
      background: 'rgba(248,113,113,0.08)', border: '1px solid #f87171',
      borderRadius: 10, padding: '14px 18px', color: '#f87171', fontSize: 13,
    }}>
      {error}
    </div>
  );

  return (
    <div>
      <h2 style={{ color: '#f1f5f9', marginBottom: 4 }}>
        Risk Monitor
      </h2>
      <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
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
              <div style={{ fontSize: 11, color: '#94a3b8' }}>{l}</div>
            </div>
          );
        })}
        <div style={{ background: '#334155', borderRadius: 10,
                      padding: '12px 20px', textAlign: 'center',
                      minWidth: 100 }}>
          <div style={{ fontSize: 22 }}>👥</div>
          <div style={{ fontSize: 22, fontWeight: 800,
                        color: '#f1f5f9' }}>
            {students.length}
          </div>
          <div style={{ fontSize: 11, color: '#94a3b8' }}>TOTAL</div>
        </div>
      </div>

      {/* -- Filter bar ------------------------------------------------------ */}
      <div style={{ display:'flex', gap:8, marginBottom:16, alignItems:'center', flexWrap:'wrap' }}>
        {levels.map(l => (
          <button key={l} onClick={() => setFilter(l)}
            style={{ padding: '6px 14px', borderRadius: 6, border: 'none',
                     background: filter === l ? '#1e3a5f' : '#334155',
                     color: filter === l ? '#fff' : '#94a3b8',
                     fontWeight: filter === l ? 700 : 400,
                     cursor: 'pointer', fontSize: 13 }}>
            {l}
          </button>
        ))}
        <button onClick={downloadCSV}
          style={{ padding:'6px 14px', borderRadius:6, border:'1px solid #334155',
                   background:'#1e293b', color:'#94a3b8', fontSize:13, cursor:'pointer',
                   marginLeft:'auto' }}>
          ⬇ Export CSV
        </button>
      </div>

      {/* -- Student table --------------------------------------------------- */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
          No students in {filter} category.
        </div>
      ) : (
        <div style={{ background: '#0f172a', borderRadius: 12,
                      border: '1px solid #334155', overflow: 'hidden' }}>
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
                const isHovered = hoveredRow === i;
                return (
                  <tr key={s.student_id}
                    onClick={() => navigate(`/teacher/students/${s.student_id}`)}
                    onMouseEnter={() => setHoveredRow(i)}
                    onMouseLeave={() => setHoveredRow(null)}
                    style={{
                      background: isHovered ? '#334155' : (i % 2 === 0 ? '#1e293b' : '#0f172a'),
                      borderBottom: '1px solid #1e293b',
                      cursor: 'pointer',
                    }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600,
                                 fontSize: 13, color: '#f1f5f9' }}>
                      {s.full_name}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12,
                                 color: '#94a3b8' }}>
                      {s.roll_number || '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 12,
                                 color: '#f1f5f9' }}>
                      {s.branch || '—'}
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: 13,
                                 textAlign: 'center', color: '#f1f5f9' }}>
                      {s.current_semester}
                    </td>
                    <td style={{ padding: '12px 14px', fontWeight: 700,
                                 color: '#f1f5f9', fontSize: 14 }}>
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
                                 color: '#94a3b8', maxWidth: 220 }}>
                      {s.advisory_text?.length > 80
                        ? s.advisory_text.substring(0, 80) + '...'
                        : (s.advisory_text || '—')}
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
