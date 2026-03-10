import React from 'react';

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    padding: '40px 20px',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    textAlign: 'center',
  },
  card: {
    background: 'linear-gradient(135deg, #f5e6c8 0%, #e8d5a8 50%, #dbc495 100%)',
    border: '3px solid #5a3a1a',
    borderRadius: '12px',
    padding: '40px',
    maxWidth: '440px',
    width: '100%',
    boxShadow: '0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.3)',
  },
  heading: {
    color: '#3a2518',
    fontSize: '22px',
    margin: '0 0 24px 0',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  positionNumber: {
    fontSize: '72px',
    fontWeight: 'bold',
    color: '#d4a843',
    textShadow: '2px 2px 0 #3a2518',
    margin: '0',
    lineHeight: 1,
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  positionLabel: {
    fontSize: '18px',
    color: '#5a3a1a',
    margin: '8px 0 24px 0',
  },
  message: {
    color: '#6b4c2a',
    fontSize: '14px',
    lineHeight: '1.6',
    margin: '0 0 28px 0',
  },
  feedLink: {
    display: 'inline-block',
    padding: '10px 28px',
    background: '#3a2518',
    color: '#d4a843',
    border: '2px solid #d4a843',
    borderRadius: '8px',
    textDecoration: 'none',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
    fontSize: '15px',
    fontWeight: 'bold',
    transition: 'background 0.2s',
  },
};

export default function WaitlistPage({ user }) {
  const position = user?.waitlist_position ?? '?';
  const total = user?.waitlist_total ?? '?';

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.heading}>You're on the waitlist!</h1>

        <p style={styles.positionNumber}>{position}</p>
        <p style={styles.positionLabel}>
          {position} of {total}
        </p>

        <p style={styles.message}>
          We're gradually opening access to keep things running smoothly.
          You'll get in soon — thanks for your patience!
        </p>

        <a
          href="/feed"
          style={styles.feedLink}
          onMouseEnter={e => e.currentTarget.style.background = '#4d3220'}
          onMouseLeave={e => e.currentTarget.style.background = '#3a2518'}
        >
          Browse the Feed
        </a>
      </div>
    </div>
  );
}
