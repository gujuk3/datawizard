import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';

export default function Dashboard() {
  const [datasets, setDatasets] = useState([]);
  const [models, setModels] = useState([]);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    API.get('/auth/me/').then(r => setUser(r.data));
    API.get('/datasets/').then(r => setDatasets(r.data));
    API.get('/ml/').then(r => setModels(r.data));
  }, []);

  return (
    <div>
      <h2 style={styles.pageTitle}>🏠 Dashboard</h2>
      <p style={styles.welcome}>Hoş geldiniz, <strong>{user?.username}</strong>!</p>

      {/* Özet Kartlar */}
      <div style={styles.summaryGrid}>
        <div style={styles.summaryCard}>
          <div style={styles.summaryVal}>{datasets.length}</div>
          <div style={styles.summaryKey}>Veri Seti</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryVal}>{models.length}</div>
          <div style={styles.summaryKey}>Eğitilmiş Model</div>
        </div>
        <div style={styles.summaryCard}>
          <div style={styles.summaryVal}>
            {datasets.reduce((a, b) => a + b.row_count, 0).toLocaleString()}
          </div>
          <div style={styles.summaryKey}>Toplam Satır</div>
        </div>
      </div>

      {/* Hızlı İşlemler */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>⚡ Hızlı İşlemler</h3>
        <div style={styles.actionRow}>
          <button style={styles.actionBtn} onClick={() => navigate('/upload')}>📂 Veri Yükle</button>
          <button style={styles.actionBtn} onClick={() => navigate('/analytics')}>📊 Analiz Et</button>
          <button style={styles.actionBtn} onClick={() => navigate('/training')}>🤖 Model Eğit</button>
          <button style={styles.actionBtn} onClick={() => navigate('/datasets')}>🗄️ Veri Setlerim</button>
        </div>
      </div>

      {/* Son Veri Setleri */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>📄 Son Veri Setleri</h3>
        {datasets.length === 0 ? (
          <p style={styles.empty}>Henüz veri seti yüklemediniz.</p>
        ) : (
          <table style={tStyles.table}>
            <thead><tr>
              {['Ad', 'Satır', 'Sütun', 'Durum', 'Tarih'].map(h => <th key={h} style={tStyles.th}>{h}</th>)}
            </tr></thead>
            <tbody>
              {datasets.slice(0, 5).map(ds => (
                <tr key={ds.id} style={styles.tableRow} onClick={() => navigate(`/datasets/${ds.id}`)}>
                  <td style={tStyles.td}>{ds.name}</td>
                  <td style={tStyles.td}>{ds.row_count}</td>
                  <td style={tStyles.td}>{ds.column_count}</td>
                  <td style={tStyles.td}><span style={styles.badge}>{ds.status}</span></td>
                  <td style={tStyles.td}>{new Date(ds.uploaded_at).toLocaleDateString('tr-TR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Son Modeller */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>🤖 Son Modeller</h3>
        {models.length === 0 ? (
          <p style={styles.empty}>Henüz model eğitmediniz.</p>
        ) : (
          <table style={tStyles.table}>
            <thead><tr>
              {['Ad', 'Algoritma', 'Tip', 'Durum', 'Tarih'].map(h => <th key={h} style={tStyles.th}>{h}</th>)}
            </tr></thead>
            <tbody>
              {models.slice(0, 5).map(m => (
                <tr key={m.id}>
                  <td style={tStyles.td}>{m.name}</td>
                  <td style={tStyles.td}>{m.algorithm}</td>
                  <td style={tStyles.td}>{m.model_type}</td>
                  <td style={tStyles.td}><span style={styles.badge}>{m.training_status}</span></td>
                  <td style={tStyles.td}>{new Date(m.created_at).toLocaleDateString('tr-TR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const tStyles = {
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '14px' },
  th: { padding: '10px 14px', background: '#f8f9fa', borderBottom: '2px solid #dee2e6', textAlign: 'left', fontWeight: '600', fontSize: '13px' },
  td: { padding: '10px 14px', borderBottom: '1px solid #f0f2f5' },
};

const styles = {
  pageTitle: { margin: '0 0 4px', color: '#2d3436' },
  welcome: { color: '#636e72', marginBottom: '24px' },
  summaryGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' },
  summaryCard: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', textAlign: 'center' },
  summaryVal: { fontSize: '36px', fontWeight: 'bold', color: '#6c5ce7' },
  summaryKey: { fontSize: '13px', color: '#636e72', marginTop: '4px' },
  card: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  cardTitle: { margin: '0 0 16px', color: '#2d3436' },
  actionRow: { display: 'flex', gap: '12px', flexWrap: 'wrap' },
  actionBtn: { padding: '10px 20px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' },
  empty: { color: '#636e72', textAlign: 'center', padding: '20px' },
  badge: { background: '#00b894', color: 'white', padding: '3px 10px', borderRadius: '4px', fontSize: '12px' },
  tableRow: { cursor: 'pointer' },
};