import React, { useState, useRef, useEffect } from 'react';
import api from '../../services/api';

const GRADE_OPTIONS = ['O','A+','A','B+','B','C','D','F','AB','S*','NS*'];
const GRADE_POINTS  = {O:10,'A+':9,A:8,'B+':7,B:6,C:5,D:4,F:0,AB:0,'S*':0,'NS*':0};
const GRADE_COLORS  = {
  O:'#27ae60','A+':'#2ecc71',A:'#3498db','B+':'#9b59b6',
  B:'#e67e22',C:'#f39c12',D:'#e74c3c',F:'#c0392b',
  AB:'#95a5a6','S*':'#7f8c8d','NS*':'#c0392b'
};

export default function UploadMarksPage() {
  const [phase, setPhase]           = useState('upload');
  const [file, setFile]             = useState(null);
  const [preview, setPreview]       = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving]         = useState(false);
  const [error, setError]           = useState('');
  const [data, setData]             = useState(null);
  const [savedResult, setSavedResult]       = useState(null);
  const [extractionStatus, setExtractionStatus] = useState(null);
  const fileRef = useRef();

  useEffect(() => {
    api.get('/student/extraction-status')
      .then(r => setExtractionStatus(r.data))
      .catch(() => {});
  }, []);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setError('');
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = ev => setPreview(ev.target.result);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleExtract = async () => {
    if (!file) { setError('Please select a file.'); return; }
    setExtracting(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/student/extract-marksheet', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      });
      const extracted = JSON.parse(JSON.stringify(res.data.extracted));
      if (res.data.warning) extracted._warning = res.data.warning;
      setData(extracted);
      setPhase('review');
    } catch (e) {
      setError(e.response?.data?.detail || 'Extraction failed. Check your API key and try again.');
    } finally {
      setExtracting(false);
    }
  };

  const updateField = (field, value) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const updateSubject = (idx, field, value) => {
    setData(prev => {
      const subjects = [...prev.subjects];
      subjects[idx] = { ...subjects[idx], [field]: value };
      if (field === 'grade_letter') {
        const g = value.toUpperCase();
        subjects[idx].grade_points = GRADE_POINTS[g] ?? 0;
        subjects[idx].is_backlog   = ['F','AB','NS','NS*'].includes(g);
      }
      return { ...prev, subjects };
    });
  };

  const addSubject = () => {
    setData(prev => ({
      ...prev,
      subjects: [...prev.subjects, {
        sno: prev.subjects.length + 1,
        subject_code: '',
        subject_name: '',
        grade_letter: 'O',
        grade_points: 10,
        credits: 3,
        is_backlog: false,
        result: 'P'
      }]
    }));
  };

  const removeSubject = (idx) => {
    setData(prev => ({
      ...prev,
      subjects: prev.subjects.filter((_, i) => i !== idx)
                             .map((s, i) => ({ ...s, sno: i + 1 }))
    }));
  };

  const handleConfirm = async () => {
    if (!data.subjects || data.subjects.length === 0) {
      setError('Please add at least one subject before saving.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const res = await api.post('/student/confirm-marksheet', data);
      setSavedResult(res.data);
      setPhase('done');
    } catch (e) {
      setError(e.response?.data?.detail || 'Save failed. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const resetAll = () => {
    setPhase('upload');
    setFile(null);
    setPreview(null);
    setData(null);
    setSavedResult(null);
    setError('');
    if (fileRef.current) fileRef.current.value = '';
  };

  const inp = {
    padding: '7px 10px', border: '1px solid #1e293b', borderRadius: 6,
    fontSize: 13, width: '100%', boxSizing: 'border-box',
    color: '#f1f5f9', background: '#0a0f1e',
  };
  const labelStyle = { fontSize: 12, color: '#64748b', display: 'block', marginBottom: 4, fontWeight: 600 };
  const card = { background: '#111827', borderRadius: 12, border: '1px solid #1e293b', padding: 24, marginBottom: 20 };

  // PHASE 1 — Upload
  if (phase === 'upload') return (
    <div style={{ maxWidth: 680 }}>
      <h2 style={{ color: '#f1f5f9', marginBottom: 4 }}>Upload Marksheet</h2>
      <p style={{ color: '#94a3b8', fontSize: 14, marginBottom: 24 }}>
        Upload your JNTUH grade sheet photo or PDF. Gemini AI will extract all
        grades automatically. You can review and edit before saving.
      </p>

      {extractionStatus && (
        <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>
          {extractionStatus.api_key_configured ? 'AI extraction ready' : 'API key not configured'}
        </div>
      )}

      <div
        style={{ border: '2px dashed #334155', borderRadius: 12, padding: 40,
                 textAlign: 'center', background: '#1e293b',
                 cursor: 'pointer', marginBottom: 16 }}
        onClick={() => fileRef.current?.click()}
      >
        <div style={{ fontSize: 52, marginBottom: 12 }}>{file ? '📄' : '📂'}</div>
        <div style={{ fontWeight: 600, color: '#f1f5f9', fontSize: 15, marginBottom: 6 }}>
          {file ? file.name : 'Click to select grade sheet'}
        </div>
        <div style={{ fontSize: 13, color: '#94a3b8' }}>JPG · PNG · PDF — Max 10MB</div>
        <input ref={fileRef} type="file" accept=".jpg,.jpeg,.png,.pdf"
               onChange={handleFileChange} style={{ display: 'none' }} />
      </div>

      {preview && (
        <div style={{ marginBottom: 16, textAlign: 'center' }}>
          <img src={preview} alt="Preview"
               style={{ maxWidth: '100%', maxHeight: 320, borderRadius: 8,
                        border: '1px solid #d0dce8', objectFit: 'contain' }} />
        </div>
      )}

      {error && (
        <div style={{ background: '#fff0f0', border: '1px solid #f5c6c6', color: '#c0392b',
                      padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
          ❌ {error}
        </div>
      )}

      {file && (
        <button onClick={handleExtract} disabled={extracting} style={{
          width: '100%', padding: 14, background: extracting ? '#7fa8c8' : '#1e3a5f',
          color: '#fff', border: 'none', borderRadius: 8, fontSize: 15,
          fontWeight: 600, cursor: extracting ? 'not-allowed' : 'pointer'
        }}>
          {extracting ? '✨ Gemini is reading your grade sheet...' : '🚀 Extract Grades with AI'}
        </button>
      )}

      {extracting && (
        <p style={{ textAlign:'center', color:'#94a3b8',
                    fontSize:13, marginTop:12 }}>
          ✨ Gemini is reading your grade sheet...
          This takes 5–10 seconds.
        </p>
      )}
    </div>
  );

  // PHASE 2 — Extraction failed (no subjects returned)
  if (phase === 'review' && data && (!data.subjects || data.subjects.length === 0)) return (
    <div style={{ maxWidth: 600, margin: '0 auto', textAlign: 'center', padding: 40 }}>
      <div style={{
        background: '#1e293b',
        border: '1px solid #ef4444',
        borderRadius: 12, padding: 32,
      }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>❌</div>
        <h3 style={{ color: '#f1f5f9', margin: '0 0 12px', fontSize: 18 }}>
          Extraction Failed
        </h3>
        <p style={{ color: '#94a3b8', fontSize: 14, lineHeight: 1.7, marginBottom: 24 }}>
          Could not extract grade data from this file.
          Please make sure you are uploading a clear photo or scan of your JNTUH SNIST grade sheet.
        </p>
        <div style={{
          background: '#0f172a', border: '1px solid #334155',
          borderRadius: 8, padding: '14px 16px',
          marginBottom: 24, textAlign: 'left',
          fontSize: 13, color: '#94a3b8', lineHeight: 1.8,
        }}>
          <div style={{ color: '#f1f5f9', fontWeight: 600, marginBottom: 8 }}>
            Tips for better extraction:
          </div>
          <div>📸 Use a well-lit, straight photo</div>
          <div>🔍 Make sure all text is clearly visible</div>
          <div>📄 PDF from university portal works best</div>
          <div>↕️ Hold phone parallel to the document</div>
          <div>🚫 Avoid shadows and glare</div>
        </div>
        <button
          onClick={() => {
            setPhase('upload');
            setData(null);
            setFile(null);
            setPreview(null);
            if (fileRef.current) fileRef.current.value = '';
          }}
          style={{
            padding: '12px 28px', background: '#3b82f6',
            color: '#fff', border: 'none', borderRadius: 8,
            fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}
        >
          ← Try Again with Different File
        </button>
      </div>
    </div>
  );

  // PHASE 2 — Review & Edit
  if (phase === 'review' && data) return (
    <div style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ color: '#f1f5f9', margin: 0 }}>Review Extracted Data</h2>
          <p style={{ color: '#64748b', fontSize: 13, margin: '4px 0 0' }}>
            Check all fields. Edit anything that looks wrong before saving.
          </p>
        </div>
        <button onClick={resetAll} style={{ padding: '8px 16px', background: 'none',
          border: '1px solid #1e293b', color: '#94a3b8', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
          ← Upload Different File
        </button>
      </div>

      {error && (
        <div style={{ background: '#fff0f0', border: '1px solid #f5c6c6', color: '#c0392b',
                      padding: 12, borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
          ❌ {error}
        </div>
      )}

      <div style={card}>
        <h3 style={{ color: '#f1f5f9', marginTop: 0, marginBottom: 16 }}>📋 Document Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          {[
            ['Hall Ticket No', 'hall_ticket_no'],
            ['Serial No', 'serial_no'],
            ['Memo No', 'memo_no'],
            ['Student Name', 'student_name'],
            ['Branch', 'branch'],
            ['Exam Month/Year', 'exam_month_year'],
          ].map(([lbl, key]) => (
            <div key={key}>
              <span style={labelStyle}>{lbl}</span>
              <input style={inp} value={data[key] || ''}
                     onChange={e => updateField(key, e.target.value)} />
            </div>
          ))}
        </div>
        <div style={{ marginTop: 12 }}>
          <span style={labelStyle}>Examination</span>
          <input style={inp} value={data.examination || ''}
                 onChange={e => updateField('examination', e.target.value)} />
        </div>
      </div>

      <div style={card}>
        <h3 style={{ color: '#f1f5f9', marginTop: 0, marginBottom: 16 }}>📊 Performance Summary</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
          {[
            ['Semester No', 'semester_no', 'number'],
            ['SGPA', 'sgpa', 'number'],
            ['CGPA', 'cgpa', 'number'],
            ['Total Credits (Sem)', 'total_credits_this_semester', 'number'],
          ].map(([lbl, key, type]) => (
            <div key={key}>
              <span style={labelStyle}>{lbl}</span>
              <input style={inp} type={type} value={data[key] ?? ''}
                     onChange={e => updateField(key,
                       type === 'number' ? parseFloat(e.target.value) || e.target.value
                                        : e.target.value)} />
            </div>
          ))}
        </div>
      </div>

      <div style={card}>
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ color: '#f1f5f9', margin: 0 }}>📚 Subjects ({data.subjects?.length || 0})</h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 700 }}>
            <thead>
              <tr style={{ background: '#1e3a5f', color: '#fff' }}>
                {['#','Code','Subject Name','Grade','Pts','Credits','Backlog',''].map(h => (
                  <th key={h} style={{ padding: '10px 8px', textAlign: 'left',
                                       fontSize: 12, whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(data.subjects || []).map((s, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? '#0f172a' : '#111827',
                                     borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '6px 8px', fontSize: 12, color: '#475569' }}>{s.sno}</td>
                  <td style={{ padding: '6px 8px' }}>
                    <input style={{ ...inp, width: 80 }} value={s.subject_code}
                           onChange={e => updateSubject(i, 'subject_code', e.target.value)} />
                  </td>
                  <td style={{ padding: '6px 8px', minWidth: 200 }}>
                    <input style={inp} value={s.subject_name}
                           onChange={e => updateSubject(i, 'subject_name', e.target.value)} />
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <select value={s.grade_letter}
                      onChange={e => updateSubject(i, 'grade_letter', e.target.value)}
                      style={{ ...inp, width: 72,
                               background: GRADE_COLORS[s.grade_letter] || '#555',
                               color: '#fff', fontWeight: 700, cursor: 'pointer' }}>
                      {GRADE_OPTIONS.map(g => <option key={g} value={g}>{g}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '6px 8px', fontWeight: 700, color: '#38bdf8', fontSize: 14 }}>
                    {s.grade_points}
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <input style={{ ...inp, width: 64 }} type="number" step="0.5" min="0" max="6"
                           value={s.credits}
                           onChange={e => updateSubject(i, 'credits', parseFloat(e.target.value) || 0)} />
                  </td>
                  <td style={{ padding: '6px 8px', textAlign: 'center' }}>
                    {s.is_backlog
                      ? <span style={{ color: '#c0392b', fontSize: 12 }}>❌</span>
                      : <span style={{ color: '#27ae60', fontSize: 12 }}>✅</span>}
                  </td>
                  <td style={{ padding: '6px 8px' }}>
                    <button onClick={() => removeSubject(i)}
                      style={{ padding: '3px 8px', background: '#fff0f0',
                               border: '1px solid #f5c6c6', color: '#c0392b',
                               borderRadius: 4, cursor: 'pointer', fontSize: 12 }}>✕</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {data.subjects?.length > 0 && (() => {
          const validSubs = data.subjects.filter(s => s.credits > 0);
          const totalCredits = validSubs.reduce((a, s) => a + s.credits, 0);
          const weightedSum = validSubs.reduce((a, s) => a + s.grade_points * s.credits, 0);
          const calcGPA = totalCredits > 0 ? (weightedSum / totalCredits).toFixed(2) : '—';
          const mismatch = data.sgpa && Math.abs(parseFloat(calcGPA) - data.sgpa) > 0.05;
          return (
            <div style={{ marginTop: 16, padding: '12px 16px',
                          background: 'rgba(56,189,248,0.08)', borderRadius: 8,
                          border: '1px solid #1e293b',
                          display: 'flex', gap: 24, fontSize: 14, flexWrap: 'wrap' }}>
              <span style={{ color: '#f1f5f9' }}>📐 <strong>Calculated SGPA:</strong> {calcGPA}</span>
              <span style={{ color: '#f1f5f9' }}>📦 <strong>Total Credits:</strong> {totalCredits}</span>
              <span style={{ color: mismatch ? '#fb923c' : '#34d399' }}>
                {mismatch
                  ? `⚠️ Extracted SGPA was ${data.sgpa != null ? data.sgpa : 'No GPA in file'} — verify`
                  : `✅ Matches extracted SGPA (${data.sgpa != null ? data.sgpa : 'No GPA in file'})`}
              </span>
            </div>
          );
        })()}
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={handleConfirm} disabled={saving} style={{
          flex: 1, padding: 14, background: saving ? '#7fa8c8' : '#1e6b3a',
          color: '#fff', border: 'none', borderRadius: 8, fontSize: 15,
          fontWeight: 600, cursor: saving ? 'not-allowed' : 'pointer'
        }}>
          {saving ? '💾 Saving...' : '✅ Confirm & Save to My Records'}
        </button>
      </div>
    </div>
  );

  // PHASE 3 — Done
  if (phase === 'done') return (
    <div style={{ maxWidth: 600, textAlign: 'center', padding: 40 }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>🎉</div>
      <h2 style={{ color: '#f1f5f9', marginBottom: 8 }}>
        Semester {savedResult?.semester_no} Saved!
      </h2>
      <p style={{ color: '#64748b', fontSize: 15, marginBottom: 32 }}>
        {savedResult?.subjects_saved} subjects saved to your academic record.
      </p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button onClick={resetAll} style={{
          padding: '12px 24px', background: '#1e3a5f', color: '#fff',
          border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14, fontWeight: 600
        }}>+ Upload Another Semester</button>
      </div>
    </div>
  );

  return null;
}
