// frontend/src/pages/teacher/StudentDetailPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../services/api';

const GRADE_COLOR = {
  O:'#27ae60', 'A+':'#2ecc71', A:'#3498db',
  'B+':'#8e44ad', B:'#e67e22', C:'#f39c12',
  D:'#e74c3c', F:'#c0392b', AB:'#7f8c8d',
};
const RISK_CFG = {
  HIGH:    {color:'#c0392b', bg:'#fff0f0', icon:'🔴'},
  MODERATE:{color:'#dd6b20', bg:'#fff5f0', icon:'🟠'},
  WATCH:   {color:'#d69e2e', bg:'#fffff0', icon:'🟡'},
  LOW:     {color:'#27ae60', bg:'#f0fff4', icon:'🟢'},
};
const INTERVENTION_TYPES = [
  'Counseling','Tutoring','Parent Meeting',
  'Written Warning','Academic Probation','Other',
];
const TYPE_COLORS = {
  'Counseling':        {bg:'#e8f4fd', color:'#2980b9'},
  'Tutoring':          {bg:'#e8fdf4', color:'#27ae60'},
  'Parent Meeting':    {bg:'#fef9e7', color:'#d69e2e'},
  'Written Warning':   {bg:'#fef0e7', color:'#dd6b20'},
  'Academic Probation':{bg:'#fde8e8', color:'#c0392b'},
  'Other':             {bg:'#f0f0f0', color:'#666'},
};

export default function StudentDetailPage() {
  const { studentId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSem, setExpandedSem] = useState(null);

  // Intervention form state
  const [showLogForm, setShowLogForm] = useState(false);
  const [logForm, setLogForm] = useState({
    intervention_type: 'Counseling', notes: '',
  });
  const [resolveId, setResolveId] = useState(null);
  const [outcome, setOutcome] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });
  const [loadError, setLoadError] = useState('');

  const load = useCallback(() => {
    setLoading(true);
    setLoadError('');
    api.get(`/teacher/students/${studentId}/profile`)
      .then(r => setProfile(r.data))
      .catch(e => setLoadError(
        e.response?.status === 404
          ? 'Student not found.'
          : 'Failed to load profile. Please try again.'
      ))
      .finally(() => setLoading(false));
  }, [studentId]);

  useEffect(() => { load(); }, [load]);

  const handleLog = async () => {
    if (!logForm.notes.trim()) {
      setMsg({ type: 'error', text: 'Notes cannot be empty.' });
      return;
    }
    setSaving(true); setMsg({ type: '', text: '' });
    try {
      await api.post('/teacher/interventions', {
        student_id: parseInt(studentId),
        intervention_type: logForm.intervention_type,
        notes: logForm.notes.trim(),
      });
      setMsg({ type: 'success', text: 'Intervention logged.' });
      setShowLogForm(false);
      setLogForm({ intervention_type: 'Counseling', notes: '' });
      load();
    } catch (e) {
      setMsg({
        type: 'error',
        text: e.response?.data?.detail || 'Failed to log.',
      });
    } finally { setSaving(false); }
  };

  const handleResolve = async (id) => {
    if (!outcome.trim()) {
      setMsg({ type: 'error', text: 'Outcome required.' });
      return;
    }
    setSaving(true); setMsg({ type: '', text: '' });
    try {
      await api.patch(`/teacher/interventions/${id}/resolve`, {
        outcome: outcome.trim(),
      });
      setMsg({ type: 'success', text: 'Intervention resolved.' });
      setResolveId(null); setOutcome('');
      load();
    } catch (e) {
      setMsg({
        type: 'error',
        text: e.response?.data?.detail || 'Failed.',
      });
    } finally { setSaving(false); }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
      Loading student profile...
    </div>
  );
  if (loadError || !profile) return (
    <div style={{
      background: 'rgba(248,113,113,0.08)', border: '1px solid #f87171',
      borderRadius: 10, padding: '14px 18px', color: '#f87171', fontSize: 13,
    }}>
      {loadError || 'Student not found.'}
    </div>
  );

  const risk = profile.risk;
  const rcfg = RISK_CFG[risk?.risk_level] || RISK_CFG.WATCH;

  const TABS = [
    { id: 'overview',       label: '📊 Overview' },
    { id: 'grades',         label: '📚 Grades' },
    { id: 'attendance',     label: '📋 Attendance' },
    { id: 'risk',           label: '⚠️ Risk' },
    {
      id: 'interventions',
      label: `🔔 Interventions (${profile.intervention_summary?.open || 0} open)`,
    },
  ];

  return (
    <div style={{ maxWidth: 960 }}>
      {/* Back */}
      <button onClick={() => navigate('/teacher/students')}
        style={{
          background: 'none', border: 'none',
          color: '#94a3b8', cursor: 'pointer',
          fontSize: 13, marginBottom: 16,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
        ← Back
      </button>

      {/* Student header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        alignItems: 'flex-start', marginBottom: 24,
        background: '#1e293b', border: '1px solid #334155',
        borderRadius: 12, padding: 20,
      }}>
        <div>
          <h2 style={{ color: '#f1f5f9', margin: '0 0 4px', fontSize: 22 }}>
            {profile.full_name}
          </h2>
          <div style={{ color: '#64748b', fontSize: 13, lineHeight: 1.8 }}>
            Roll: {profile.roll_number || '—'} &nbsp;·&nbsp;
            Branch: {profile.branch || '—'} &nbsp;·&nbsp;
            Semester: {profile.current_semester || '—'} &nbsp;·&nbsp;
            Email: {profile.email || '—'}
          </div>
        </div>
        <div style={{ textAlign: 'center', minWidth: 70 }}>
          <div style={{ fontSize: 28, fontWeight: 900, color: '#f1f5f9' }}>
            {profile.cgpa?.toFixed(2) ?? '—'}
          </div>
          <div style={{ fontSize: 11, color: '#64748b' }}>CGPA</div>
        </div>
      </div>

      {/* Quick stat cards */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        {[
          {
            label: 'SARS Score',
            value: risk ? `${risk.sars_score?.toFixed(1)}` : '—',
            sub: risk?.risk_level || 'Not computed',
            bg: rcfg.bg, color: rcfg.color,
          },
          {
            label: 'Semesters Uploaded',
            value: profile.semesters_uploaded,
            sub: 'grade sheets',
            bg: '#0f172a', color: '#f1f5f9',
          },
          {
            label: 'Total Backlogs',
            value: profile.total_backlogs,
            sub: profile.total_backlogs === 0 ? 'None ✅' : 'Need attention',
            bg: profile.total_backlogs > 0 ? '#fff0f0' : '#f0fff4',
            color: profile.total_backlogs > 0 ? '#c0392b' : '#27ae60',
          },
          {
            label: 'Avg Attendance',
            value: profile.overall_attendance != null
              ? `${profile.overall_attendance}%` : '—',
            sub: profile.overall_attendance == null
              ? 'Not uploaded'
              : profile.overall_attendance >= 75
                ? 'Above 75% ✅' : 'Below 75% ⚠️',
            bg: profile.overall_attendance == null
              ? '#0f172a'
              : profile.overall_attendance >= 75 ? '#f0fff4' : '#fff0f0',
            color: '#f1f5f9',
          },
          {
            label: 'Open Interventions',
            value: profile.intervention_summary?.open || 0,
            sub: `${profile.intervention_summary?.total || 0} total`,
            bg: '#0f172a', color: '#f1f5f9',
          },
        ].map(c => (
          <div key={c.label} style={{
            background: c.bg, border: '1px solid #334155',
            borderRadius: 10, padding: '14px 18px',
            minWidth: 130, flex: 1,
          }}>
            <div style={{ fontSize: 24, fontWeight: 900, color: c.color }}>
              {c.value}
            </div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#f1f5f9', marginTop: 2 }}>
              {c.label}
            </div>
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)}
            style={{
              padding: '8px 16px', borderRadius: 8,
              border: 'none', fontSize: 13, fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === t.id ? '#1e3a5f' : '#334155',
              color: activeTab === t.id ? '#fff' : '#94a3b8',
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── TAB: OVERVIEW ────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div>
          {profile.semesters.length > 0 && (
            <div style={{
              background: '#1e293b', border: '1px solid #334155',
              borderRadius: 12, padding: 20, marginBottom: 16,
            }}>
              <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
                SGPA Trend
              </h3>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {profile.semesters.map(s => (
                  <div key={s.semester_no} style={{
                    textAlign: 'center', background: '#0f172a',
                    border: '1px solid #334155', borderRadius: 8,
                    padding: '10px 16px', minWidth: 70,
                  }}>
                    <div style={{ fontSize: 20, fontWeight: 900, color: '#f1f5f9' }}>
                      {s.sgpa?.toFixed(2) ?? '—'}
                    </div>
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      Sem {s.semester_no}
                    </div>
                    {s.backlog_count > 0 && (
                      <div style={{ fontSize: 10, color: '#c0392b', marginTop: 2 }}>
                        {s.backlog_count} backlog{s.backlog_count > 1 ? 's' : ''}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {risk?.advisory_text && (
            <div style={{
              background: '#0f172a', border: '1px solid #334155',
              borderRadius: 12, padding: 20,
            }}>
              <h3 style={{ color: '#f1f5f9', margin: '0 0 10px', fontSize: 15 }}>
                💡 AI Advisory Summary
              </h3>
              <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
                {risk.advisory_text}
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── TAB: GRADES ──────────────────────────────────────── */}
      {activeTab === 'grades' && (
        <div>
          {profile.semesters.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
              No grade data uploaded yet.
            </div>
          ) : (
            profile.semesters.map(sem => (
              <div key={sem.semester_no} style={{
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: 12, marginBottom: 12, overflow: 'hidden',
              }}>
                <div
                  onClick={() => setExpandedSem(
                    expandedSem === sem.semester_no ? null : sem.semester_no
                  )}
                  style={{
                    display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', padding: '14px 20px',
                    background: '#0f172a', cursor: 'pointer',
                    borderBottom: expandedSem === sem.semester_no
                      ? '1px solid #334155' : 'none',
                  }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15 }}>
                      Semester {sem.semester_no}
                    </span>
                    <span style={{ fontWeight: 700, color: '#3498db', fontSize: 14 }}>
                      SGPA: {sem.sgpa?.toFixed(2) ?? '—'}
                    </span>
                    <span style={{ fontSize: 12, color: '#64748b' }}>
                      {sem.subject_count} subjects
                      &nbsp;·&nbsp;
                      {sem.credits_earned}/{sem.credits_attempted} cr
                    </span>
                    {sem.backlog_count > 0 && (
                      <span style={{
                        background: '#fff0f0', color: '#c0392b',
                        fontSize: 11, fontWeight: 700,
                        padding: '2px 8px', borderRadius: 8,
                      }}>
                        {sem.backlog_count} backlog{sem.backlog_count > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  <span style={{ color: '#64748b', fontSize: 18 }}>
                    {expandedSem === sem.semester_no ? '▲' : '▼'}
                  </span>
                </div>

                {expandedSem === sem.semester_no && (
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: '#334155' }}>
                        {['Code', 'Subject', 'Grade', 'Points', 'Credits', 'Status'].map(h => (
                          <th key={h} style={{
                            padding: '8px 14px', textAlign: 'left',
                            fontSize: 12, color: '#94a3b8', fontWeight: 600,
                          }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sem.subjects.map((s, i) => (
                        <tr key={i} style={{
                          borderTop: '1px solid #334155',
                          background: s.is_backlog ? 'rgba(248,113,113,0.05)' : '#0f172a',
                        }}>
                          <td style={{ padding: '9px 14px', fontSize: 12, color: '#64748b' }}>
                            {s.subject_code || '—'}
                          </td>
                          <td style={{ padding: '9px 14px', fontSize: 13, fontWeight: 500, color: '#f1f5f9' }}>
                            {s.subject_name}
                          </td>
                          <td style={{ padding: '9px 14px' }}>
                            <span style={{
                              background: GRADE_COLOR[s.grade_letter] || '#ddd',
                              color: '#fff', padding: '3px 10px',
                              borderRadius: 6, fontSize: 12, fontWeight: 700,
                            }}>
                              {s.grade_letter}
                            </span>
                          </td>
                          <td style={{ padding: '9px 14px', fontSize: 13, fontWeight: 600, color: '#f1f5f9' }}>
                            {s.grade_points}
                          </td>
                          <td style={{ padding: '9px 14px', fontSize: 13, color: '#94a3b8' }}>
                            {s.credits}
                          </td>
                          <td style={{ padding: '9px 14px', fontSize: 12 }}>
                            {s.is_backlog
                              ? <span style={{ color: '#c0392b', fontWeight: 700 }}>⚠️ Backlog</span>
                              : <span style={{ color: '#27ae60' }}>✓ Pass</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* ── TAB: ATTENDANCE ──────────────────────────────────── */}
      {activeTab === 'attendance' && (
        <div>
          {Object.keys(profile.attendance_by_semester).length === 0 ? (
            <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
              No attendance data uploaded by this student.
            </div>
          ) : (
            Object.entries(profile.attendance_by_semester)
              .sort(([a], [b]) => a - b)
              .map(([sem, subjects]) => {
                const avg = subjects.reduce(
                  (acc, s) => acc + (s.percentage || 0), 0
                ) / subjects.length;
                return (
                  <div key={sem} style={{
                    background: '#1e293b', border: '1px solid #334155',
                    borderRadius: 12, marginBottom: 12, overflow: 'hidden',
                  }}>
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      padding: '12px 20px', background: '#0f172a',
                      borderBottom: '1px solid #334155',
                    }}>
                      <span style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 15 }}>
                        Semester {sem}
                      </span>
                      <span style={{
                        fontWeight: 700, fontSize: 14,
                        color: avg >= 75 ? '#27ae60' : '#c0392b',
                      }}>
                        Avg: {avg.toFixed(1)}%{avg < 75 ? ' ⚠️' : ' ✅'}
                      </span>
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ background: '#334155' }}>
                          {['Subject', 'Attended', 'Total', '%'].map(h => (
                            <th key={h} style={{
                              padding: '7px 14px', textAlign: 'left',
                              fontSize: 12, color: '#94a3b8', fontWeight: 600,
                            }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {subjects.map((s, i) => (
                          <tr key={i} style={{ borderTop: '1px solid #334155' }}>
                            <td style={{ padding: '9px 14px', fontSize: 13, color: '#f1f5f9' }}>
                              {s.subject_name}
                            </td>
                            <td style={{ padding: '9px 14px', fontSize: 13, color: '#94a3b8' }}>
                              {s.classes_attended}
                            </td>
                            <td style={{ padding: '9px 14px', fontSize: 13, color: '#94a3b8' }}>
                              {s.total_classes}
                            </td>
                            <td style={{
                              padding: '9px 14px', fontWeight: 700, fontSize: 13,
                              color: s.percentage >= 75 ? '#27ae60' : '#c0392b',
                            }}>
                              {s.percentage}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              })
          )}
        </div>
      )}

      {/* ── TAB: RISK ────────────────────────────────────────── */}
      {activeTab === 'risk' && (
        <div>
          {!risk ? (
            <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
              Risk score not yet computed for this student.
            </div>
          ) : (
            <>
              <div style={{
                background: rcfg.bg, border: `2px solid ${rcfg.color}`,
                borderRadius: 16, padding: 28, marginBottom: 20,
                textAlign: 'center',
              }}>
                <div style={{ fontSize: 40 }}>{rcfg.icon}</div>
                <div style={{ fontSize: 60, fontWeight: 900, color: rcfg.color, lineHeight: 1 }}>
                  {risk.sars_score?.toFixed(1)}
                </div>
                <div style={{ fontSize: 12, color: '#64748b', margin: '4px 0 10px' }}>
                  out of 100
                </div>
                <div style={{
                  display: 'inline-block', background: rcfg.color,
                  color: '#fff', padding: '5px 18px',
                  borderRadius: 20, fontWeight: 700, fontSize: 15,
                }}>
                  {risk.risk_level}
                </div>
                <div style={{ marginTop: 12, fontSize: 12, color: '#64748b' }}>
                  Confidence: {((risk.confidence || 0) * 100).toFixed(0)}%
                  &nbsp;·&nbsp;
                  {risk.computed_at
                    ? new Date(risk.computed_at).toLocaleString()
                    : '—'}
                </div>
              </div>

              {risk.factor_breakdown && Object.keys(risk.factor_breakdown).length > 0 && (
                <div style={{
                  background: '#1e293b', border: '1px solid #334155',
                  borderRadius: 12, padding: 20, marginBottom: 20,
                }}>
                  <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
                    Score Breakdown
                  </h3>
                  {[
                    {
                      label: 'GPA Trend', weight: '40%',
                      score: risk.factor_breakdown.gpa_risk,
                      contrib: risk.factor_breakdown.gpa_component,
                      detail: `CGPA: ${risk.factor_breakdown.cgpa} · Trend: ${risk.factor_breakdown.trend_direction}`,
                      color: '#3498db',
                    },
                    {
                      label: 'Backlog Count', weight: '35%',
                      score: risk.factor_breakdown.backlog_risk,
                      contrib: risk.factor_breakdown.backlog_component,
                      detail: `Total backlogs: ${risk.factor_breakdown.total_backlogs}`,
                      color: '#e67e22',
                    },
                    {
                      label: 'Attendance', weight: '25%',
                      score: risk.factor_breakdown.attendance_risk,
                      contrib: risk.factor_breakdown.attendance_component,
                      detail: risk.factor_breakdown.avg_attendance != null
                        ? `Avg: ${risk.factor_breakdown.avg_attendance}%`
                        : 'No attendance data',
                      color: '#9b59b6',
                    },
                  ].map(f => (
                    <div key={f.label} style={{ marginBottom: 16 }}>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between',
                        marginBottom: 4,
                      }}>
                        <div>
                          <span style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 13 }}>
                            {f.label}
                          </span>
                          <span style={{ color: '#64748b', fontSize: 11, marginLeft: 6 }}>
                            ({f.weight})
                          </span>
                        </div>
                        <span style={{ fontWeight: 700, color: f.color, fontSize: 14 }}>
                          {f.score?.toFixed(1) ?? '—'}/100
                          &nbsp;→&nbsp;
                          {f.contrib?.toFixed(2) ?? '—'} pts
                        </span>
                      </div>
                      <div style={{
                        height: 10, background: '#334155',
                        borderRadius: 5, overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', borderRadius: 5,
                          background: f.color,
                          width: `${Math.min(100, f.score || 0)}%`,
                          transition: 'width 0.5s',
                        }} />
                      </div>
                      <div style={{ fontSize: 11, color: '#64748b', marginTop: 3 }}>
                        {f.detail}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {risk.advisory_text && (
                <div style={{
                  background: '#0f172a', border: '1px solid #334155',
                  borderRadius: 12, padding: 20,
                }}>
                  <h3 style={{ color: '#f1f5f9', margin: '0 0 10px', fontSize: 15 }}>
                    💡 Advisory
                  </h3>
                  <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
                    {risk.advisory_text}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── TAB: INTERVENTIONS ───────────────────────────────── */}
      {activeTab === 'interventions' && (
        <div>
          {msg.text && (
            <div style={{
              background: msg.type === 'success' ? '#f0fff4' : '#fff0f0',
              border: `1px solid ${msg.type === 'success' ? '#9ae6b4' : '#f5c6c6'}`,
              borderRadius: 8, padding: '10px 14px',
              marginBottom: 12,
              color: msg.type === 'success' ? '#276749' : '#c0392b',
              fontSize: 13,
            }}>
              {msg.type === 'success' ? '✅' : '❌'} {msg.text}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
            <button
              onClick={() => { setShowLogForm(!showLogForm); setMsg({ type: '', text: '' }); }}
              style={{
                padding: '9px 20px', background: '#1e3a5f', color: '#fff',
                border: 'none', borderRadius: 8, fontSize: 13,
                fontWeight: 600, cursor: 'pointer',
              }}>
              {showLogForm ? '✕ Cancel' : '+ Log Intervention'}
            </button>
          </div>

          {showLogForm && (
            <div style={{
              background: '#0f172a', border: '1px solid #334155',
              borderRadius: 12, padding: 20, marginBottom: 20,
            }}>
              <h4 style={{ color: '#f1f5f9', margin: '0 0 16px' }}>New Intervention</h4>
              <div style={{ marginBottom: 12 }}>
                <label style={{ fontSize: 13, color: '#94a3b8', display: 'block', marginBottom: 6, fontWeight: 600 }}>
                  Type
                </label>
                <select
                  value={logForm.intervention_type}
                  onChange={e => setLogForm(f => ({ ...f, intervention_type: e.target.value }))}
                  style={{
                    padding: '8px 12px', borderRadius: 8,
                    border: '1px solid #334155', fontSize: 13, minWidth: 200,
                    background: '#0f172a', color: '#f1f5f9',
                  }}>
                  {INTERVENTION_TYPES.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 16 }}>
                <label style={{ fontSize: 13, color: '#94a3b8', display: 'block', marginBottom: 6, fontWeight: 600 }}>
                  Notes
                </label>
                <textarea rows={3}
                  value={logForm.notes}
                  onChange={e => setLogForm(f => ({ ...f, notes: e.target.value }))}
                  placeholder="Describe the intervention..."
                  style={{
                    width: '100%', padding: '8px 12px', borderRadius: 8,
                    border: '1px solid #334155', fontSize: 13, resize: 'vertical',
                    fontFamily: 'inherit', boxSizing: 'border-box',
                    background: '#0f172a', color: '#f1f5f9',
                  }} />
              </div>
              <button onClick={handleLog} disabled={saving}
                style={{
                  padding: '9px 22px',
                  background: saving ? '#ccc' : '#27ae60',
                  color: '#fff', border: 'none', borderRadius: 8,
                  fontSize: 13, fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}>
                {saving ? 'Saving...' : '✓ Save'}
              </button>
            </div>
          )}

          <h3 style={{ color: '#f1f5f9', margin: '0 0 12px', fontSize: 15 }}>
            Intervention History
            <span style={{ color: '#64748b', fontWeight: 400, fontSize: 13, marginLeft: 8 }}>
              ({profile.intervention_summary?.open || 0} open,{' '}
              {profile.intervention_summary?.resolved || 0} resolved)
            </span>
          </h3>

          {profile.interventions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#64748b', fontSize: 14 }}>
              No interventions logged yet.
            </div>
          ) : (
            profile.interventions.map(item => {
              const tc = TYPE_COLORS[item.intervention_type] || TYPE_COLORS['Other'];
              return (
                <div key={item.id} style={{
                  background: '#1e293b', border: '1px solid #334155',
                  borderRadius: 12, padding: 16, marginBottom: 12,
                }}>
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
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
                    <span style={{ fontSize: 12, color: '#64748b' }}>
                      {item.created_at
                        ? new Date(item.created_at).toLocaleDateString('en-IN', {
                            day: '2-digit', month: 'short', year: 'numeric',
                          })
                        : '—'}
                    </span>
                  </div>
                  <p style={{ margin: '10px 0 0', fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>
                    {item.notes}
                  </p>
                  {item.outcome && (
                    <div style={{
                      marginTop: 10, padding: '8px 12px',
                      background: '#0f172a', borderRadius: 8,
                      fontSize: 12, color: '#94a3b8',
                    }}>
                      <strong>Outcome:</strong> {item.outcome}
                      {item.resolved_at && (
                        <span style={{ color: '#64748b', marginLeft: 8 }}>
                          · {new Date(item.resolved_at).toLocaleDateString('en-IN')}
                        </span>
                      )}
                    </div>
                  )}
                  {item.status === 'open' && (
                    resolveId === item.id ? (
                      <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
                        <input
                          value={outcome}
                          onChange={e => setOutcome(e.target.value)}
                          placeholder="Describe outcome..."
                          style={{
                            flex: 1, padding: '7px 10px', borderRadius: 8,
                            border: '1px solid #334155', fontSize: 13,
                            background: '#0f172a', color: '#f1f5f9',
                          }} />
                        <button
                          onClick={() => handleResolve(item.id)}
                          disabled={saving}
                          style={{
                            padding: '7px 14px', background: '#27ae60',
                            color: '#fff', border: 'none', borderRadius: 8,
                            fontSize: 12, cursor: 'pointer',
                          }}>
                          {saving ? '...' : 'Resolve'}
                        </button>
                        <button
                          onClick={() => { setResolveId(null); setOutcome(''); }}
                          style={{
                            padding: '7px 12px', background: '#334155',
                            color: '#94a3b8', border: 'none', borderRadius: 8,
                            fontSize: 12, cursor: 'pointer',
                          }}>
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => { setResolveId(item.id); setOutcome(''); setMsg({ type: '', text: '' }); }}
                        style={{
                          marginTop: 10, padding: '6px 14px',
                          background: '#334155', color: '#94a3b8',
                          border: '1px solid #334155', borderRadius: 8,
                          fontSize: 12, cursor: 'pointer',
                        }}>
                        Mark Resolved
                      </button>
                    )
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
