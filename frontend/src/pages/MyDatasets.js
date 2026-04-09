import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';

export default function MyDatasets() {
  const [datasets, setDatasets] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    API.get('/datasets/').then(r => setDatasets(r.data));
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Bu veri setini silmek istediğinize emin misiniz?')) return;
    try {
      await API.delete(`/datasets/${id}/delete/`);
      setDatasets(prev => prev.filter(d => d.id !== id));
    } catch {
      alert('Silme başarısız.');
    }
  };

  return (
    <div>
      <h2 style={styles.pageTitle}>🗄️ Veri Setlerim</h2>

      {datasets.length === 0 ? (
        <div style={styles.empty}>
          <p>Henüz veri seti yüklemediniz.</p>
          <a href="/upload" style={styles.uploadLink}>📂 Veri Yükle</a>
        </div>
      ) : (
        <div style={styles.grid}>
          {datasets.map(ds => (
            <div key={ds.id} style={styles.card} onClick={() => navigate(`/datasets/${ds.id}`)}>
              <div style={styles.cardHeader}>
                <span style={styles.fileIcon}>📄</span>
                <span style={styles.statusBadge}>{ds.status}</span>
              </div>
              <h3 style={styles.dsName}>{ds.name}</h3>
              <div style={styles.metaGrid}>
                <div style={styles.metaItem}><span style={styles.metaVal}>{ds.row_count}</span><span style={styles.metaKey}>Satır</span></div>
                <div style={styles.metaItem}><span style={styles.metaVal}>{ds.column_count}</span><span style={styles.metaKey}>Sütun</span></div>
              </div>
              <div style={styles.uploadDate}>
                {new Date(ds.uploaded_at).toLocaleDateString('tr-TR')}
              </div>
              <div style={styles.viewBtn}>Detay Görüntüle →</div>
              <button
                style={styles.deleteBtn}
                onClick={(e) => handleDelete(e, ds.id)}
              >
                🗑️ Sil
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  pageTitle: { margin: '0 0 24px', color: '#2d3436' },
  empty: { textAlign: 'center', padding: '60px', color: '#636e72' },
  uploadLink: { display: 'inline-block', marginTop: '12px', background: '#6c5ce7', color: 'white', padding: '10px 24px', borderRadius: '8px', textDecoration: 'none' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' },
  card: { background: 'white', padding: '20px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' },
  fileIcon: { fontSize: '28px' },
  statusBadge: { background: '#00b894', color: 'white', padding: '3px 10px', borderRadius: '4px', fontSize: '12px' },
  dsName: { margin: '0 0 16px', fontSize: '15px', color: '#2d3436', wordBreak: 'break-all' },
  metaGrid: { display: 'flex', gap: '16px', marginBottom: '12px' },
  metaItem: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
  metaVal: { fontSize: '20px', fontWeight: 'bold', color: '#6c5ce7' },
  metaKey: { fontSize: '11px', color: '#636e72' },
  uploadDate: { fontSize: '12px', color: '#b2bec3', marginBottom: '12px' },
  viewBtn: { color: '#6c5ce7', fontSize: '13px', fontWeight: '600' },
  deleteBtn: { marginTop: '8px', width: '100%', padding: '6px', background: 'transparent', border: '1px solid #e17055', color: '#e17055', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' },
};