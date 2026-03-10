import React from 'react';
import { ToastContext, useToastState } from '../hooks/useToast';

const styles = {
  container: {
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 10000,
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    pointerEvents: 'none',
  },
  toast: {
    pointerEvents: 'auto',
    background: '#3a2518',
    color: '#d4a843',
    border: '2px solid #d4a843',
    borderRadius: '6px',
    padding: '12px 20px',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '14px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
    cursor: 'pointer',
    maxWidth: '360px',
    wordBreak: 'break-word',
    animation: 'toast-slide-in 0.3s ease-out',
  },
};

const keyframesStyle = `
@keyframes toast-slide-in {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
`;

export function ToastProvider({ children }) {
  const { toasts, showToast, dismissToast } = useToastState();

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <style>{keyframesStyle}</style>
      <div style={styles.container}>
        {toasts.map(toast => (
          <div
            key={toast.id}
            style={styles.toast}
            onClick={() => dismissToast(toast.id)}
            role="alert"
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export default ToastProvider;
