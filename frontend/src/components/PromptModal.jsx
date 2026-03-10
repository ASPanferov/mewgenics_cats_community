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
    maxWidth: '600px',
    width: '100%',
    maxHeight: '85vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.3)',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  title: {
    margin: '0 0 16px 0',
    color: '#3a2518',
    fontSize: '20px',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  textarea: {
    width: '100%',
    minHeight: '220px',
    padding: '12px',
    border: '2px solid #8b6914',
    borderRadius: '6px',
    background: '#fdf6e3',
    color: '#3a2518',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '13px',
    lineHeight: '1.5',
    resize: 'vertical',
    outline: 'none',
    boxSizing: 'border-box',
    flex: 1,
    overflowY: 'auto',
  },
  buttons: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'flex-end',
    marginTop: '16px',
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
    transition: 'background 0.2s',
  },
  btnGenerate: {
    padding: '10px 24px',
    background: '#3a2518',
    color: '#d4a843',
    border: '2px solid #d4a843',
    borderRadius: '6px',
    cursor: 'pointer',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
    fontWeight: 'bold',
    transition: 'background 0.2s',
  },
  loading: {
    color: '#6b4c2a',
    textAlign: 'center',
    padding: '40px 0',
    fontSize: '16px',
  },
  error: {
    color: '#a33',
    textAlign: 'center',
    padding: '20px 0',
    fontSize: '14px',
  },
};

export default function PromptModal({ catId, catName, isOpen, onClose, onGenerated }) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !catId) return;
    setLoading(true);
    setError(null);
    setPrompt('');

    fetch(`/api/cat/${catId}/prompt`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setPrompt(data.prompt || '');
      })
      .catch(err => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, catId]);

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch(`/api/cat/${catId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_prompt: prompt }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${res.status}`);
      }
      const result = await res.json();
      if (onGenerated) onGenerated(result);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  }, [catId, prompt, onClose, onGenerated]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={e => e.stopPropagation()}>
        <h2 style={styles.title}>
          {catName ? `Prompt: ${catName}` : 'Generation Prompt'}
        </h2>

        {loading && <div style={styles.loading}>Loading prompt...</div>}
        {error && <div style={styles.error}>{error}</div>}

        {!loading && (
          <textarea
            style={styles.textarea}
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="AI generation prompt..."
          />
        )}

        <div style={styles.buttons}>
          <button
            style={styles.btnCancel}
            onClick={onClose}
            disabled={generating}
            onMouseEnter={e => e.target.style.background = '#b8a47e'}
            onMouseLeave={e => e.target.style.background = '#c9b896'}
          >
            Cancel
          </button>
          <button
            style={{
              ...styles.btnGenerate,
              opacity: (loading || generating) ? 0.6 : 1,
            }}
            onClick={handleGenerate}
            disabled={loading || generating}
            onMouseEnter={e => { if (!loading && !generating) e.target.style.background = '#4d3220'; }}
            onMouseLeave={e => e.target.style.background = '#3a2518'}
          >
            {generating ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </div>
    </div>
  );
}
