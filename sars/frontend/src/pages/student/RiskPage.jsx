import React, { useEffect, useState } from 'react';
import api from '../../services/api';

const RISK_CONFIG = {
  LOW:      { color: '#27ae60', bg: '#f0fff4', border: '#9ae6b4',
               icon: '🟢', label: 'LOW RISK' },
  WATCH:    { color: '#d69e2e', bg: '#fffff0', border: '#f6e05e',
               icon: '🟡', label: 'WATCH' },
  MODERATE: { color: '#dd6b20', bg: '#fff5f0', border: '#fbd38d',
               icon: '🟠', label: 'MODERATE RISK' },
  HIGH:     { color: '#c0392b', bg: '#fff0f0', border: '#f5c6c6',
               icon: '🔴', label: 'HIGH RISK' },
};

export default function RiskPage() {
  const [risk, setRisk]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [computing, setComputing] = useState(false);
  const [error, setError]         = useState('');

  const fetchRisk = () => {
    setLoading(true);
    api.get('/student/risk-score')
      .then(r => setRisk(r.data))
      .catch(() => setError('Failed to load risk score.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRisk(); }, []);

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
    <div style={{ textAlign: 'center', padding: 60, color: '#666' }}>
      Loading your risk score...
    </div>
  );

  // -- Not computed yet ------------------------------------------------------
  if (!risk?.computed) return (
    <div style={{ maxWidth: 600 }}>
      <h2 style={{ color: '#1e3a5f', marginBottom: 8 }}>
        SARS Risk Score
      </h2>
      <div style={{ background: '#fff8e0', border: '1px solid #f6e05e',
                    borderRadius: 12, padding: 32, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
        <h3 style={{ color: '#1e3a5f', margin: '0 0 8px' }}>
          No Risk Score Yet
        </h3>
        <p style={{ color: '#666', fontSize: 14, marginBottom: 24 }}>
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

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 24 }}>
        <h2 style={{ color: '#1e3a5f', margin: 0 }}>SARS Risk Score</h2>
        <button onClick={handleCompute} disabled={computing}
          style={{ padding: '8px 18px', background: '#1e3a5f',
                   color: '#fff', border: 'none', borderRadius: 6,
                   fontSize: 13, cursor: computing ? 'not-allowed' : 'pointer' }}>
          {computing ? '⏳ Recalculating...' : '🔄 Recalculate'}
        </button>
      </div>

      {/* -- Main Score Card ------------------------------------------------- */}
      <div style={{ background: cfg.bg, border: `2px solid ${cfg.border}`,
                    borderRadius: 16, padding: 32, marginBottom: 20,
                    textAlign: 'center' }}>
        <div style={{ fontSize: 52 }}>{cfg.icon}</div>
        <div style={{ fontSize: 72, fontWeight: 900,
                      color: cfg.color, lineHeight: 1 }}>
          {risk.sars_score?.toFixed(1)}
        </div>
        <div style={{ fontSize: 13, color: '#888', margin: '4px 0 12px' }}>
          out of 100
        </div>
        <div style={{ display: 'inline-block', background: cfg.color,
                      color: '#fff', padding: '6px 20px', borderRadius: 20,
                      fontWeight: 700, fontSize: 16, letterSpacing: 1 }}>
          {cfg.label}
        </div>
        <div style={{ marginTop: 16, fontSize: 13, color: '#666' }}>
          Confidence: {((risk.confidence || 0) * 100).toFixed(0)}%
          &nbsp;·&nbsp;
          Last computed: {risk.computed_at
            ? new Date(risk.computed_at).toLocaleString()
            : 'N/A'}
        </div>
      </div>

      {/* -- Factor Breakdown ------------------------------------------------ */}
      <div style={{ background: '#fff', border: '1px solid #e0e8f0',
                    borderRadius: 12, padding: 24, marginBottom: 20 }}>
        <h3 style={{ color: '#1e3a5f', margin: '0 0 20px' }}>
          📊 Score Breakdown
        </h3>

        {[
          {
            label: 'GPA Trend',
            weight: '40%',
            score: fb.gpa_risk,
            contribution: fb.gpa_component,
            detail: `CGPA: ${fb.cgpa ?? '—'} · Trend: ${
              fb.trend_direction ?? 'N/A'
            }${fb.trend_bonus !== 0
              ? ` (${fb.trend_bonus > 0 ? '+' : ''}${fb.trend_bonus} pts)`
              : ''}`,
            color: '#3498db',
          },
          {
            label: 'Backlog Count',
            weight: '35%',
            score: fb.backlog_risk,
            contribution: fb.backlog_component,
            detail: `Total backlogs: ${fb.total_backlogs ?? 0}`,
            color: '#e67e22',
          },
          {
            label: 'Attendance',
            weight: '25%',
            score: fb.attendance_risk,
            contribution: fb.attendance_component,
            detail: fb.avg_attendance != null
              ? `Avg attendance: ${fb.avg_attendance?.toFixed(1)}%`
              : 'No attendance data (neutral penalty applied)',
            color: '#9b59b6',
          },
        ].map(f => (
          <div key={f.label} style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between',
                          alignItems: 'center', marginBottom: 6 }}>
              <div>
                <span style={{ fontWeight: 600, color: '#1e3a5f',
                               fontSize: 14 }}>
                  {f.label}
                </span>
                <span style={{ color: '#888', fontSize: 12,
                               marginLeft: 8 }}>
                  (weight {f.weight})
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontWeight: 700, color: f.color,
                               fontSize: 15 }}>
                  {f.score?.toFixed(1) ?? '—'}/100
                </span>
                <span style={{ color: '#888', fontSize: 12,
                               marginLeft: 8 }}>
                  → {f.contribution?.toFixed(2) ?? '—'} pts
                </span>
              </div>
            </div>
            {/* Progress bar */}
            <div style={{ height: 10, background: '#f0f4f8',
                          borderRadius: 5, overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 5,
                background: f.color,
                width: `${Math.min(100, f.score ?? 0)}%`,
                transition: 'width 0.6s ease',
              }} />
            </div>
            <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>
              {f.detail}
            </div>
          </div>
        ))}
      </div>

      {/* -- Advisory Text --------------------------------------------------- */}
      {risk.advisory_text && (
        <div style={{ background: '#f8fafd', border: '1px solid #e0e8f0',
                      borderRadius: 12, padding: 20, marginBottom: 20 }}>
          <h3 style={{ color: '#1e3a5f', margin: '0 0 12px' }}>
            💡 Advisory
          </h3>
          <p style={{ color: '#444', fontSize: 14,
                      lineHeight: 1.7, margin: 0 }}>
            {risk.advisory_text}
          </p>
        </div>
      )}

      {/* -- Semesters analyzed ---------------------------------------------- */}
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
