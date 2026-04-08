import React, { useState } from 'react';
import API from '../api';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

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
    <div style={styles.container}>
      <div style={styles.header}>
        <a href="/dashboard" style={styles.back}>← Dashboard</a>
        <h2 style={styles.logo}>🧙 DataWizard</h2>
      </div>
      <div style={styles.content}>
        <h3>Veri Yükle</h3>
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
          <div style={styles.result}>
            <h4>✅ Yükleme Başarılı</h4>
            <p><strong>Dosya:</strong> {result.dataset.name}</p>
            <p><strong>Satır:</strong> {result.dataset.row_count} · <strong>Sütun:</strong> {result.dataset.column_count}</p>
            <h4>Sütunlar:</h4>
            {result.dataset.columns.map(col => (
              <div key={col.id} style={styles.colCard}>
                <strong>{col.name}</strong> <span style={styles.type}>{col.data_type}</span>
                <span style={styles.meta}>Eksik: {col.missing_count} · Benzersiz: {col.unique_count}</span>
              </div>
            ))}
            <a href="/dashboard" style={styles.button2}>Dashboard'a Dön</a>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight:'100vh', background:'#f0f2f5' },
  header: { background:'#6c5ce7', color:'white', padding:'16px 32px', display:'flex', alignItems:'center', gap:'24px' },
  back: { color:'white', textDecoration:'none', opacity:0.9 },
  logo: { margin:0, color:'white' },
  content: { padding:'32px', maxWidth:'700px', margin:'0 auto' },
  card: { background:'white', padding:'24px', borderRadius:'8px', boxShadow:'0 2px 8px rgba(0,0,0,0.08)', marginBottom:'24px' },
  fileInput: { display:'block', marginBottom:'16px' },
  button: { background:'#6c5ce7', color:'white', border:'none', padding:'12px 24px', borderRadius:'8px', cursor:'pointer', fontSize:'14px' },
  button2: { display:'inline-block', marginTop:'16px', background:'#00b894', color:'white', padding:'10px 20px', borderRadius:'8px', textDecoration:'none' },
  error: { color:'red', marginTop:'12px' },
  result: { background:'white', padding:'24px', borderRadius:'8px', boxShadow:'0 2px 8px rgba(0,0,0,0.08)' },
  colCard: { background:'#f8f9fa', padding:'10px 16px', borderRadius:'6px', marginBottom:'8px', display:'flex', gap:'12px', alignItems:'center' },
  type: { background:'#dfe6e9', padding:'2px 8px', borderRadius:'4px', fontSize:'12px' },
  meta: { color:'#636e72', fontSize:'13px', marginLeft:'auto' },
};