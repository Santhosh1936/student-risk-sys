// frontend/src/pages/student/UploadMarksPage.jsx
import React, { useState, useRef } from 'react';
import api from '../../services/api';

export default function UploadMarksPage() {
  const [file, setFile]         = useState(null);
  const [preview, setPreview]   = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState('');
  const fileRef = useRef();

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError('');
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => setPreview(ev.target.result);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (!f) return;
    setFile(f);
    setResult(null);
    setError('');
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => setPreview(ev.target.result);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleUpload = async () => {
    if (!file) { setError('Please select a file first.'); return; }
    setUploading(true);
    setError('');
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/student/upload-marksheet', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      setFile(null);
      setPreview(null);
      if (fileRef.current) fileRef.current.value = '';
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const gradeColor = (grade) => ({
    'O':  '#16a34a', 'A+': '#22c55e', 'A':  '#3b82f6',
    'B+': '#8b5cf6', 'B':  '#f97316', 'C':  '#eab308',
    'D':  '#ef4444', 'F':  '#dc2626', 'AB': '#6b7280',
    'S*': '#9ca3af', 'S':  '#9ca3af',
  }[grade] || '#6b7280');

  return (
    <div style={{ maxWidth: 820, color: '#f1f5f9' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>
          Upload Marksheet
        </h1>
        <p style={{ fontSize: 14, color: '#64748b' }}>
          Upload your JNTUH grade sheet (JPG, PNG, or PDF — max 10 MB).
          Grades are extracted automatically.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onClick={() => fileRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        style={{
          border: '2px dashed #334155',
          borderRadius: 14,
          padding: '40px 32px',
          textAlign: 'center',
          background: '#0a0f1e',
          cursor: 'pointer',
          marginBottom: 20,
          transition: 'border-color 0.2s',
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>📄</div>
        <div style={{ fontSize: 15, fontWeight: 600, color: '#f1f5f9', marginBottom: 6 }}>
          {file ? file.name : 'Click or drag & drop your grade sheet here'}
        </div>
        <div style={{ fontSize: 13, color: '#475569' }}>
          Supported: JPG · PNG · PDF — Max 10 MB
        </div>
        <input
          ref={fileRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* Image preview */}
      {preview && (
        <div style={{ marginBottom: 20, textAlign: 'center' }}>
          <img
            src={preview}
            alt="Preview"
            style={{
              maxWidth: '100%', maxHeight: 320, borderRadius: 10,
              border: '1px solid #1e293b', objectFit: 'contain',
            }}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{
          background: 'rgba(248,113,113,0.1)', border: '1px solid rgba(248,113,113,0.3)',
          color: '#fca5a5', padding: '12px 16px', borderRadius: 8,
          marginBottom: 16, fontSize: 14,
        }}>
          ❌ {error}
        </div>
      )}

      {/* Upload button */}
      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          style={{
            width: '100%', padding: 14,
            background: uploading ? '#334155' : 'linear-gradient(135deg,#0ea5e9,#38bdf8)',
            color: '#fff', border: 'none', borderRadius: 10,
            fontSize: 15, fontWeight: 600,
            cursor: uploading ? 'not-allowed' : 'pointer',
            marginBottom: 28, display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: 8,
          }}
        >
          {uploading ? (
            <>
              <span style={{
                width: 16, height: 16,
                border: '2px solid rgba(255,255,255,0.3)',
                borderTop: '2px solid #fff',
                borderRadius: '50%',
                animation: 'spin 0.7s linear infinite',
                display: 'inline-block',
              }} />
              Extracting grades…
            </>
          ) : '🚀 Upload & Extract Grades'}
        </button>
      )}

      {/* Result */}
      {result && (
        <div style={{
          background: 'rgba(52,211,153,0.08)',
          border: '1px solid rgba(52,211,153,0.3)',
          borderRadius: 14, padding: 24, marginBottom: 24,
        }}>
          {/* Summary row */}
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            alignItems: 'center', marginBottom: 16,
          }}>
            <h3 style={{ color: '#34d399', margin: 0, fontSize: 17 }}>
              ✅ Semester {result.semester_no} uploaded
            </h3>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 26, fontWeight: 800, color: '#f1f5f9' }}>
                {result.sgpa ?? '—'}
              </div>
              <div style={{ fontSize: 11, color: '#64748b' }}>SGPA</div>
            </div>
          </div>

          {/* Meta */}
          {(result.exam_month_year || result.hall_ticket_no) && (
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>
              {result.exam_month_year && `📅 ${result.exam_month_year}`}
              {result.hall_ticket_no && ` · Hall Ticket: ${result.hall_ticket_no}`}
            </div>
          )}

          {/* Partial extraction warning */}
          {result.extraction_note && result.extraction_note !== 'Parsed successfully' && (
            <div style={{
              background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)',
              padding: '8px 12px', borderRadius: 8, fontSize: 13,
              color: '#fbbf24', marginBottom: 16,
            }}>
              ⚠️ {result.extraction_note}
            </div>
          )}

          {/* Subject table */}
          {result.subjects && result.subjects.length > 0 && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#0f172a' }}>
                    {['Code', 'Subject', 'Grade', 'Points', 'Credits', 'Status'].map((h) => (
                      <th key={h} style={{
                        padding: '10px 12px', textAlign: 'left',
                        color: '#64748b', fontSize: 11, fontWeight: 600,
                        textTransform: 'uppercase', letterSpacing: '0.05em',
                        borderBottom: '1px solid #1e293b',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.subjects.map((s, i) => (
                    <tr key={i} style={{
                      background: i % 2 === 0 ? '#111827' : '#0f172a',
                      borderBottom: '1px solid #1e293b',
                    }}>
                      <td style={{ padding: '10px 12px', color: '#64748b', fontFamily: 'monospace' }}>
                        {s.subject_code}
                      </td>
                      <td style={{ padding: '10px 12px', color: '#f1f5f9' }}>
                        {s.subject_name}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{
                          background: gradeColor(s.grade_letter),
                          color: '#fff', padding: '2px 10px',
                          borderRadius: 12, fontSize: 12, fontWeight: 700,
                        }}>
                          {s.grade_letter}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', fontWeight: 700, color: '#38bdf8' }}>
                        {s.grade_points}
                      </td>
                      <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                        {s.credits}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        {s.is_backlog
                          ? <span style={{ color: '#f87171', fontSize: 12 }}>❌ Backlog</span>
                          : <span style={{ color: '#34d399', fontSize: 12 }}>✅ Pass</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
