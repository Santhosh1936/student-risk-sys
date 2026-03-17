// frontend/src/pages/student/AttendancePage.jsx
import React, { useEffect, useState, useCallback } from 'react';
import api from '../../services/api';

// ── helpers ──────────────────────────────────────────────────────────────────

function pctColor(pct) {
  if (pct == null) return '#64748b';
  if (pct >= 75) return '#34d399';
  if (pct >= 65) return '#fbbf24';
  return '#f87171';
}

// ── main component ────────────────────────────────────────────────────────────

export default function AttendancePage() {
  const [tab, setTab] = useState('view');      // 'view' | 'upload'

  return (
    <div className="fade-up">
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', marginBottom: 4 }}>
          Attendance
        </h1>
        <p style={{ fontSize: 14, color: '#64748b' }}>
          Track your attendance. Keeping it above 75% prevents exam-eligibility risk.
        </p>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {['view', 'upload'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
              cursor: 'pointer', border: '1px solid',
              borderColor: tab === t ? '#38bdf8' : '#1e293b',
              background: tab === t ? 'rgba(56,189,248,0.12)' : 'transparent',
              color: tab === t ? '#38bdf8' : '#64748b',
              transition: 'all 0.15s',
            }}
          >
            {t === 'view' ? 'View Records' : 'Add / Update'}
          </button>
        ))}
      </div>

      {tab === 'view'   && <ViewTab />}
      {tab === 'upload' && <UploadTab onSaved={() => setTab('view')} />}
    </div>
  );
}

// ── View tab ──────────────────────────────────────────────────────────────────

function ViewTab() {
  const [data, setData]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const [error, setError]     = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    api.get('/student/attendance')
      .then((r) => setData(r.data))
      .catch(() => setError('Could not load attendance records.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (semNo) => {
    setDeleting(semNo);
    setConfirmDelete(null);
    try {
      await api.delete(`/student/attendance/${semNo}`);
      load();
    } catch (e) {
      setError(e.response?.data?.detail || 'Delete failed.');
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <p style={{ color: '#64748b', padding: 16 }}>Loading…</p>;

  if (error) return (
    <div style={{
      background: 'rgba(248,113,113,0.08)', border: '1px solid #f87171',
      borderRadius: 10, padding: '12px 16px', color: '#f87171', fontSize: 13,
    }}>
      {error}
    </div>
  );

  if (data.length === 0) return (
    <div style={{ textAlign: 'center', padding: '60px 0', color: '#64748b' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>📋</div>
      <h3 style={{ color: '#f1f5f9', marginBottom: 8 }}>No attendance data yet</h3>
      <p style={{ fontSize: 14 }}>Switch to the Add / Update tab to enter your attendance.</p>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {data.map((sem) => {
        const subjs = sem.subjects || [];
        const below = subjs.filter((s) => (s.percentage ?? 0) < 75).length;
        const avgPct = subjs.length
          ? subjs.reduce((acc, s) => acc + (s.percentage ?? 0), 0) / subjs.length
          : null;

        return (
          <div key={sem.semester_no} style={{
            background: '#111827', border: '1px solid #1e293b',
            borderRadius: 12, overflow: 'hidden',
          }}>
            {/* Semester header */}
            <div style={{
              padding: '14px 20px', borderBottom: '1px solid #1e293b',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <span style={{ fontWeight: 700, fontSize: 15, color: '#f1f5f9' }}>
                  Semester {sem.semester_no}
                </span>
                <span style={{ fontSize: 13, color: '#475569', marginLeft: 12 }}>
                  {subjs.length} subject{subjs.length !== 1 ? 's' : ''}
                  {below > 0 && (
                    <span style={{ color: '#f87171', marginLeft: 8 }}>
                      · {below} below 75%
                    </span>
                  )}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                {avgPct != null && (
                  <span style={{
                    fontSize: 20, fontWeight: 800,
                    color: pctColor(avgPct),
                    fontFamily: "'Space Mono', monospace",
                  }}>
                    {avgPct.toFixed(1)}%
                    <span style={{ fontSize: 11, color: '#475569', marginLeft: 4 }}>avg</span>
                  </span>
                )}
                {confirmDelete === sem.semester_no ? (
                  <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                    <span style={{ fontSize:12, color:'#f87171' }}>Delete?</span>
                    <button
                      onClick={() => handleDelete(sem.semester_no)}
                      disabled={deleting === sem.semester_no}
                      style={{ padding:'3px 10px', background:'#ef4444', color:'#fff',
                               border:'none', borderRadius:5, fontSize:11,
                               cursor: deleting === sem.semester_no ? 'not-allowed' : 'pointer' }}>
                      Yes
                    </button>
                    <button
                      onClick={() => setConfirmDelete(null)}
                      style={{ padding:'3px 10px', background:'#334155', color:'#94a3b8',
                               border:'none', borderRadius:5, fontSize:11, cursor:'pointer' }}>
                      No
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmDelete(sem.semester_no)}
                    disabled={deleting === sem.semester_no}
                    style={{
                      background: 'rgba(248,113,113,0.1)', border: '1px solid #f87171',
                      color: '#f87171', borderRadius: 7, padding: '5px 12px',
                      fontSize: 12,
                      cursor: deleting === sem.semester_no ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {deleting === sem.semester_no ? 'Deleting…' : '🗑 Delete'}
                  </button>
                )}
              </div>
            </div>

            {/* Subject rows */}
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#0a0f1e' }}>
                  {['Subject', 'Attended', 'Total', 'Percentage'].map((h) => (
                    <th key={h} style={{
                      padding: '9px 16px', textAlign: 'left',
                      fontSize: 11, color: '#475569', fontWeight: 600,
                      textTransform: 'uppercase', letterSpacing: '0.05em',
                      borderBottom: '1px solid #1e293b',
                    }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {subjs.map((s, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '10px 16px', color: '#f1f5f9' }}>{s.subject_name}</td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>{s.classes_attended}</td>
                    <td style={{ padding: '10px 16px', color: '#94a3b8' }}>{s.total_classes}</td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{
                        background: `${pctColor(s.percentage)}22`,
                        border: `1px solid ${pctColor(s.percentage)}55`,
                        color: pctColor(s.percentage),
                        borderRadius: 12, padding: '2px 10px',
                        fontSize: 12, fontWeight: 700,
                      }}>
                        {s.percentage != null ? `${s.percentage}%` : '—'}
                      </span>
                      {(s.percentage ?? 0) < 75 && (
                        <span style={{
                          color: '#f87171', fontSize: 11, marginLeft: 8,
                        }}>
                          below threshold
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

// ── Upload tab ────────────────────────────────────────────────────────────────

function UploadTab({ onSaved }) {
  const [semesters, setSemesters]   = useState([]);
  const [semNo, setSemNo]           = useState('');
  const [rows, setRows]             = useState([]);   // [{subject_name, classes_attended, total_classes}]
  const [saving, setSaving]         = useState(false);
  const [error, setError]           = useState('');
  const [loadingSems, setLoadingSems] = useState(true);

  // Load available semesters to pre-fill subject names
  useEffect(() => {
    api.get('/student/semesters')
      .then((r) => setSemesters(r.data))
      .catch(() => {})
      .finally(() => setLoadingSems(false));
  }, []);

  // When semester selection changes, pre-fill subject rows from grade data
  const handleSemChange = (val) => {
    setSemNo(val);
    setError('');
    const sem = semesters.find((s) => String(s.semester_no) === val);
    if (sem && sem.subjects && sem.subjects.length > 0) {
      setRows(
        sem.subjects
          .filter((s) => (s.credits ?? 0) > 0)   // skip 0-credit subjects
          .map((s) => ({
            subject_name: s.subject_name,
            classes_attended: '',
            total_classes: '',
          }))
      );
    } else {
      // No grade data for this semester — start with one blank row
      setRows([{ subject_name: '', classes_attended: '', total_classes: '' }]);
    }
  };

  const updateRow = (idx, field, value) => {
    setRows((prev) => prev.map((r, i) => i === idx ? { ...r, [field]: value } : r));
  };

  const addRow = () => {
    setRows((prev) => [...prev, { subject_name: '', classes_attended: '', total_classes: '' }]);
  };

  const removeRow = (idx) => {
    setRows((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!semNo) { setError('Select a semester.'); return; }
    if (rows.length === 0) { setError('Add at least one subject.'); return; }

    for (const r of rows) {
      if (!r.subject_name.trim()) { setError('Subject name cannot be blank.'); return; }
      const att = parseInt(r.classes_attended, 10);
      const tot = parseInt(r.total_classes, 10);
      if (isNaN(att) || att < 0) { setError(`Invalid classes attended for "${r.subject_name}".`); return; }
      if (isNaN(tot) || tot <= 0) { setError(`Total classes must be > 0 for "${r.subject_name}".`); return; }
      if (att > tot) { setError(`Attended > total for "${r.subject_name}".`); return; }
    }

    setSaving(true);
    try {
      await api.post('/student/attendance', {
        semester_no: parseInt(semNo, 10),
        subjects: rows.map((r) => ({
          subject_name: r.subject_name.trim(),
          classes_attended: parseInt(r.classes_attended, 10),
          total_classes: parseInt(r.total_classes, 10),
        })),
      });
      onSaved();
    } catch (e) {
      const detail = e.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Save failed. Check inputs.');
    } finally {
      setSaving(false);
    }
  };

  if (loadingSems) return <p style={{ color: '#64748b', padding: 16 }}>Loading…</p>;

  return (
    <form onSubmit={handleSubmit}>
      {/* Semester selector */}
      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Semester</label>
        <select
          value={semNo}
          onChange={(e) => handleSemChange(e.target.value)}
          style={inputStyle}
        >
          <option value="">— select semester —</option>
          {semesters.length > 0
            ? semesters.map((s) => (
                <option key={s.semester_no} value={String(s.semester_no)}>
                  Semester {s.semester_no}
                </option>
              ))
            : [1,2,3,4,5,6,7,8].map((n) => (
                <option key={n} value={String(n)}>Semester {n}</option>
              ))
          }
        </select>
        {semesters.length === 0 && (
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>
            Tip: Upload a marksheet first so subject names are pre-filled automatically.
          </p>
        )}
      </div>

      {/* Subject rows */}
      {semNo && (
        <>
          <div style={{ marginBottom: 10, fontSize: 13, color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Subjects
          </div>

          {rows.map((row, idx) => (
            <div key={idx} style={{
              display: 'grid',
              gridTemplateColumns: '1fr 120px 120px 36px',
              gap: 8, marginBottom: 8, alignItems: 'center',
            }}>
              <input
                placeholder="Subject name"
                value={row.subject_name}
                onChange={(e) => updateRow(idx, 'subject_name', e.target.value)}
                style={inputStyle}
              />
              <input
                type="number" min="0"
                placeholder="Attended"
                value={row.classes_attended}
                onChange={(e) => updateRow(idx, 'classes_attended', e.target.value)}
                style={{ ...inputStyle, textAlign: 'center' }}
              />
              <input
                type="number" min="1"
                placeholder="Total"
                value={row.total_classes}
                onChange={(e) => updateRow(idx, 'total_classes', e.target.value)}
                style={{ ...inputStyle, textAlign: 'center' }}
              />
              <button
                type="button"
                onClick={() => removeRow(idx)}
                disabled={rows.length === 1}
                style={{
                  background: 'rgba(248,113,113,0.1)',
                  border: '1px solid #f87171',
                  color: '#f87171', borderRadius: 7,
                  width: 36, height: 36, fontSize: 16,
                  cursor: 'pointer', display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  opacity: rows.length === 1 ? 0.3 : 1,
                }}
              >
                ×
              </button>
            </div>
          ))}

          <button
            type="button"
            onClick={addRow}
            style={{
              background: 'transparent', border: '1px dashed #1e293b',
              color: '#64748b', borderRadius: 8, padding: '8px 16px',
              fontSize: 13, cursor: 'pointer', width: '100%', marginBottom: 20,
            }}
          >
            + Add subject
          </button>
        </>
      )}

      {/* Error */}
      {error && (
        <div style={{
          background: 'rgba(248,113,113,0.08)', border: '1px solid #f8717180',
          borderRadius: 8, padding: '10px 14px',
          color: '#f87171', fontSize: 13, marginBottom: 16,
        }}>
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={saving || !semNo}
        style={{
          background: semNo ? '#38bdf8' : '#1e293b',
          color: semNo ? '#0a0f1e' : '#475569',
          border: 'none', borderRadius: 9, padding: '11px 28px',
          fontSize: 14, fontWeight: 700, cursor: semNo ? 'pointer' : 'not-allowed',
        }}
      >
        {saving ? 'Saving…' : 'Save Attendance'}
      </button>
    </form>
  );
}

// ── styles ────────────────────────────────────────────────────────────────────

const labelStyle = {
  display: 'block', fontSize: 12, color: '#64748b',
  fontWeight: 600, textTransform: 'uppercase',
  letterSpacing: '0.05em', marginBottom: 6,
};

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  background: '#0a0f1e', border: '1px solid #1e293b',
  borderRadius: 8, padding: '10px 14px',
  color: '#f1f5f9', fontSize: 13, outline: 'none',
};
