import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const RISK_CONFIG = {
  LOW:      { color: '#34d399', bg: 'rgba(52,211,153,0.08)',  border: 'rgba(52,211,153,0.3)',
               icon: '🟢', label: 'LOW RISK' },
  WATCH:    { color: '#fbbf24', bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.3)',
               icon: '🟡', label: 'WATCH' },
  MODERATE: { color: '#fb923c', bg: 'rgba(251,146,60,0.08)',  border: 'rgba(251,146,60,0.3)',
               icon: '🟠', label: 'MODERATE RISK' },
  HIGH:     { color: '#f87171', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.3)',
               icon: '🔴', label: 'HIGH RISK' },
};

const getRiskEmoji = (level) => {
  const map = { LOW: '😊', WATCH: '😐', MODERATE: '😟', HIGH: '😰' };
  return map[level] || '😐';
};

const getGpaEmoji = (cgpa) => {
  if (!cgpa && cgpa !== 0) return '❓';
  if (cgpa >= 8.5) return '🌟';
  if (cgpa >= 7.5) return '😊';
  if (cgpa >= 7.0) return '😐';
  if (cgpa >= 6.0) return '😟';
  return '😰';
};

const getBacklogEmoji = (count) => {
  if (count === 0) return '✅';
  if (count === 1) return '⚠️';
  if (count === 2) return '😟';
  return '🚨';
};

const getAttendanceEmoji = (avgAttendance) => {
  if (avgAttendance === null || avgAttendance === undefined) return '📭';
  if (avgAttendance >= 90) return '🟢';
  if (avgAttendance >= 75) return '🟢';
  if (avgAttendance >= 60) return '🟡';
  return '🔴';
};

function FactorBar({ label, emoji, sublabel, score, color, tags, onToggleRange, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <div>
          <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 13, display: 'flex', alignItems: 'center' }}>
            {label}
            {emoji && <span style={{ fontSize: 15, marginLeft: 6 }}>{emoji}</span>}
            {onToggleRange && (
              <button
                onClick={onToggleRange}
                title="See what affects this score"
                style={{
                  background: 'none', border: '1px solid #334155',
                  color: '#64748b', borderRadius: '50%',
                  width: 16, height: 16, fontSize: 9, fontWeight: 700,
                  cursor: 'pointer', marginLeft: 6, padding: 0,
                  lineHeight: '14px', textAlign: 'center',
                  display: 'inline-flex', alignItems: 'center',
                  justifyContent: 'center', flexShrink: 0,
                }}
              >
                ?
              </button>
            )}
          </div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 1 }}>
            {sublabel}
          </div>
        </div>
        <div style={{ fontWeight: 700, color, fontSize: 14, alignSelf: 'center' }}>
          {score?.toFixed(1)}/100
        </div>
      </div>
      <div style={{ height: 8, background: '#1e293b', borderRadius: 4,
                    overflow: 'hidden', marginBottom: tags?.length ? 6 : 0 }}>
        <div style={{
          height: '100%', borderRadius: 4, background: color,
          width: `${Math.min(100, score || 0)}%`,
          transition: 'width 0.6s ease',
        }} />
      </div>
      {tags && tags.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
          {tags.map((t, i) => (
            <span key={i} style={{
              background: '#450a0a', color: '#fca5a5',
              fontSize: 10, fontWeight: 600,
              padding: '2px 8px', borderRadius: 10,
              border: '1px solid #7f1d1d',
            }}>
              {t}
            </span>
          ))}
        </div>
      )}
      {children}
    </div>
  );
}

function SgpaTrendChart({ semestersData }) {
  if (!semestersData || semestersData.length === 0) return null;

  const sgpaMap = {};
  semestersData.forEach(s => { sgpaMap[s.semester_no] = s.gpa; });

  const ALL_SEMS = [1, 2, 3, 4, 5, 6, 7, 8];
  const MAX_SGPA = 10;
  const BAR_HEIGHT = 120;
  const BAR_WIDTH  = 36;
  const BAR_GAP    = 12;
  const CHART_H    = BAR_HEIGHT + 48;

  const getBarColor = (sgpa) => {
    if (sgpa >= 8.5) return '#22c55e';
    if (sgpa >= 7.5) return '#3b82f6';
    if (sgpa >= 6.5) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div style={{
      background: '#1e293b', border: '1px solid #334155',
      borderRadius: 12, padding: 20, marginBottom: 20,
    }}>
      <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15, fontWeight: 700 }}>
        📊 SGPA Trend by Semester
      </h3>

      <div style={{ position: 'relative', height: CHART_H, width: '100%', overflowX: 'auto' }}>
        <div style={{
          display: 'flex', alignItems: 'flex-end',
          gap: BAR_GAP, height: CHART_H,
          paddingBottom: 0,
          minWidth: ALL_SEMS.length * (BAR_WIDTH + BAR_GAP),
        }}>
          {ALL_SEMS.map(semNo => {
            const sgpa = sgpaMap[semNo];
            const hasData = sgpa !== undefined && sgpa !== null;
            const barH = hasData
              ? Math.max(Math.round((sgpa / MAX_SGPA) * BAR_HEIGHT), 24)
              : 0;
            const color = hasData ? getBarColor(sgpa) : 'transparent';

            return (
              <div key={semNo} style={{
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', width: BAR_WIDTH,
                flexShrink: 0,
              }}>
                {hasData ? (
                  <div style={{
                    width: BAR_WIDTH, height: barH,
                    background: color, borderRadius: '4px 4px 0 0',
                    transition: 'height 0.5s ease',
                    display: 'flex', alignItems: 'flex-start',
                    justifyContent: 'center', paddingTop: 4,
                  }}>
                    <span style={{
                      fontSize: 10, fontWeight: 700, color: '#fff',
                      textShadow: '0 1px 2px rgba(0,0,0,0.5)',
                      lineHeight: 1, whiteSpace: 'nowrap',
                    }}>
                      {parseFloat(sgpa).toFixed(2)}
                    </span>
                  </div>
                ) : (
                  <div style={{
                    width: BAR_WIDTH, height: BAR_HEIGHT * 0.12,
                    border: '2px dashed #334155', borderBottom: 'none',
                    borderRadius: '4px 4px 0 0',
                    display: 'flex', alignItems: 'flex-start',
                    justifyContent: 'center', paddingTop: 3,
                  }}>
                    <span style={{ fontSize: 9, color: '#475569', fontWeight: 400 }}>—</span>
                  </div>
                )}

                <div style={{
                  fontSize: 11, marginTop: 6, height: 16, lineHeight: '16px',
                  color: hasData ? '#94a3b8' : '#475569',
                  fontWeight: hasData ? 600 : 400,
                  textAlign: 'center',
                }}>
                  S{semNo}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{
          position: 'absolute', bottom: 22, left: 0, right: 0,
          height: 1, background: '#334155',
        }} />
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 8 }}>
        {[
          { color: '#22c55e', label: '≥ 8.5 Excellent' },
          { color: '#3b82f6', label: '7.5–8.49 Good' },
          { color: '#f59e0b', label: '6.5–7.49 Average' },
          { color: '#ef4444', label: '< 6.5 At Risk' },
        ].map(l => (
          <div key={l.label} style={{
            display: 'flex', alignItems: 'center',
            gap: 5, fontSize: 11, color: '#94a3b8',
          }}>
            <div style={{ width: 10, height: 10, borderRadius: 2,
                          background: l.color, flexShrink: 0 }} />
            {l.label}
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 5,
                      fontSize: 11, color: '#475569' }}>
          <div style={{ width: 10, height: 10, borderRadius: 2,
                        border: '2px dashed #334155' }} />
          Not uploaded yet
        </div>
      </div>
    </div>
  );
}

export default function RiskPage() {
  const [risk, setRisk]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [computing, setComputing]     = useState(false);
  const [error, setError]             = useState('');
  const [semestersData, setSemestersData] = useState([]);
  const [showRange, setShowRange] = useState({ gpa: false, backlog: false, attendance: false });

  const toggleRange = (key) => setShowRange(prev => ({ ...prev, [key]: !prev[key] }));

  const fetchRisk = () => {
    setLoading(true);
    api.get('/student/risk-score')
      .then(r => setRisk(r.data))
      .catch(() => setError('Failed to load risk score.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRisk(); }, []);

  useEffect(() => {
    api.get('/student/semesters')
      .then(r => setSemestersData(r.data || []))
      .catch(() => setSemestersData([]));
  }, []);

  const handleCompute = async () => {
    setComputing(true);
    setError('');
    try {
      await api.post('/student/compute-risk');
      fetchRisk();
    } catch (e) {
      setError('Could not compute risk score. Upload a marksheet first.');
    } finally {
      setComputing(false);
    }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
      Loading your risk score...
    </div>
  );

  // -- Not computed yet -------------------------------------------------------
  if (!risk?.computed) return (
    <div style={{ maxWidth: 600 }}>
      <h2 style={{ color: '#f1f5f9', marginBottom: 8 }}>SARS Risk Score</h2>
      <div style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.3)',
                    borderRadius: 12, padding: 32, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
        <h3 style={{ color: '#f1f5f9', margin: '0 0 8px' }}>No Risk Score Yet</h3>
        <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>
          Upload at least one semester marksheet to compute your SARS score.
        </p>
        <button onClick={handleCompute} disabled={computing}
          style={{ padding: '12px 28px', background: '#1e3a5f',
                   color: '#fff', border: 'none', borderRadius: 8,
                   fontSize: 15, fontWeight: 600,
                   cursor: computing ? 'not-allowed' : 'pointer' }}>
          {computing ? '⏳ Computing...' : '🔄 Compute Risk Score'}
        </button>
      </div>
      {error && (
        <div style={{ color: '#c0392b', fontSize: 13,
                      marginTop: 12, textAlign: 'center' }}>
          {error}
        </div>
      )}
    </div>
  );

  // -- Risk computed ----------------------------------------------------------
  const cfg = RISK_CONFIG[risk.risk_level] || RISK_CONFIG.WATCH;
  const fb  = risk.factor_breakdown || {};

  const backlogTags = [];
  semestersData.forEach(sem => {
    (sem.subjects || []).forEach(s => {
      if (s.is_backlog) {
        backlogTags.push(`${s.subject_name} (Sem ${sem.semester_no})`);
      }
    });
  });

  const backlogSublabel = fb.total_backlogs === 0
    ? 'No backlogs ✅'
    : fb.total_backlogs === 1
      ? '1 backlog subject'
      : `${fb.total_backlogs} backlog subjects`;

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ color: '#f1f5f9', margin: 0 }}>SARS Risk Score</h2>
        <button onClick={handleCompute} disabled={computing}
          style={{ padding: '8px 18px', background: '#1e3a5f',
                   color: '#fff', border: 'none', borderRadius: 6,
                   fontSize: 13, cursor: computing ? 'not-allowed' : 'pointer' }}>
          {computing ? '⏳ Recalculating...' : '🔄 Recalculate'}
        </button>
      </div>

      {/* -- Main Score Card (two-box layout) ----------------------------------- */}
      <div style={{
        background: cfg.bg, border: `2px solid ${cfg.color}`,
        borderRadius: 16, padding: 24, marginBottom: 20,
        display: 'flex', gap: 20, alignItems: 'stretch', flexWrap: 'wrap',
      }}>

        {/* LEFT BOX — score */}
        <div style={{
          flex: '0 0 200px', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', textAlign: 'center',
          background: 'rgba(0,0,0,0.15)', borderRadius: 12,
          padding: '24px 16px', minWidth: 160,
        }}>
          <div style={{ fontSize: 44 }}>{cfg.icon}</div>
          <div style={{ fontSize: 64, fontWeight: 900, color: cfg.color,
                        lineHeight: 1, marginTop: 8 }}>
            {risk.sars_score?.toFixed(1)}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8', margin: '4px 0 12px' }}>
            out of 100
          </div>
          <div style={{
            background: cfg.color, color: '#fff',
            padding: '6px 18px', borderRadius: 20,
            fontWeight: 700, fontSize: 14, letterSpacing: 1,
          }}>
            {cfg.label}
          </div>
          <div style={{ marginTop: 14, fontSize: 12, color: '#64748b', lineHeight: 1.8 }}>
            <div>Confidence: {((risk.confidence || 0) * 100).toFixed(0)}%</div>
            <div>{risk.computed_at
              ? new Date(risk.computed_at).toLocaleString()
              : 'N/A'}</div>
          </div>
        </div>

        {/* RIGHT BOX — factors (GPA + Backlog only) */}
        <div style={{
          flex: 1, background: 'rgba(0,0,0,0.15)',
          borderRadius: 12, padding: '20px 20px', minWidth: 240,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ fontWeight: 700, color: '#f1f5f9', fontSize: 14 }}>
              📋 What's Causing This Risk
            </div>
            <span style={{ fontSize: 22 }}>{getRiskEmoji(risk.risk_level)}</span>
          </div>

          <FactorBar
            label="GPA Risk"
            emoji={getGpaEmoji(fb.cgpa)}
            sublabel={`CGPA: ${fb.cgpa ?? '—'}`}
            score={fb.gpa_risk}
            color={cfg.color}
            onToggleRange={() => toggleRange('gpa')}
          >
            {showRange.gpa && (
              <div style={{ background: '#0f172a', border: '1px solid #334155',
                            borderRadius: 8, padding: '10px 12px',
                            marginTop: 8, marginBottom: 4, fontSize: 11 }}>
                <div style={{ color: '#94a3b8', fontWeight: 600,
                              marginBottom: 6, fontSize: 11 }}>
                  📊 What CGPA causes what risk:
                </div>
                {[
                  { dot: '🟢', range: 'CGPA ≥ 8.5',
                    label: 'Excellent — well above placement cutoff',
                    active: fb.cgpa >= 8.5 },
                  { dot: '🟢', range: 'CGPA 7.5 – 8.49',
                    label: 'Good — placement eligible',
                    active: fb.cgpa >= 7.5 && fb.cgpa < 8.5 },
                  { dot: '🟡', range: 'CGPA 7.0 – 7.49',
                    label: 'Borderline — below 7.5 SNIST cutoff',
                    active: fb.cgpa >= 7.0 && fb.cgpa < 7.5 },
                  { dot: '🟠', range: 'CGPA 6.0 – 6.99',
                    label: 'Needs improvement urgently',
                    active: fb.cgpa >= 6.0 && fb.cgpa < 7.0 },
                  { dot: '🔴', range: 'CGPA < 6.0',
                    label: 'Critical — academic probation risk',
                    active: fb.cgpa < 6.0 },
                ].map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 6,
                    padding: '3px 6px', borderRadius: 5, marginBottom: 2,
                    background: r.active ? 'rgba(59,130,246,0.12)' : 'transparent',
                    border: r.active ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                  }}>
                    <span style={{ fontSize: 11, flexShrink: 0 }}>{r.dot}</span>
                    <div>
                      <span style={{ fontWeight: r.active ? 700 : 400,
                                     color: r.active ? '#93c5fd' : '#64748b' }}>
                        {r.range}
                      </span>
                      <span style={{ color: '#475569', marginLeft: 4 }}>— {r.label}</span>
                      {r.active && (
                        <span style={{ marginLeft: 6, fontSize: 10,
                                       color: '#93c5fd', fontWeight: 700 }}>
                          ← You are here
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </FactorBar>

          <FactorBar
            label="Backlog Risk"
            emoji={getBacklogEmoji(fb.total_backlogs || 0)}
            sublabel={backlogSublabel}
            score={fb.backlog_risk}
            color="#e67e22"
            tags={backlogTags}
            onToggleRange={() => toggleRange('backlog')}
          >
            {showRange.backlog && (
              <div style={{ background: '#0f172a', border: '1px solid #334155',
                            borderRadius: 8, padding: '10px 12px',
                            marginTop: 8, marginBottom: 4, fontSize: 11 }}>
                <div style={{ color: '#94a3b8', fontWeight: 600,
                              marginBottom: 6, fontSize: 11 }}>
                  📊 What backlogs cause what risk:
                </div>
                {[
                  { dot: '🟢', range: '0 backlogs',
                    label: 'Clean record — placement eligible',
                    active: (fb.total_backlogs || 0) === 0 },
                  { dot: '🟠', range: '1 – 2 backlogs',
                    label: 'Not eligible for placements',
                    active: (fb.total_backlogs || 0) >= 1 && (fb.total_backlogs || 0) <= 2 },
                  { dot: '🔴', range: '3+ backlogs',
                    label: 'Critical — completely ineligible',
                    active: (fb.total_backlogs || 0) >= 3 },
                ].map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 6,
                    padding: '3px 6px', borderRadius: 5, marginBottom: 2,
                    background: r.active ? 'rgba(59,130,246,0.12)' : 'transparent',
                    border: r.active ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                  }}>
                    <span style={{ fontSize: 11, flexShrink: 0 }}>{r.dot}</span>
                    <div>
                      <span style={{ fontWeight: r.active ? 700 : 400,
                                     color: r.active ? '#93c5fd' : '#64748b' }}>
                        {r.range}
                      </span>
                      <span style={{ color: '#475569', marginLeft: 4 }}>— {r.label}</span>
                      {r.active && (
                        <span style={{ marginLeft: 6, fontSize: 10,
                                       color: '#93c5fd', fontWeight: 700 }}>
                          ← You are here
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </FactorBar>

          <FactorBar
            label="Attendance Risk"
            emoji={getAttendanceEmoji(fb.avg_attendance)}
            sublabel={`Average attendance: ${fb.avg_attendance ?? 'No data'}${fb.avg_attendance !== null && fb.avg_attendance !== undefined ? '%' : ''}`}
            score={fb.attendance_risk}
            color="#a855f7"
            onToggleRange={() => toggleRange('attendance')}
          >
            {showRange.attendance && (
              <div style={{ background: '#0f172a', border: '1px solid #334155',
                            borderRadius: 8, padding: '10px 12px',
                            marginTop: 8, marginBottom: 4, fontSize: 11 }}>
                <div style={{ color: '#94a3b8', fontWeight: 600,
                              marginBottom: 6, fontSize: 11 }}>
                  📊 What attendance causes what risk:
                </div>
                {[
                  { dot: '🟢', range: '>= 90%',
                    label: 'Excellent attendance',
                    active: fb.avg_attendance !== null && fb.avg_attendance !== undefined && fb.avg_attendance >= 90 },
                  { dot: '🟢', range: '75-89%',
                    label: 'Above 75% minimum requirement',
                    active: fb.avg_attendance !== null && fb.avg_attendance !== undefined && fb.avg_attendance >= 75 && fb.avg_attendance < 90 },
                  { dot: '🟡', range: '60-74%',
                    label: 'Below 75% - exam eligibility at risk',
                    active: fb.avg_attendance !== null && fb.avg_attendance !== undefined && fb.avg_attendance >= 60 && fb.avg_attendance < 75 },
                  { dot: '🔴', range: '< 60%',
                    label: 'Critical - may lose exam eligibility',
                    active: fb.avg_attendance !== null && fb.avg_attendance !== undefined && fb.avg_attendance < 60 },
                  { dot: '📭', range: 'No data',
                    label: 'Upload attendance for accurate scoring',
                    active: fb.avg_attendance === null || fb.avg_attendance === undefined },
                ].map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 6,
                    padding: '3px 6px', borderRadius: 5, marginBottom: 2,
                    background: r.active ? 'rgba(59,130,246,0.12)' : 'transparent',
                    border: r.active ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                  }}>
                    <span style={{ fontSize: 11, flexShrink: 0 }}>{r.dot}</span>
                    <div>
                      <span style={{ fontWeight: r.active ? 700 : 400,
                                     color: r.active ? '#93c5fd' : '#64748b' }}>
                        {r.range}
                      </span>
                      <span style={{ color: '#475569', marginLeft: 4 }}>- {r.label}</span>
                      {r.active && (
                        <span style={{ marginLeft: 6, fontSize: 10,
                                       color: '#93c5fd', fontWeight: 700 }}>
                          ← You are here
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </FactorBar>
        </div>
      </div>

      <SgpaTrendChart semestersData={semestersData} />

      {/* -- Advisory Text ----------------------------------------------------- */}
      {risk.advisory_text && (
        <div style={{ background: '#111827', border: '1px solid #1e293b',
                      borderRadius: 12, padding: 20, marginBottom: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 12px' }}>💡 Advisory</h3>
          <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
            {risk.advisory_text}
          </p>
        </div>
      )}

      {/* -- Semesters analyzed ------------------------------------------------ */}
      <div style={{ fontSize: 12, color: '#aaa', textAlign: 'center' }}>
        Based on {fb.semesters_analyzed ?? 0} semester
        {(fb.semesters_analyzed ?? 0) !== 1 ? 's' : ''} of data.
        Upload more marksheets for higher accuracy.
      </div>

      {error && (
        <div style={{ color: '#c0392b', fontSize: 13,
                      marginTop: 12, textAlign: 'center' }}>
          {error}
        </div>
      )}
    </div>
  );
}
