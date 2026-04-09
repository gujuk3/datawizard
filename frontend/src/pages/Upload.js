import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await API.post('/datasets/upload/', formData);
      setResult(res.data);
      setError('');
    } catch (err) {
      setError('Yükleme başarısız. Dosyayı kontrol edin.');
    }
    setLoading(false);
  };

  return (
    <div>
      <h2 style={styles.pageTitle}>📂 Veri Yükle</h2>

      <div style={styles.card}>
        <form onSubmit={handleUpload}>
          <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])} style={styles.fileInput} />
          <button style={styles.button} type="submit" disabled={!file || loading}>
            {loading ? 'Yükleniyor...' : 'Yükle'}
          </button>
        </form>
        {error && <p style={styles.error}>{error}</p>}
      </div>

      {result && (
        <div style={styles.card}>
          <h4 style={styles.successTitle}>✅ Yükleme Başarılı</h4>
          <p><strong>Dosya:</strong> {result.dataset.name}</p>
          <p><strong>Satır:</strong> {result.dataset.row_count} · <strong>Sütun:</strong> {result.dataset.column_count}</p>
          <h4>Sütunlar:</h4>
          {result.dataset.columns.map(col => (
            <div key={col.id} style={styles.colCard}>
              <strong>{col.name}</strong>
              <span style={styles.type}>{col.data_type}</span>
              <span style={styles.meta}>Eksik: {col.missing_count} · Benzersiz: {col.unique_count}</span>
            </div>
          ))}
          <div style={styles.actionRow}>
            <button style={styles.button2} onClick={() => navigate('/datasets')}>
              🗄️ Veri Setlerim
            </button>
            <button style={styles.button3} onClick={() => navigate('/analytics')}>
              📊 Analiz Et
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  pageTitle: { margin: '0 0 24px', color: '#2d3436' },
  card: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  fileInput: { display: 'block', marginBottom: '16px' },
  button: { background: '#6c5ce7', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '8px', cursor: 'pointer', fontSize: '14px' },
  error: { color: 'red', marginTop: '12px' },
  successTitle: { color: '#00b894', margin: '0 0 12px' },
  colCard: { background: '#f8f9fa', padding: '10px 16px', borderRadius: '6px', marginBottom: '8px', display: 'flex', gap: '12px', alignItems: 'center' },
  type: { background: '#dfe6e9', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' },
  meta: { color: '#636e72', fontSize: '13px', marginLeft: 'auto' },
  actionRow: { display: 'flex', gap: '12px', marginTop: '16px' },
  button2: { padding: '10px 20px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px' },
  button3: { padding: '10px 20px', background: '#00b894', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px' },
};