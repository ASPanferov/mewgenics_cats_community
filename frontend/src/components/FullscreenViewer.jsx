import React, { useEffect, useCallback } from 'react';

const styles = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(10, 5, 0, 0.92)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9500,
    cursor: 'pointer',
    padding: '20px',
  },
  image: {
    maxWidth: '95vw',
    maxHeight: '95vh',
    objectFit: 'contain',
    borderRadius: '4px',
    boxShadow: '0 0 40px rgba(0,0,0,0.8)',
    cursor: 'default',
  },
};

export default function FullscreenViewer({ imageUrl, isOpen, onClose }) {
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
      };
    }
  }, [isOpen, handleKeyDown]);

  if (!isOpen || !imageUrl) return null;

  return (
    <div style={styles.overlay} onClick={onClose}>
      <img
        src={imageUrl}
        alt="Fullscreen view"
        style={styles.image}
        onClick={e => e.stopPropagation()}
      />
    </div>
  );
}
