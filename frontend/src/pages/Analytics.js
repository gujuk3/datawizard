import React, { useEffect, useState, useCallback } from 'react';
import API from '../api';
import MarkdownText from '../components/MarkdownText';
import ChartImage from '../components/ChartImage';

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
      else if (type === 'explain') res = await API.post(`/analytics/${selectedId}/explain/`, { type: 'statistics' });
      else if (type === 'charts') { setLoading(false); return; }
      setResult({ type, data: res.data });
    } catch (e) {
      setResult({ type: 'error', data: e.response?.data?.error || 'Hata oluştu.' });
    }
    setLoading(false);
  };

  const isActive = !!selectedId;

  const tabs = [
    { key: 'statistics', label: '📈 İstatistikler' },
    { key: 'missing', label: '🔍 Eksik Veri' },
    { key: 'correlation', label: '🔗 Korelasyon' },
    { key: 'preprocess', label: '⚙️ Ön İşleme' },
    { key: 'charts', label: '📊 Grafikler' },
    { key: 'explain', label: '🤖 AI Açıklama' },
  ];

  return (
    <div>
      <h2 style={styles.pageTitle}>📊 Veri Analizi</h2>

      <div style={styles.card}>
        <label style={styles.label}>Veri Seti Seç</label>
        <select style={styles.select} value={selectedId} onChange={e => { setSelectedId(e.target.value); setResult(null); setActiveTab(null); }}>
          <option value="">-- Veri seti seçin --</option>
          {datasets.map(d => (
            <option key={d.id} value={d.id}>{d.name} ({d.row_count} satır)</option>
          ))}
        </select>
      </div>

      <div style={styles.btnRow}>
        {tabs.map(btn => (
          <button
            key={btn.key}
            style={{ ...styles.btn, ...(activeTab === btn.key ? styles.btnActive : {}), ...(!isActive ? styles.btnDisabled : {}) }}
            onClick={() => { setActiveTab(btn.key); if (btn.key !== 'charts' && btn.key !== 'preprocess') run(btn.key); }}
            disabled={!isActive || loading}
          >
            {btn.label}
          </button>
        ))}
      </div>

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

      {activeTab === 'charts' && isActive && (
        <ChartsPanel datasetId={selectedId} />
      )}

      {loading && <div style={styles.loading}>⏳ Hesaplanıyor...</div>}

      {result && !loading && (
        <div style={styles.card}>
          {result.type === 'error' && <p style={{ color: 'red' }}>{result.data}</p>}
          {result.type === 'statistics' && <StatisticsResult data={result.data} datasetId={selectedId} />}
          {result.type === 'missing' && <MissingResult data={result.data} />}
          {result.type === 'correlation' && <CorrelationResult data={result.data} datasetId={selectedId} />}
          {result.type === 'preprocess' && <PreprocessResult data={result.data} />}
          {result.type === 'explain' && <ExplainResult data={result.data} />}
        </div>
      )}
    </div>
  );
}

// ── Charts Panel ──────────────────────────────────────────────────────────────

function ChartsPanel({ datasetId }) {
  const [columns, setColumns] = useState([]);
  const [colMeta, setColMeta] = useState({});
  const [chartType, setChartType] = useState('distribution');
  const [column, setColumn] = useState('');
  const [xCol, setXCol] = useState('');
  const [yCol, setYCol] = useState('');
  const [hueCol, setHueCol] = useState('');
  const [chart, setChart] = useState(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState('');

  useEffect(() => {
    API.get(`/datasets/${datasetId}/`).then(r => {
      const cols = r.data.columns || [];
      setColumns(cols);
      const meta = {};
      cols.forEach(c => { meta[c.name] = c.data_type; });
      setColMeta(meta);
      const numericCols = cols.filter(c => isNumeric(c.data_type));
      if (cols.length > 0) setColumn(cols[0].name);
      if (numericCols.length > 0) { setXCol(numericCols[0].name); setYCol(numericCols[Math.min(1, numericCols.length - 1)].name); }
    });
  }, [datasetId]);

  const isNumeric = dtype => ['int64','float64','int32','float32','int','float'].includes(dtype);
  const numericCols = columns.filter(c => isNumeric(c.data_type));
  const categoricalCols = columns.filter(c => !isNumeric(c.data_type));

  const loadChart = useCallback(async () => {
    setChart(null);
    setChartError('');
    setChartLoading(true);
    try {
      let url = `/analytics/${datasetId}/chart/?`;
      if (chartType === 'distribution') {
        const dtype = colMeta[column] || '';
        url += isNumeric(dtype) ? `type=histogram&column=${column}` : `type=bar&column=${column}`;
      } else if (chartType === 'box') {
        url += 'type=box';
      } else if (chartType === 'scatter') {
        url += `type=scatter&x=${xCol}&y=${yCol}${hueCol ? `&hue=${hueCol}` : ''}`;
      }
      const res = await API.get(url);
      setChart(res.data.chart);
    } catch (e) {
      setChartError(e.response?.data?.error || 'Grafik oluşturulamadı.');
    }
    setChartLoading(false);
  }, [datasetId, chartType, column, xCol, yCol, hueCol, colMeta]);

  useEffect(() => {
    if (columns.length > 0 && column) loadChart();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType, column, xCol, yCol, hueCol]);

  return (
    <div style={styles.card}>
      <h3 style={{ margin: '0 0 16px', color: '#2d3436' }}>📊 Grafik Görüntüleyici</h3>

      {/* Chart type selector */}
      <div style={styles.chartTypeTabs}>
        {[
          { key: 'distribution', label: 'Dağılım' },
          { key: 'box', label: 'Kutu Grafik' },
          { key: 'scatter', label: 'Dağılım Noktası' },
        ].map(t => (
          <button
            key={t.key}
            style={{ ...styles.chartTypeBtn, ...(chartType === t.key ? styles.chartTypeBtnActive : {}) }}
            onClick={() => setChartType(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Controls */}
      {chartType === 'distribution' && (
        <div style={styles.chartControls}>
          <label style={styles.ctrlLabel}>Sütun</label>
          <select style={styles.ctrlSelect} value={column} onChange={e => setColumn(e.target.value)}>
            {columns.map(c => <option key={c.name} value={c.name}>{c.name} ({c.data_type})</option>)}
          </select>
        </div>
      )}

      {chartType === 'box' && (
        <p style={{ color: '#636e72', fontSize: '13px', margin: '8px 0 0' }}>
          Tüm sayısal sütunlar kutu grafiğinde karşılaştırılır.
        </p>
      )}

      {chartType === 'scatter' && (
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '4px' }}>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={styles.ctrlLabel}>X Ekseni</label>
            <select style={styles.ctrlSelect} value={xCol} onChange={e => setXCol(e.target.value)}>
              {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={styles.ctrlLabel}>Y Ekseni</label>
            <select style={styles.ctrlSelect} value={yCol} onChange={e => setYCol(e.target.value)}>
              {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: '140px' }}>
            <label style={styles.ctrlLabel}>Renk (opsiyonel)</label>
            <select style={styles.ctrlSelect} value={hueCol} onChange={e => setHueCol(e.target.value)}>
              <option value="">— yok —</option>
              {categoricalCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
        </div>
      )}

      <ChartImage src={chart} loading={chartLoading} error={chartError} height={400} />
    </div>
  );
}

// ── Result components ─────────────────────────────────────────────────────────

function StatisticsResult({ data, datasetId }) {
  const stats = data.statistics;
  const [activeCol, setActiveCol] = useState('');
  const [chart, setChart] = useState(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [chartError, setChartError] = useState('');

  const allCols = [
    ...Object.keys(stats.numeric).map(c => ({ name: c, kind: 'numeric' })),
    ...Object.keys(stats.categorical).map(c => ({ name: c, kind: 'categorical' })),
  ];

  useEffect(() => {
    if (allCols.length > 0 && !activeCol) setActiveCol(allCols[0].name);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!activeCol) return;
    const kind = stats.numeric[activeCol] ? 'numeric' : 'categorical';
    setChart(null); setChartError(''); setChartLoading(true);
    const type = kind === 'numeric' ? 'histogram' : 'bar';
    API.get(`/analytics/${datasetId}/chart/?type=${type}&column=${activeCol}`)
      .then(r => { setChart(r.data.chart); setChartLoading(false); })
      .catch(e => { setChartError(e.response?.data?.error || 'Grafik yüklenemedi.'); setChartLoading(false); });
  }, [activeCol, datasetId, stats.numeric]);

  return (
    <div>
      <h3>📈 İstatistikler</h3>
      {Object.keys(stats.numeric).length > 0 && (
        <>
          <h4>Sayısal Sütunlar</h4>
          <div style={{ overflowX: 'auto' }}>
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
          </div>
        </>
      )}

      {/* Column chart */}
      {allCols.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{ fontWeight: '600', fontSize: '14px', color: '#2d3436' }}>📊 Sütun Grafiği:</span>
            <select
              style={{ ...styles.select, width: 'auto', marginBottom: 0, padding: '6px 12px' }}
              value={activeCol}
              onChange={e => setActiveCol(e.target.value)}
            >
              {allCols.map(c => (
                <option key={c.name} value={c.name}>{c.name} ({c.kind === 'numeric' ? 'sayısal' : 'kategorik'})</option>
              ))}
            </select>
          </div>
          <ChartImage src={chart} loading={chartLoading} error={chartError} height={320} />
        </div>
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
      <div style={{ overflowX: 'auto' }}>
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
    </div>
  );
}

function CorrelationResult({ data, datasetId }) {
  const c = data.correlation;
  const [heatmap, setHeatmap] = useState(null);
  const [heatmapLoading, setHeatmapLoading] = useState(true);
  const [heatmapError, setHeatmapError] = useState('');

  useEffect(() => {
    API.get(`/analytics/${datasetId}/chart/?type=correlation&method=${c.method}`)
      .then(r => { setHeatmap(r.data.chart); setHeatmapLoading(false); })
      .catch(e => { setHeatmapError(e.response?.data?.error || 'Isı haritası yüklenemedi.'); setHeatmapLoading(false); });
  }, [datasetId, c.method]);

  return (
    <div>
      <h3>🔗 Korelasyon Matrisi</h3>

      {/* Heatmap */}
      <ChartImage src={heatmap} loading={heatmapLoading} error={heatmapError} height={400} />

      {/* Raw table (collapsible feel — always shown below heatmap) */}
      <details style={{ marginTop: '16px' }}>
        <summary style={{ cursor: 'pointer', color: '#636e72', fontSize: '13px', userSelect: 'none' }}>
          Ham tablo göster
        </summary>
        <div style={{ overflowX: 'auto', marginTop: '8px' }}>
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
      </details>
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
      {r.values_filled > 0 && <p>Doldurulan değer sayısı: <strong>{r.values_filled}</strong></p>}
      {r.columns_affected?.length > 0 && (
        <p>Etkilenen sütunlar: <strong>{r.columns_affected.join(', ')}</strong></p>
      )}
    </div>
  );
}

function ExplainResult({ data }) {
  return (
    <div>
      <h3>🤖 AI Açıklama</h3>
      <div style={{
        background: '#f8f6ff', border: '1px solid #a29bfe',
        borderRadius: '8px', padding: '20px',
      }}>
        <MarkdownText>{data.explanation}</MarkdownText>
      </div>
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
  btnRow: { display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' },
  btn: { padding: '10px 16px', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '13px', background: '#dfe6e9', color: '#2d3436', fontWeight: '500' },
  btnActive: { background: '#6c5ce7', color: 'white' },
  btnDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  loading: { textAlign: 'center', padding: '40px', color: '#636e72', fontSize: '16px' },
  chartTypeTabs: { display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' },
  chartTypeBtn: { padding: '8px 16px', border: '1px solid #ddd', borderRadius: '20px', cursor: 'pointer', fontSize: '13px', background: 'white', color: '#636e72' },
  chartTypeBtnActive: { background: '#6c5ce7', color: 'white', border: '1px solid #6c5ce7' },
  chartControls: { marginBottom: '4px' },
  ctrlLabel: { display: 'block', fontSize: '12px', fontWeight: '600', color: '#636e72', marginBottom: '4px' },
  ctrlSelect: { width: '100%', padding: '8px 12px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '13px', background: 'white', marginBottom: '8px' },
};
