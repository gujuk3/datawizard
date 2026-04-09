import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../api';

export default function DatasetDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState(null);
  const [models, setModels] = useState([]);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    API.get(`/datasets/${id}/`).then(r => setDataset(r.data));
    API.get(`/datasets/${id}/preview/`).then(r => setPreview(r.data));
    API.get('/ml/').then(r => {
      setModels(r.data.filter(m => m.dataset_id === parseInt(id)));
    });
  }, [id]);

  if (!dataset) return <div style={styles.loading}>Yükleniyor...</div>;

  return (
    <div>
      <button style={styles.backBtn} onClick={() => navigate('/datasets')}>← Veri Setlerim</button>

      <h2 style={styles.pageTitle}>📄 {dataset.name}</h2>

      {/* Dataset Özeti */}
      <div style={styles.card}>
        <div style={styles.summaryGrid}>
          <div style={styles.summaryItem}><span style={styles.summaryVal}>{dataset.row_count}</span><span style={styles.summaryKey}>Satır</span></div>
          <div style={styles.summaryItem}><span style={styles.summaryVal}>{dataset.column_count}</span><span style={styles.summaryKey}>Sütun</span></div>
          <div style={styles.summaryItem}><span style={styles.summaryVal}>{dataset.file_size} MB</span><span style={styles.summaryKey}>Boyut</span></div>
          <div style={styles.summaryItem}><span style={styles.summaryVal}>{dataset.status}</span><span style={styles.summaryKey}>Durum</span></div>
        </div>
      </div>

      {/* Sütunlar */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>📋 Sütunlar</h3>
        <table style={tStyles.table}>
          <thead><tr>
            {['Sütun Adı', 'Veri Tipi', 'Eksik', 'Benzersiz'].map(h => <th key={h} style={tStyles.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {dataset.columns.map(col => (
              <tr key={col.id}>
                <td style={tStyles.td}><strong>{col.name}</strong></td>
                <td style={tStyles.td}><span style={styles.typeBadge}>{col.data_type}</span></td>
                <td style={{ ...tStyles.td, color: col.missing_count > 0 ? '#e17055' : '#00b894' }}>
                  {col.missing_count}
                </td>
                <td style={tStyles.td}>{col.unique_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {preview && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>👁️ Veri Önizleme (İlk 50 Satır)</h3>
          <p style={{ color: '#636e72', fontSize: '13px', marginBottom: '12px' }}>
            Toplam {preview.total_rows} satırdan ilk 50 tanesi gösteriliyor.
          </p>
          <div style={styles.tableWrapper}>
            <table style={tStyles.table}>
              <thead>
                <tr>
                  {preview.columns.map(col => (
                    <th key={col} style={tStyles.th}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, i) => (
                  <tr key={i} style={i % 2 === 0 ? {} : { background: '#f8f9fa' }}>
                    {row.map((cell, j) => (
                      <td key={j} style={{
                        ...tStyles.td,
                        color: cell === null ? '#b2bec3' : '#2d3436',
                        fontStyle: cell === null ? 'italic' : 'normal',
                      }}>
                        {cell === null ? 'NaN' : cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Bu veri setiyle yapılan hızlı işlemler */}
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>⚡ Hızlı İşlemler</h3>
        <div style={styles.actionRow}>
          <button style={styles.actionBtn} onClick={() => navigate(`/analytics?dataset=${id}`)}>
            📊 Analiz Et
          </button>
          <button style={styles.actionBtn2} onClick={() => navigate(`/training?dataset=${id}`)}>
            🤖 Model Eğit
          </button>
        </div>
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
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', color: '#636e72' },
  backBtn: { background: 'none', border: 'none', color: '#6c5ce7', cursor: 'pointer', fontSize: '14px', marginBottom: '16px', padding: '0' },
  pageTitle: { margin: '0 0 24px', color: '#2d3436' },
  card: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  cardTitle: { margin: '0 0 16px', color: '#2d3436' },
  summaryGrid: { display: 'flex', gap: '32px' },
  summaryItem: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
  summaryVal: { fontSize: '28px', fontWeight: 'bold', color: '#6c5ce7' },
  summaryKey: { fontSize: '12px', color: '#636e72', marginTop: '4px' },
  typeBadge: { background: '#dfe6e9', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' },
  actionRow: { display: 'flex', gap: '12px' },
  actionBtn: { padding: '10px 24px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' },
  actionBtn2: { padding: '10px 24px', background: '#00b894', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', fontWeight: '600' },
  tableWrapper: { overflowX: 'auto', borderRadius: '8px', border: '1px solid #dee2e6' },
};