import React, { useState, useEffect, useRef } from 'react';
import api from '../../services/api';

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
  const bottomRef = useRef(null);

  // Load existing chat history on mount
  useEffect(() => {
    api.get('/student/advisor/history')
      .then(r => {
        setMessages(r.data.messages || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
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
      };
      setMessages(prev => [...prev, aiMsg]);
      if (res.data.data_was_refreshed) {
        setRefreshed(true);
        setTimeout(() => setRefreshed(false), 5000);
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
    <div style={{ textAlign: 'center', padding: 60, color: '#666' }}>
      Loading your chat history...
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column',
                  height: 'calc(100vh - 80px)', maxWidth: 860 }}>

      {/* ── Header ───────────────────────────────────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ color: '#1e3a5f', margin: '0 0 4px' }}>
          🎓 SARS Advisor
        </h2>
        <p style={{ color: '#888', fontSize: 13, margin: 0 }}>
          Your personal AI academic advisor — knows your full
          academic history and risk profile.
        </p>
      </div>

      {/* ── Data refresh banner ───────────────────────────────────── */}
      {refreshed && (
        <div style={{ background: '#f0fff4', border: '1px solid #9ae6b4',
                      borderRadius: 8, padding: '10px 16px',
                      marginBottom: 12, fontSize: 13, color: '#276749' }}>
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
            <h3 style={{ color: '#1e3a5f', margin: '0 0 8px' }}>
              Hello! I'm your SARS Advisor
            </h3>
            <p style={{ color: '#666', fontSize: 14, marginBottom: 24 }}>
              I know your grades, CGPA, backlogs, and risk score.
              Ask me anything about your academics.
            </p>
            {/* Suggestion chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap',
                          gap: 8, justifyContent: 'center' }}>
              {SUGGESTIONS.map((s, i) => (
                <button key={i} onClick={() => sendMessage(s)}
                  style={{ padding: '8px 14px', background: '#f0f4f8',
                           border: '1px solid #dde4ed', borderRadius: 20,
                           fontSize: 13, color: '#1e3a5f',
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
                : msg.isError ? '#fff0f0' : '#f0f4f8',
              color: msg.role === 'user' ? '#fff' : '#2d3748',
              fontSize: 14,
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
              border: msg.isError ? '1px solid #f5c6c6' : 'none',
            }}>
              {msg.content}
              <div style={{ fontSize: 11, marginTop: 4,
                            opacity: 0.6, textAlign: 'right' }}>
                {msg.created_at
                  ? new Date(msg.created_at).toLocaleTimeString(
                      [], { hour: '2-digit', minute: '2-digit' }
                    )
                  : ''}
              </div>
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {sending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '12px 16px', background: '#f0f4f8',
                          borderRadius: '18px 18px 18px 4px',
                          fontSize: 20, color: '#888' }}>
              ✦ ✦ ✦
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
              style={{ padding: '6px 12px', background: '#f0f4f8',
                       border: '1px solid #dde4ed', borderRadius: 16,
                       fontSize: 12, color: '#1e3a5f',
                       cursor: sending ? 'not-allowed' : 'pointer' }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* ── Input bar ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, paddingTop: 12,
                    borderTop: '1px solid #e0e8f0' }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about your grades, CGPA predictions, study plan..."
          disabled={sending}
          rows={2}
          style={{ flex: 1, padding: '10px 14px', borderRadius: 12,
                   border: '1px solid #dde4ed', fontSize: 14,
                   resize: 'none', outline: 'none',
                   fontFamily: 'inherit', lineHeight: 1.5,
                   background: sending ? '#f9f9f9' : '#fff' }}
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
      <div style={{ fontSize: 11, color: '#aaa',
                    textAlign: 'center', marginTop: 6 }}>
        Press Enter to send · Shift+Enter for new line
      </div>
    </div>
  );
}
