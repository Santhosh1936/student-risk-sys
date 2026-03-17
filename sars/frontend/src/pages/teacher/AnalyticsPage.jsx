// frontend/src/pages/teacher/AnalyticsPage.jsx
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const RISK_COLORS = {
  HIGH: '#c0392b', MODERATE: '#dd6b20',
  WATCH: '#d69e2e', LOW: '#27ae60',
  'NOT COMPUTED': '#aaa',
};
const BAR_COLORS = [
  '#3498db', '#e67e22', '#9b59b6',
  '#27ae60', '#c0392b', '#1abc9c',
];

function HBar({ label, value, max, color, suffix }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
        <span style={{ color: '#f1f5f9', fontWeight: 500 }}>{label}</span>
        <span style={{ color: '#94a3b8', fontWeight: 600 }}>
          {value}{suffix || ''}
        </span>
      </div>
      <div style={{ height: 11, background: '#1e293b', borderRadius: 6, overflow: 'hidden' }}>
        <div style={{
          height: '100%', borderRadius: 6,
          background: color, width: `${pct}%`,
          transition: 'width 0.5s ease',
        }} />
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  useEffect(() => {
    api.get('/teacher/analytics')
      .then(r => setData(r.data))
      .catch(() => setError('Could not load analytics data. Please try again.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
      Loading analytics...
    </div>
  );
  if (error) return (
    <div style={{
      background: 'rgba(248,113,113,0.08)', border: '1px solid #f87171',
      borderRadius: 10, padding: '14px 18px', color: '#f87171', fontSize: 13,
    }}>
      {error}
    </div>
  );
  if (!data || data.total_students === 0) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
      No student data available yet.
    </div>
  );

  const maxCgpa = Math.max(...Object.values(data.cgpa_distribution), 1);
  const maxRisk = Math.max(...Object.values(data.risk_breakdown), 1);
  const maxBlog = data.top_backlog_subjects[0]?.count || 1;
  const maxSgpa = Math.max(...data.semester_trend.map(s => s.avg_sgpa), 10);

  return (
    <div style={{ maxWidth: 920 }}>
      <h2 style={{ color: '#f1f5f9', margin: '0 0 4px' }}>
        📊 Analytics Dashboard
      </h2>
      <p style={{ color: '#94a3b8', fontSize: 13, marginBottom: 24 }}>
        Class-wide academic performance overview
      </p>

      {/* Summary row */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
        {[
          { label: 'Total Students',     value: data.total_students,                  bg: '#1e293b', color: '#f1f5f9'  },
          { label: 'HIGH Risk',          value: data.risk_breakdown.HIGH || 0,        bg: '#fff0f0', color: '#c0392b'  },
          { label: 'MODERATE',           value: data.risk_breakdown.MODERATE || 0,    bg: '#fff5f0', color: '#dd6b20'  },
          { label: 'WATCH',              value: data.risk_breakdown.WATCH || 0,       bg: '#fffff0', color: '#d69e2e'  },
          { label: 'LOW Risk',           value: data.risk_breakdown.LOW || 0,         bg: '#f0fff4', color: '#27ae60'  },
          { label: 'Open Interventions', value: data.intervention_summary?.open || 0, bg: '#1e293b', color: '#f1f5f9'  },
        ].map(c => (
          <div key={c.label} style={{
            background: c.bg, border: '1px solid #334155',
            borderRadius: 10, padding: '14px 18px',
            textAlign: 'center', minWidth: 110, flex: 1,
          }}>
            <div style={{ fontSize: 26, fontWeight: 900, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{c.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* CGPA Distribution */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            CGPA Distribution
          </h3>
          {Object.entries(data.cgpa_distribution).map(([range, count], i) => (
            <HBar key={range} label={range} value={count} max={maxCgpa}
              color={BAR_COLORS[i % 6]} suffix=" students" />
          ))}
        </div>

        {/* Risk Breakdown */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Risk Level Breakdown
          </h3>
          {Object.entries(data.risk_breakdown).map(([level, count]) => (
            <HBar key={level} label={level} value={count} max={maxRisk}
              color={RISK_COLORS[level] || '#aaa'} suffix=" students" />
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Backlog Subjects */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Top Subjects With Backlogs
          </h3>
          {data.top_backlog_subjects.length === 0 ? (
            <p style={{ color: '#27ae60', fontSize: 14 }}>
              🎉 No backlogs across all students!
            </p>
          ) : (
            data.top_backlog_subjects.map((s, i) => (
              <HBar key={s.subject} label={s.subject} value={s.count}
                max={maxBlog} color={BAR_COLORS[i % 6]} suffix=" students" />
            ))
          )}
        </div>

        {/* SGPA Trend */}
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Class Avg SGPA by Semester
          </h3>
          {data.semester_trend.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: 14 }}>No semester data yet.</p>
          ) : (
            data.semester_trend.map((s, i) => (
              <HBar key={s.semester_no}
                label={`Semester ${s.semester_no} (${s.student_count} students)`}
                value={s.avg_sgpa} max={maxSgpa}
                color={BAR_COLORS[i % 6]} />
            ))
          )}
        </div>
      </div>

      {/* Attendance + Interventions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Attendance Status
          </h3>
          {[
            { label: 'Above 75% ✅', value: data.attendance_summary.above_75, color: '#27ae60' },
            { label: 'Below 75% ⚠️', value: data.attendance_summary.below_75, color: '#c0392b' },
            { label: 'Not uploaded', value: data.attendance_summary.no_data,  color: '#aaa'    },
          ].map(a => {
            const max = Math.max(
              data.attendance_summary.above_75,
              data.attendance_summary.below_75,
              data.attendance_summary.no_data,
              1,
            );
            return (
              <HBar key={a.label} label={a.label} value={a.value}
                max={max} color={a.color} suffix=" students" />
            );
          })}
        </div>

        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Interventions by Type
          </h3>
          {Object.keys(data.intervention_summary?.by_type || {}).length === 0 ? (
            <p style={{ color: '#64748b', fontSize: 14 }}>No interventions logged yet.</p>
          ) : (
            Object.entries(data.intervention_summary.by_type).map(([type, count], i) => (
              <HBar key={type} label={type} value={count}
                max={Math.max(...Object.values(data.intervention_summary.by_type), 1)}
                color={BAR_COLORS[i % 6]} suffix=" logged" />
            ))
          )}
        </div>
      </div>

      {/* Branch CGPA */}
      {data.branch_cgpa.length > 0 && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: '#f1f5f9', margin: '0 0 16px', fontSize: 15 }}>
            Branch-Wise Average CGPA
          </h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {data.branch_cgpa.map((b, i) => (
              <div key={b.branch} style={{
                background: '#0f172a', border: '1px solid #334155',
                borderRadius: 10, padding: '14px 20px',
                textAlign: 'center', minWidth: 140,
              }}>
                <div style={{ fontSize: 24, fontWeight: 900, color: BAR_COLORS[i % 6] }}>
                  {b.avg_cgpa.toFixed(2)}
                </div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#f1f5f9', marginTop: 4 }}>
                  {b.branch}
                </div>
                <div style={{ fontSize: 11, color: '#64748b' }}>
                  {b.student_count} student{b.student_count !== 1 ? 's' : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
