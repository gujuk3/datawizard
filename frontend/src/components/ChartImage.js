import React from 'react';

export default function ChartImage({ src, loading, error, height = 340 }) {
  if (loading) {
    return (
      <div style={styles.placeholder}>
        <div style={styles.spinner} />
        <span style={styles.placeholderText}>Grafik oluşturuluyor…</span>
      </div>
    );
  }
  if (error) {
    return (
      <div style={{ ...styles.placeholder, background: '#fff5f5' }}>
        <span style={{ color: '#e17055', fontSize: '13px' }}>{error}</span>
      </div>
    );
  }
  if (!src) return null;
  return (
    <div style={styles.wrapper}>
      <img
        src={src}
        alt="chart"
        style={{ maxWidth: '100%', height: 'auto', maxHeight: height, display: 'block', margin: '0 auto' }}
      />
    </div>
  );
}

const styles = {
  wrapper: {
    background: 'white',
    borderRadius: '8px',
    padding: '8px',
    border: '1px solid #eee',
    marginTop: '12px',
  },
  placeholder: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '10px',
    height: '160px',
    background: '#f8f9fa',
    borderRadius: '8px',
    marginTop: '12px',
    border: '1px dashed #ddd',
  },
  placeholderText: {
    color: '#636e72',
    fontSize: '13px',
  },
  spinner: {
    width: '28px',
    height: '28px',
    border: '3px solid #dfe6e9',
    borderTop: '3px solid #6c5ce7',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  },
};

// Inject keyframe once
if (typeof document !== 'undefined' && !document.getElementById('chart-spinner-style')) {
  const style = document.createElement('style');
  style.id = 'chart-spinner-style';
  style.textContent = '@keyframes spin { to { transform: rotate(360deg); } }';
  document.head.appendChild(style);
}
