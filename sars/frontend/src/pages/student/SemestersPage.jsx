// frontend/src/pages/student/SemestersPage.jsx
import React, { useEffect, useState } from 'react';
import api from '../../services/api';

export default function SemestersPage() {
  const [semesters, setSemesters] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [expanded, setExpanded]   = useState(null);

  useEffect(() => {
    api.get('/student/semesters')
      .then((r) => setSemesters(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const gradeColor = (g) => ({
    'O':  '#16a34a', 'A+': '#22c55e', 'A':  '#3b82f6',
    'B+': '#8b5cf6', 'B':  '#f97316', 'C':  '#eab308',
    'D':  '#ef4444', 'F':  '#dc2626', 'AB': '#6b7280',
    'S*': '#9ca3af', 'S':  '#9ca3af',
  }[g] || '#6b7280');

  if (loading) {
    return <p style={{ color: '#64748b', padding: 32 }}>Loading academic records…</p>;
  }

  if (semesters.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#64748b' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📭</div>
        <h3 style={{ color: '#f1f5f9', marginBottom: 8 }}>No marksheets uploaded yet</h3>
        <p style={{ fontSize: 14 }}>
          Go to Upload Marks to add your grade sheets.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>
          Academic Records
        </h1>
        <p style={{ fontSize: 14, color: '#64748b' }}>
          {semesters.length} semester{semesters.length !== 1 ? 's' : ''} uploaded
        </p>
      </div>

      {/* SGPA tile bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
        {semesters.map((s) => (
          <div
            key={s.semester_no}
            onClick={() => setExpanded(expanded === s.semester_no ? null : s.semester_no)}
            style={{
              background: '#1e3a5f', color: '#fff',
              borderRadius: 10, padding: '12px 20px',
              textAlign: 'center', minWidth: 88, cursor: 'pointer',
              border: expanded === s.semester_no
                ? '1px solid #38bdf8' : '1px solid transparent',
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 800 }}>{s.gpa ?? '—'}</div>
            <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>Sem {s.semester_no}</div>
          </div>
        ))}
      </div>

      {/* Semester cards */}
      {semesters.map((sem) => (
        <div
          key={sem.semester_no}
          style={{
            background: '#111827', borderRadius: 12, marginBottom: 14,
            border: '1px solid #1e293b', overflow: 'hidden',
          }}
        >
          {/* Header row */}
          <div
            onClick={() =>
              setExpanded(expanded === sem.semester_no ? null : sem.semester_no)
            }
            style={{
              padding: '16px 20px', cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              background: expanded === sem.semester_no ? '#0f172a' : 'transparent',
            }}
          >
            <div>
              <span style={{ fontWeight: 700, fontSize: 15, color: '#f1f5f9' }}>
                Semester {sem.semester_no}
              </span>
              <span style={{ fontSize: 13, color: '#475569', marginLeft: 12 }}>
                {sem.subjects?.length || 0} subjects
                {sem.credits_earned != null && ` · ${sem.credits_earned} credits`}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              {sem.gpa != null && (
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#38bdf8' }}>
                    {sem.gpa}
                  </div>
                  <div style={{ fontSize: 11, color: '#475569' }}>SGPA</div>
                </div>
              )}
              <span style={{ fontSize: 16, color: '#475569' }}>
                {expanded === sem.semester_no ? '▲' : '▼'}
              </span>
            </div>
          </div>

          {/* Expanded subject table */}
          {expanded === sem.semester_no && sem.subjects && (
            <div style={{ borderTop: '1px solid #1e293b', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#0a0f1e' }}>
                    {['Code', 'Subject', 'Grade', 'Points', 'Credits'].map((h) => (
                      <th
                        key={h}
                        style={{
                          padding: '10px 16px', textAlign: 'left',
                          fontSize: 11, color: '#475569',
                          fontWeight: 600, textTransform: 'uppercase',
                          letterSpacing: '0.05em',
                          borderBottom: '1px solid #1e293b',
                        }}
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sem.subjects.map((s, i) => (
                    <tr
                      key={i}
                      style={{ borderBottom: '1px solid #1e293b' }}
                    >
                      <td style={{
                        padding: '10px 16px', color: '#64748b',
                        fontFamily: 'monospace', fontSize: 12,
                      }}>
                        {s.subject_code || '—'}
                      </td>
                      <td style={{ padding: '10px 16px', color: '#f1f5f9' }}>
                        {s.subject_name}
                        {s.is_backlog && (
                          <span style={{
                            color: '#f87171', fontSize: 11,
                            marginLeft: 8, fontWeight: 600,
                          }}>
                            BACKLOG
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '10px 16px' }}>
                        <span style={{
                          background: gradeColor(s.grade_letter),
                          color: '#fff', padding: '2px 10px',
                          borderRadius: 12, fontSize: 12, fontWeight: 700,
                        }}>
                          {s.grade_letter}
                        </span>
                      </td>
                      <td style={{
                        padding: '10px 16px', fontWeight: 700,
                        color: '#38bdf8', fontSize: 13,
                      }}>
                        {s.grade_points}
                      </td>
                      <td style={{ padding: '10px 16px', color: '#94a3b8' }}>
                        {s.credits}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
