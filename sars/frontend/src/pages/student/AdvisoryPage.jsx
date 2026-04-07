import React, { useState, useEffect, useRef } from 'react';
import api from '../../services/api';
import ReactMarkdown from 'react-markdown';

const SUGGESTIONS = [
  "What is my current academic risk level?",
  "Which subjects should I focus on most?",
  "What CGPA do I need next semester to reach 8.0?",
  "How can I clear my backlogs faster?",
  "What happens if I score O in all subjects next semester?",
  "Give me a study plan based on my weak subjects",
];

export default function AdvisoryPage() {
  const [messages, setMessages]   = useState([]);
  const [input, setInput]         = useState('');
  const [sending, setSending]     = useState(false);
  const [loading, setLoading]     = useState(true);
  const [refreshed, setRefreshed] = useState(false);
  const [ragStatus, setRagStatus] = useState(null);
  const [openSources, setOpenSources] = useState({});
  const bottomRef = useRef(null);

  const fetchRagStatus = async () => {
    try {
      const res = await api.get('/student/rag-status');
      setRagStatus(res.data || null);
    } catch {
      setRagStatus({ indexed: false, chunk_count: 0, chunk_types: [] });
    }
  };

  // Load existing chat history on mount
  useEffect(() => {
    api.get('/student/advisor/history')
      .then(r => {
        setMessages(r.data.messages || []);
      })
      .catch(() => {
        const errMsg = {
          id: Date.now(), role: 'model',
          content: 'Could not load chat history. Start a new conversation below.',
          isError: true, created_at: new Date().toISOString(),
        };
        setMessages([errMsg]);
      })
      .finally(() => setLoading(false));

    fetchRagStatus();
  }, []);

  const getChunkLabel = (chunkType) => {
    if (chunkType === 'identity') return '👤 Student Profile';
    if (chunkType === 'risk_summary') return '⚠️ Risk Assessment';
    if ((chunkType || '').startsWith('semester_')) return '📚 Semester Grades';
    if (chunkType === 'backlogs') return '🚨 Backlog Record';
    if (chunkType === 'attendance') return '📋 Attendance';
    if (chunkType === 'cgpa_trajectory') return '📈 CGPA Trend';
    if (chunkType === 'placement_eligibility') return '🎯 Placement Eligibility';
    return '📎 Source';
  };

  const getRelevanceStyle = (relevance) => {
    if (relevance === 'HIGH') {
      return { bg: 'rgba(52,211,153,0.12)', color: '#34d399', border: '1px solid rgba(52,211,153,0.35)' };
    }
    if (relevance === 'MEDIUM') {
      return { bg: 'rgba(251,191,36,0.12)', color: '#fbbf24', border: '1px solid rgba(251,191,36,0.35)' };
    }
    return { bg: 'rgba(148,163,184,0.12)', color: '#94a3b8', border: '1px solid rgba(148,163,184,0.35)' };
  };

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const container = bottomRef.current?.parentElement;
    if (!container) return;
    const isNearBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight < 120;
    if (isNearBottom || messages[messages.length-1]?.role === 'user') {
      const timerId = setTimeout(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      return () => clearTimeout(timerId);
    }
  }, [messages]);

  const sendMessage = async (text) => {
    const msgText = text || input.trim();
    if (!msgText || sending) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: msgText,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);
    setRefreshed(false);

    try {
      const res = await api.post('/student/advisor/chat',
        { message: msgText }
      );
      const aiMsg = {
        id: Date.now() + 1,
        role: 'model',
        content: res.data.response,
        created_at: new Date().toISOString(),
        sources: Array.isArray(res.data.sources) ? res.data.sources : [],
      };
      setMessages(prev => [...prev, aiMsg]);
      if (res.data.data_was_refreshed) {
        setRefreshed(true);
        setTimeout(() => setRefreshed(false), 5000);
      }
      if (!ragStatus?.indexed) {
        fetchRagStatus();
      }
    } catch (err) {
      const errMsg = {
        id: Date.now() + 1,
        role: 'model',
        content: '⚠️ Sorry, the advisor is unavailable right now. '
               + 'Please try again in a moment.',
        created_at: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
      Loading your chat history...
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: 'calc(100vh - 80px)', maxWidth: 860 }}>

      {/* ── Header ───────────────────────────────────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ color: '#f1f5f9', margin: '0 0 4px' }}>
          🎓 SARS Advisor
        </h2>
        <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>
          Your personal AI academic advisor — knows your full
          academic history and risk profile.
        </p>
        {ragStatus && (
          <div style={{
            display: 'inline-block',
            marginTop: 10,
            padding: '5px 10px',
            borderRadius: 999,
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: 0.2,
            background: '#0f172a',
            color: ragStatus.indexed ? '#34d399' : '#94a3b8',
            border: ragStatus.indexed
              ? '1px solid rgba(52,211,153,0.4)'
              : '1px solid rgba(148,163,184,0.35)',
          }}>
            {ragStatus.indexed
              ? '🔍 RAG Active — answers grounded in your data'
              : '⚡ Upload grades to enable RAG'}
          </div>
        )}
      </div>

      {/* ── Data refresh banner ───────────────────────────────────── */}
      {refreshed && (
        <div style={{ background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.3)',
                      borderRadius: 8, padding: '10px 16px',
                      marginBottom: 12, fontSize: 13, color: '#34d399' }}>
          ✅ Your latest academic data has been loaded into this
          conversation automatically.
        </div>
      )}

      {/* ── Chat messages ─────────────────────────────────────────── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0',
                    display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Welcome message if no history */}
        {messages.length === 0 && !loading && (
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🤖</div>
            <h3 style={{ color: '#f1f5f9', margin: '0 0 8px' }}>
              Hello! I'm your SARS Advisor
            </h3>
            <p style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>
              I know your grades, CGPA, backlogs, and risk score.
              Ask me anything about your academics.
            </p>
            {/* Suggestion chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap',
                          gap: 8, justifyContent: 'center' }}>
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)}
                  style={{ padding: '8px 14px', background: '#1e293b',
                           border: '1px solid #263348', borderRadius: 20,
                           fontSize: 13, color: '#94a3b8',
                           cursor: 'pointer' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message bubbles */}
        {messages.map(msg => (
          <div key={msg.id}
            style={{ display: 'flex',
                     justifyContent: msg.role === 'user'
                       ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '75%',
              padding: '12px 16px',
              borderRadius: msg.role === 'user'
                ? '18px 18px 4px 18px'
                : '18px 18px 18px 4px',
              background: msg.role === 'user'
                ? '#1e3a5f'
                : msg.isError ? 'rgba(248,113,113,0.08)' : '#1e293b',
              color: msg.role === 'user' ? '#fff' : '#f1f5f9',
              fontSize: 14,
              lineHeight: 1.6,
              whiteSpace: msg.role === 'user' ? 'pre-wrap' : undefined,
              border: msg.isError ? '1px solid rgba(248,113,113,0.3)' : 'none',
            }}>
              {msg.role === 'model' && !msg.isError ? (
                <ReactMarkdown
                  components={{
                    p: ({children}) => <p style={{margin:'4px 0',lineHeight:1.6}}>{children}</p>,
                    strong: ({children}) => <strong style={{color:'#f1f5f9'}}>{children}</strong>,
                    ul: ({children}) => <ul style={{paddingLeft:18,margin:'4px 0'}}>{children}</ul>,
                    li: ({children}) => <li style={{margin:'2px 0'}}>{children}</li>,
                    h3: ({children}) => <h3 style={{color:'#93c5fd',margin:'8px 0 4px',fontSize:14}}>{children}</h3>,
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : msg.content}
              <div style={{ fontSize: 11, marginTop: 4,
                            opacity: 0.6, textAlign: 'right' }}>
                {msg.created_at
                  ? new Date(msg.created_at).toLocaleTimeString(
                      [], { hour: '2-digit', minute: '2-digit' }
                    )
                  : ''}
              </div>

              {msg.role === 'model' && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <button
                    onClick={() => setOpenSources(prev => ({ ...prev, [msg.id]: !prev[msg.id] }))}
                    style={{
                      background: '#0f172a',
                      color: '#cbd5e1',
                      border: '1px solid #334155',
                      borderRadius: 8,
                      fontSize: 12,
                      padding: '4px 8px',
                      cursor: 'pointer',
                    }}
                  >
                    📎 Sources ({msg.sources.length})
                  </button>

                  {openSources[msg.id] && (
                    <div style={{ marginTop: 8, display: 'grid', gap: 8 }}>
                      {msg.sources.map((source, idx) => {
                        const badge = getRelevanceStyle(source.relevance);
                        return (
                          <div key={`${msg.id}-source-${idx}`} style={{
                            background: '#0b1220',
                            border: '1px solid #334155',
                            borderRadius: 8,
                            padding: '8px 10px',
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                              <span style={{
                                background: 'rgba(59,130,246,0.12)',
                                color: '#93c5fd',
                                border: '1px solid rgba(59,130,246,0.35)',
                                borderRadius: 999,
                                fontSize: 11,
                                padding: '2px 8px',
                                fontWeight: 600,
                              }}>
                                {getChunkLabel(source.chunk_type)}
                              </span>
                              <span style={{
                                ...badge,
                                borderRadius: 999,
                                fontSize: 11,
                                padding: '2px 8px',
                                fontWeight: 700,
                                whiteSpace: 'nowrap',
                              }}>
                                {source.relevance || 'LOW'}
                              </span>
                            </div>
                            <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.5 }}>
                              {source.preview}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {sending && (
          <div style={{ display:'flex', justifyContent:'flex-start', marginBottom: 16 }}>
            <div style={{
              padding:'12px 16px', background:'#1e293b',
              borderRadius:'18px 18px 18px 4px',
              display:'flex', gap:4, alignItems:'center',
            }}>
              {[0,1,2].map(i => (
                <div key={i} style={{
                  width:8, height:8, borderRadius:'50%',
                  background:'#94a3b8',
                  animation:'bounce 1.2s infinite',
                  animationDelay:`${i*0.2}s`,
                }}/>
              ))}
              <style>{`
                @keyframes bounce {
                  0%,60%,100%{transform:translateY(0)}
                  30%{transform:translateY(-6px)}
                }
              `}</style>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Suggestion chips (after first message) ────────────────── */}
      {messages.length > 0 && messages.length < 4 && (
        <div style={{ display: 'flex', flexWrap: 'wrap',
                      gap: 6, marginBottom: 10 }}>
          {SUGGESTIONS.slice(0, 3).map((s, i) => (
            <button key={i} onClick={() => sendMessage(s)}
              disabled={sending}
              style={{ padding: '6px 12px', background: '#1e293b',
                       border: '1px solid #263348', borderRadius: 16,
                       fontSize: 12, color: '#94a3b8',
                       cursor: sending ? 'not-allowed' : 'pointer' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* ── Input bar ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, paddingTop: 12,
                    borderTop: '1px solid #1e293b' }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about your grades, CGPA predictions, study plan..."
          disabled={sending}
          rows={2}
          style={{ flex: 1, padding: '10px 14px', borderRadius: 12,
                   border: '1px solid #1e293b', fontSize: 14,
                   resize: 'none', outline: 'none',
                   fontFamily: 'inherit', lineHeight: 1.5,
                   background: sending ? '#0a0f1e' : '#111827',
                   color: '#f1f5f9' }}
        />
        <button onClick={() => sendMessage()} disabled={sending || !input.trim()}
          style={{ padding: '0 22px', background:
                     sending || !input.trim() ? '#ccc' : '#1e3a5f',
                   color: '#fff', border: 'none', borderRadius: 12,
                   fontSize: 18, cursor:
                     sending || !input.trim() ? 'not-allowed' : 'pointer',
                   transition: 'background 0.2s' }}>
          ➤
        </button>
      </div>
      <div style={{ fontSize: 11, color: '#475569',
                    textAlign: 'center', marginTop: 6 }}>
        Press Enter to send · Shift+Enter for new line
      </div>
    </div>
  );
}
