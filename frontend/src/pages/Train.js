import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import API from '../api';

const ALGORITHMS = [
  { value:'random_forest_classifier', label:'Random Forest (Sınıflandırma)', type:'classification' },
  { value:'logistic_regression', label:'Logistic Regression', type:'classification' },
  { value:'decision_tree', label:'Decision Tree', type:'classification' },
  { value:'knn', label:'K-Nearest Neighbors', type:'classification' },
  { value:'linear_regression', label:'Linear Regression (Regresyon)', type:'regression' },
  { value:'random_forest_regressor', label:'Random Forest (Regresyon)', type:'regression' },
];

export default function Train() {
  const { id } = useParams();
  const [dataset, setDataset] = useState(null);
  const [algorithm, setAlgorithm] = useState('random_forest_classifier');
  const [target, setTarget] = useState('');
  const [testSize, setTestSize] = useState(0.2);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    API.get(`/datasets/${id}/`).then(r => {
      setDataset(r.data);
      if (r.data.columns.length > 0) {
        setTarget(r.data.columns[r.data.columns.length - 1].name);
      }
    });
  }, [id]);

  const selectedAlgo = ALGORITHMS.find(a => a.value === algorithm);

  const numericCols = dataset?.columns.filter(c =>
    ['int64','float64','int32','float32'].includes(c.data_type)
  ) || [];

  const featureCols = numericCols.filter(c => c.name !== target).map(c => c.name);

  const handleTrain = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await API.post('/ml/train/', {
        dataset_id: parseInt(id),
        algorithm,
        model_type: selectedAlgo.type,
        target_column: target,
        feature_columns: featureCols,
        test_size: testSize,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.error || 'Eğitim başarısız.');
    }
    setLoading(false);
  };

  if (!dataset) return <div style={styles.loading}>Yükleniyor...</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <a href={`/analysis/${id}`} style={styles.back}>← Analiz</a>
        <h2 style={styles.logo}>🧙 DataWizard — Model Eğitimi</h2>
      </div>

      <div style={styles.content}>
        <div style={styles.card}>
          <h3>Model Ayarları</h3>
          <p style={styles.dsInfo}>📂 {dataset.name} · {dataset.row_count} satır · {dataset.column_count} sütun</p>

          <label style={styles.label}>Algoritma</label>
          <select style={styles.select} value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
            {ALGORITHMS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
          </select>

          <label style={styles.label}>Hedef Sütun (tahmin edilecek)</label>
          <select style={styles.select} value={target} onChange={e => setTarget(e.target.value)}>
            {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>

          <label style={styles.label}>Özellik Sütunları (otomatik seçildi)</label>
          <div style={styles.features}>
            {featureCols.map(f => <span key={f} style={styles.featureTag}>{f}</span>)}
          </div>

          <label style={styles.label}>Test Oranı: %{Math.round(testSize * 100)}</label>
          <input type="range" min="0.1" max="0.4" step="0.1" value={testSize}
            onChange={e => setTestSize(parseFloat(e.target.value))} style={{width:'100%'}} />

          {error && <p style={styles.error}>{error}</p>}

          <button style={styles.button} onClick={handleTrain} disabled={loading || !target}>
            {loading ? '⏳ Eğitiliyor...' : '🚀 Eğitimi Başlat'}
          </button>
        </div>

        {result && (
          <div style={styles.card}>
            <h3>✅ Model Eğitimi Tamamlandı</h3>
            <p><strong>Algoritma:</strong> {result.model.algorithm}</p>
            <p><strong>Süre:</strong> {result.model.training_duration}s</p>
            <h4>Metrikler</h4>
            <div style={styles.metrics}>
              {result.model.metrics
                .filter(m => m.metric_value !== null)
                .map(m => (
                  <div key={m.metric_name} style={styles.metricCard}>
                    <div style={styles.metricValue}>{(m.metric_value * 100).toFixed(1)}%</div>
                    <div style={styles.metricName}>{m.metric_name}</div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  loading: { display:'flex', justifyContent:'center', alignItems:'center', height:'100vh' },
  container: { minHeight:'100vh', background:'#f0f2f5' },
  header: { background:'#6c5ce7', color:'white', padding:'16px 32px', display:'flex', alignItems:'center', gap:'24px' },
  back: { color:'white', textDecoration:'none', opacity:0.9 },
  logo: { margin:0, color:'white' },
  content: { padding:'32px', maxWidth:'700px', margin:'0 auto' },
  card: { background:'white', padding:'24px', borderRadius:'8px', boxShadow:'0 2px 8px rgba(0,0,0,0.08)', marginBottom:'24px' },
  dsInfo: { color:'#636e72', marginBottom:'20px' },
  label: { display:'block', fontWeight:'bold', marginBottom:'6px', marginTop:'16px', color:'#2d3436' },
  select: { width:'100%', padding:'10px', border:'1px solid #ddd', borderRadius:'8px', fontSize:'14px', marginBottom:'4px' },
  features: { display:'flex', flexWrap:'wrap', gap:'8px', padding:'12px', background:'#f8f9fa', borderRadius:'8px' },
  featureTag: { background:'#6c5ce7', color:'white', padding:'4px 10px', borderRadius:'4px', fontSize:'13px' },
  button: { width:'100%', padding:'14px', background:'#6c5ce7', color:'white', border:'none', borderRadius:'8px', fontSize:'16px', cursor:'pointer', marginTop:'24px' },
  error: { color:'red', marginTop:'12px' },
  metrics: { display:'flex', gap:'16px', flexWrap:'wrap' },
  metricCard: { background:'#f0f2f5', padding:'16px', borderRadius:'8px', textAlign:'center', minWidth:'100px' },
  metricValue: { fontSize:'24px', fontWeight:'bold', color:'#6c5ce7' },
  metricName: { fontSize:'12px', color:'#636e72', marginTop:'4px' },
};