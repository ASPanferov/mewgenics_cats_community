import React, { useState, useEffect, useCallback } from 'react';

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(30, 15, 5, 0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9000,
    padding: '20px',
  },
  modal: {
    background: 'linear-gradient(135deg, #f5e6c8 0%, #e8d5a8 50%, #dbc495 100%)',
    border: '3px solid #5a3a1a',
    borderRadius: '12px',
    padding: '28px',
    maxWidth: '480px',
    width: '100%',
    boxShadow: '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.3)',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  title: {
    margin: '0 0 20px 0',
    color: '#3a2518',
    fontSize: '20px',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  field: {
    marginBottom: '14px',
  },
  label: {
    display: 'block',
    marginBottom: '4px',
    color: '#5a3a1a',
    fontSize: '13px',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    border: '2px solid #8b6914',
    borderRadius: '6px',
    background: '#fdf6e3',
    color: '#3a2518',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
  },
  textarea: {
    width: '100%',
    minHeight: '120px',
    padding: '10px 12px',
    border: '2px solid #8b6914',
    borderRadius: '6px',
    background: '#fdf6e3',
    color: '#3a2518',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
    lineHeight: '1.5',
    resize: 'vertical',
    outline: 'none',
    boxSizing: 'border-box',
  },
  buttons: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
    marginTop: '20px',
  },
  btnCancel: {
    padding: '10px 24px',
    background: '#c9b896',
    color: '#3a2518',
    border: '2px solid #8b6914',
    borderRadius: '6px',
    cursor: 'pointer',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
  },
  btnSend: {
    padding: '10px 24px',
    background: '#3a2518',
    color: '#d4a843',
    border: '2px solid #d4a843',
    borderRadius: '6px',
    cursor: 'pointer',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
    fontWeight: 'bold',
  },
  error: {
    color: '#a33',
    fontSize: '13px',
    marginTop: '8px',
  },
};

export default function FeedbackModal({ isOpen, onClose, userName }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setName(userName || '');
      setEmail('');
      setMessage('');
      setError(null);
    }
  }, [isOpen, userName]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  const handleSend = async () => {
    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }
    setSending(true);
    setError(null);

    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          message: message.trim(),
          page_url: window.location.href,
        }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${res.status}`);
      }
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>
        <h2 style={styles.title}>Feedback / Bug Report</h2>

        <div style={styles.field}>
          <label style={styles.label}>Name (optional)</label>
          <input
            style={styles.input}
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Your name"
          />
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Email</label>
          <input
            style={styles.input}
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="your@email.com"
          />
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Message</label>
          <textarea
            style={styles.textarea}
            value={message}
            onChange={e => setMessage(e.target.value)}
            placeholder="Describe your issue or feedback..."
          />
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.buttons}>
          <button
            style={styles.btnCancel}
            onClick={onClose}
            disabled={sending}
          >
            Cancel
          </button>
          <button
            style={{
              ...styles.btnSend,
              opacity: sending ? 0.6 : 1,
            }}
            onClick={handleSend}
            disabled={sending}
          >
            {sending ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
