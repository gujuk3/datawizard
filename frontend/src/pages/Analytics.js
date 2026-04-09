import React, { useEffect, useState } from 'react';
import API from '../api';

export default function Analytics() {
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [activeTab, setActiveTab] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preprocessForm, setPreprocessForm] = useState({ strategy: 'mean' });

  useEffect(() => {
    API.get('/datasets/').then(r => setDatasets(r.data));
  }, []);

  const run = async (type) => {
    setLoading(true);
    setActiveTab(type);
    setResult(null);
    try {
      let res;
      if (type === 'statistics') res = await API.get(`/analytics/${selectedId}/statistics/`);
      else if (type === 'missing') res = await API.get(`/analytics/${selectedId}/missing/`);
      else if (type === 'correlation') res = await API.get(`/analytics/${selectedId}/correlation/`);
      else if (type === 'preprocess') res = await API.post(`/analytics/${selectedId}/preprocess/`, preprocessForm);
      setResult({ type, data: res.data });
    } catch (e) {
      setResult({ type: 'error', data: e.response?.data?.error || 'Hata oluştu.' });
    }
    setLoading(false);
  };

  const isActive = !!selectedId;

  return (
    <div>
      <h2 style={styles.pageTitle}>📊 Veri Analizi</h2>

      {/* Dataset Seçimi */}
      <div style={styles.card}>
        <label style={styles.label}>Veri Seti Seç</label>
        <select style={styles.select} value={selectedId} onChange={e => { setSelectedId(e.target.value); setResult(null); }}>
          <option value="">-- Veri seti seçin --</option>
          {datasets.map(d => (
            <option key={d.id} value={d.id}>{d.name} ({d.row_count} satır)</option>
          ))}
        </select>
      </div>

      {/* Analiz Butonları */}
      <div style={styles.btnRow}>
        {[
          { key: 'statistics', label: '📈 İstatistikler' },
          { key: 'missing', label: '🔍 Eksik Veri' },
          { key: 'correlation', label: '🔗 Korelasyon' },
          { key: 'preprocess', label: '⚙️ Ön İşleme' },
        ].map(btn => (
          <button
            key={btn.key}
            style={{ ...styles.btn, ...(activeTab === btn.key ? styles.btnActive : {}), ...(!isActive ? styles.btnDisabled : {}) }}
            onClick={() => run(btn.key)}
            disabled={!isActive || loading}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Ön İşleme Ayarları */}
      {activeTab === 'preprocess' && isActive && (
        <div style={styles.card}>
          <label style={styles.label}>Strateji</label>
          <select style={styles.select} value={preprocessForm.strategy}
            onChange={e => setPreprocessForm({ ...preprocessForm, strategy: e.target.value })}>
            <option value="mean">Ortalama ile Doldur</option>
            <option value="median">Medyan ile Doldur</option>
            <option value="drop">Eksik Satırları Sil</option>
          </select>
          <button style={{ ...styles.btn, ...styles.btnActive, marginTop: '12px' }}
            onClick={() => run('preprocess')} disabled={loading}>
            Uygula
          </button>
        </div>
      )}

      {/* Sonuçlar */}
      {loading && <div style={styles.loading}>⏳ Hesaplanıyor...</div>}

      {result && !loading && (
        <div style={styles.card}>
          {result.type === 'error' && <p style={{ color: 'red' }}>{result.data}</p>}
          {result.type === 'statistics' && <StatisticsResult data={result.data} />}
          {result.type === 'missing' && <MissingResult data={result.data} />}
          {result.type === 'correlation' && <CorrelationResult data={result.data} />}
          {result.type === 'preprocess' && <PreprocessResult data={result.data} />}
        </div>
      )}
    </div>
  );
}

function StatisticsResult({ data }) {
  const stats = data.statistics;
  return (
    <div>
      <h3>📈 İstatistikler</h3>
      {Object.keys(stats.numeric).length > 0 && (
        <>
          <h4>Sayısal Sütunlar</h4>
          <table style={tStyles.table}>
            <thead><tr>
              {['Sütun','Ort','Medyan','Std','Min','Max','Q1','Q3'].map(h => <th key={h} style={tStyles.th}>{h}</th>)}
            </tr></thead>
            <tbody>
              {Object.entries(stats.numeric).map(([col, s]) => (
                <tr key={col}>
                  <td style={tStyles.td}><strong>{col}</strong></td>
                  <td style={tStyles.td}>{s.mean}</td>
                  <td style={tStyles.td}>{s.median}</td>
                  <td style={tStyles.td}>{s.std}</td>
                  <td style={tStyles.td}>{s.min}</td>
                  <td style={tStyles.td}>{s.max}</td>
                  <td style={tStyles.td}>{s.q1}</td>
                  <td style={tStyles.td}>{s.q3}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

function MissingResult({ data }) {
  const m = data.missing_values;
  return (
    <div>
      <h3>🔍 Eksik Veri Raporu</h3>
      <p>Toplam eksik: <strong>{m.total_missing}</strong> / {m.total_cells} (%{m.total_missing_pct})</p>
      <table style={tStyles.table}>
        <thead><tr>
          {['Sütun','Eksik Sayı','Eksik %','Toplam'].map(h => <th key={h} style={tStyles.th}>{h}</th>)}
        </tr></thead>
        <tbody>
          {m.columns.map(col => (
            <tr key={col.name} style={col.missing_count > 0 ? { background: '#fff3cd' } : {}}>
              <td style={tStyles.td}><strong>{col.name}</strong></td>
              <td style={tStyles.td}>{col.missing_count}</td>
              <td style={tStyles.td}>{col.missing_pct}%</td>
              <td style={tStyles.td}>{col.total_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CorrelationResult({ data }) {
  const c = data.correlation;
  return (
    <div>
      <h3>🔗 Korelasyon Matrisi</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={tStyles.table}>
          <thead><tr>
            <th style={tStyles.th}></th>
            {c.columns.map(col => <th key={col} style={tStyles.th}>{col}</th>)}
          </tr></thead>
          <tbody>
            {c.columns.map((row, i) => (
              <tr key={row}>
                <td style={{ ...tStyles.td, fontWeight: 'bold' }}>{row}</td>
                {c.matrix[i].map((val, j) => (
                  <td key={j} style={{
                    ...tStyles.td, textAlign: 'center',
                    background: `rgba(108,92,231,${Math.abs(val)})`,
                    color: Math.abs(val) > 0.5 ? 'white' : '#2d3436',
                  }}>{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PreprocessResult({ data }) {
  const r = data.report;
  return (
    <div>
      <h3>⚙️ Ön İşleme Sonucu</h3>
      <p>Strateji: <strong>{r.strategy}</strong></p>
      <p>Önceki satır: <strong>{r.rows_before}</strong> → Sonraki: <strong>{r.rows_after}</strong></p>
      {r.columns_affected?.length > 0 && (
        <p>Etkilenen sütunlar: <strong>{r.columns_affected.join(', ')}</strong></p>
      )}
    </div>
  );
}

const tStyles = {
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '13px' },
  th: { padding: '8px 12px', background: '#f8f9fa', borderBottom: '2px solid #dee2e6', textAlign: 'left', fontWeight: '600' },
  td: { padding: '8px 12px', borderBottom: '1px solid #dee2e6' },
};

const styles = {
  pageTitle: { margin: '0 0 24px', color: '#2d3436' },
  card: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  label: { display: 'block', fontWeight: '600', marginBottom: '8px', color: '#2d3436' },
  select: { width: '100%', padding: '10px 14px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', background: 'white' },
  btnRow: { display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' },
  btn: { padding: '10px 20px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px', background: '#dfe6e9', color: '#2d3436', fontWeight: '500' },
  btnActive: { background: '#6c5ce7', color: 'white' },
  btnDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  loading: { textAlign: 'center', padding: '40px', color: '#636e72', fontSize: '16px' },
};