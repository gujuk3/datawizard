import React, { useEffect, useState, useCallback } from 'react';
import API from '../api';
import MarkdownText from '../components/MarkdownText';
import ChartImage from '../components/ChartImage';

const ALGORITHMS = [
  { value: 'random_forest_classifier', label: 'Random Forest Classifier', type: 'classification' },
  { value: 'logistic_regression', label: 'Logistic Regression', type: 'classification' },
  { value: 'decision_tree', label: 'Decision Tree', type: 'classification' },
  { value: 'knn', label: 'K-Nearest Neighbors', type: 'classification' },
  { value: 'linear_regression', label: 'Linear Regression', type: 'regression' },
  { value: 'random_forest_regressor', label: 'Random Forest Regressor', type: 'regression' },
];

export default function ModelTraining() {
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [dataset, setDataset] = useState(null);
  const [algorithm, setAlgorithm] = useState('random_forest_classifier');
  const [target, setTarget] = useState('');
  const [testSize, setTestSize] = useState(0.2);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [predInputs, setPredInputs] = useState({});
  const [predResult, setPredResult] = useState(null);
  const [predLoading, setPredLoading] = useState(false);
  const [trainedModels, setTrainedModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedFeatureCols, setSelectedFeatureCols] = useState([]);
  const [modelName, setModelName] = useState('');
  const [fiChart, setFiChart] = useState(null);
  const [fiChartLoading, setFiChartLoading] = useState(false);
  const [evalChart, setEvalChart] = useState(null);
  const [evalChartLoading, setEvalChartLoading] = useState(false);

  useEffect(() => {
  API.get('/datasets/').then(r => setDatasets(r.data));
  API.get('/ml/').then(r => setTrainedModels(r.data));
  }, []);

  const selectDataset = (id) => {
    setSelectedId(id);
    setResult(null);
    setPredResult(null);
    setError('');
    if (id) {
      API.get(`/datasets/${id}/`).then(r => {
        setDataset(r.data);
        const cols = r.data.columns;
        if (cols.length > 0) setTarget(cols[cols.length - 1].name);
      });
    } else {
      setDataset(null);
    }
  };

  const numericCols = dataset?.columns.filter(c =>
    ['int64', 'float64', 'int32', 'float32', 'int', 'float'].includes(c.data_type)
  ) || [];

  const featureCols = numericCols.filter(c => c.name !== target).map(c => c.name);
  const selectedAlgo = ALGORITHMS.find(a => a.value === algorithm);

  // Reset selected feature columns whenever the available pool changes
  useEffect(() => {
    setSelectedFeatureCols(featureCols);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, dataset]);

  const toggleFeatureCol = useCallback((col) => {
    setSelectedFeatureCols(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    );
  }, []);

  const isDuplicateName = modelName.trim() && trainedModels.some(
    m => m.name.toLowerCase() === modelName.trim().toLowerCase()
  );

  const loadCharts = useCallback((modelId, modelType) => {
    setFiChart(null); setEvalChart(null);
    setFiChartLoading(true); setEvalChartLoading(true);

    API.get(`/ml/${modelId}/chart/?type=feature_importance`)
      .then(r => setFiChart(r.data.chart))
      .catch(() => {})
      .finally(() => setFiChartLoading(false));

    const evalType = modelType === 'classification' ? 'confusion_matrix' : 'prediction_vs_actual';
    API.get(`/ml/${modelId}/chart/?type=${evalType}`)
      .then(r => setEvalChart(r.data.chart))
      .catch(() => {})
      .finally(() => setEvalChartLoading(false));
  }, []);

  const handleTrain = async () => {
    if (!modelName.trim()) { setError('Model ismi boş bırakılamaz.'); return; }
    if (isDuplicateName) { setError(`"${modelName.trim()}" isimli bir model zaten mevcut.`); return; }

    setLoading(true);
    setError('');
    setResult(null);
    setPredResult(null);
    setFiChart(null); setEvalChart(null);

    try {
      const res = await API.post('/ml/train/', {
        dataset_id: parseInt(selectedId),
        name: modelName.trim(),
        algorithm,
        model_type: selectedAlgo.type,
        target_column: target,
        feature_columns: selectedFeatureCols,
        test_size: testSize,
      });
      setResult(res.data);
      setTrainedModels(prev => [res.data.model, ...prev.filter(m => m.id !== res.data.model.id)]);
      setModelName('');
      const initInputs = {};
      selectedFeatureCols.forEach(f => initInputs[f] = '');
      setPredInputs(initInputs);
      loadCharts(res.data.model.id, res.data.model.model_type);
    } catch (e) {
      setError(e.response?.data?.error || 'Eğitim başarısız.');
    }
    setLoading(false);
  };

  const handlePredict = async () => {
    setPredLoading(true);
    setPredResult(null);
    try {
      const features = {};
      // Use the model's own feature_columns — not the current training config
      (selectedModel?.feature_columns || []).forEach(f => {
        features[f] = parseFloat(predInputs[f]) || 0;
      });
      const res = await API.post(`/ml/${selectedModel.id}/predict/`, { features });
      setPredResult(res.data);
    } catch (e) {
      setPredResult({ error: e.response?.data?.error || 'Tahmin başarısız.' });
    }
    setPredLoading(false);
  };

  return (
    <div>
      <h2 style={styles.pageTitle}>🤖 Model Eğitimi</h2>

      {/* Dataset Seçimi */}
      <div style={styles.card}>
        <label style={styles.label}>Veri Seti Seç</label>
        <select style={styles.select} value={selectedId} onChange={e => selectDataset(e.target.value)}>
          <option value="">-- Veri seti seçin --</option>
          {datasets.map(d => (
            <option key={d.id} value={d.id}>{d.name} ({d.row_count} satır)</option>
          ))}
        </select>
      </div>

      {/* Model Ayarları */}
      {dataset && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Model Ayarları</h3>
          <div style={{ marginBottom: '16px' }}>
            <label style={styles.label}>Model İsmi</label>
            <input
              type="text"
              style={{
                ...styles.select,
                marginBottom: 0,
                borderColor: isDuplicateName ? '#e17055' : '#ddd',
              }}
              placeholder="örn. İlk Denemem, Iris Sınıflandırıcı..."
              value={modelName}
              onChange={e => { setModelName(e.target.value); setError(''); }}
            />
            {isDuplicateName && (
              <span style={{ fontSize: '12px', color: '#e17055' }}>
                Bu isim zaten kullanılıyor
              </span>
            )}
          </div>

          <div style={styles.grid2}>
            <div>
              <label style={styles.label}>Algoritma</label>
              <select style={styles.select} value={algorithm} onChange={e => setAlgorithm(e.target.value)}>
                <optgroup label="Classification">
                  {ALGORITHMS.filter(a => a.type === 'classification').map(a =>
                    <option key={a.value} value={a.value}>{a.label}</option>
                  )}
                </optgroup>
                <optgroup label="Regression">
                  {ALGORITHMS.filter(a => a.type === 'regression').map(a =>
                    <option key={a.value} value={a.value}>{a.label}</option>
                  )}
                </optgroup>
              </select>
            </div>
            <div>
              <label style={styles.label}>Hedef Sütun</label>
              <select style={styles.select} value={target} onChange={e => setTarget(e.target.value)}>
                {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <label style={styles.label}>Test Oranı: %{Math.round(testSize * 100)}</label>
          <input type="range" min="0.1" max="0.4" step="0.1" value={testSize}
            onChange={e => setTestSize(parseFloat(e.target.value))}
            style={{ width: '100%', marginBottom: '12px' }} />

          <div style={styles.featureBox}>
            <span style={styles.featureLabel}>Özellik Sütunları:</span>
            <span style={styles.featureHint}>Eğitime dahil etmek istemediklerini kaldır</span>
            {featureCols.map(f => {
              const isSelected = selectedFeatureCols.includes(f);
              return (
                <span
                  key={f}
                  onClick={() => toggleFeatureCol(f)}
                  style={isSelected ? styles.featureTagSelected : styles.featureTagDeselected}
                  title={isSelected ? 'Kaldırmak için tıkla' : 'Eklemek için tıkla'}
                >
                  {isSelected ? '✓ ' : '✕ '}{f}
                </span>
              );
            })}
            {selectedFeatureCols.length === 0 && (
              <span style={styles.featureWarning}>En az bir sütun seçilmeli</span>
            )}
          </div>

          {error && <p style={styles.error}>{error}</p>}

          <button
            style={{
              ...styles.trainBtn,
              ...(loading || !target || selectedFeatureCols.length === 0 ? styles.trainBtnDisabled : {})
            }}
            onClick={handleTrain}
            disabled={loading || !target || selectedFeatureCols.length === 0 || !modelName.trim() || isDuplicateName}
          >
            {loading ? '⏳ Eğitiliyor...' : '🚀 Eğitimi Başlat'}
          </button>
        </div>
      )}

      {/* Eğitim Sonuçları */}
      {result && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>✅ Eğitim Tamamlandı</h3>
          <div style={styles.metaRow}>
            <span>Algoritma: <strong>{result.model.algorithm}</strong></span>
            <span>Tip: <strong>{result.model.model_type}</strong></span>
            <span>Süre: <strong>{result.model.training_duration}s</strong></span>
          </div>

          <div style={styles.metricsGrid}>
            {result.model.metrics.filter(m => m.metric_value !== null).map(m => (
              <div key={m.metric_name} style={styles.metricCard}>
                <div style={styles.metricVal}>
                  {m.metric_name === 'r2_score'
                    ? m.metric_value.toFixed(4)
                    : (m.metric_value * (m.metric_name === 'mse' || m.metric_name === 'rmse' ? 1 : 100)).toFixed(1) + (m.metric_name === 'mse' || m.metric_name === 'rmse' ? '' : '%')}
                </div>
                <div style={styles.metricName}>{m.metric_name.replace('_', ' ').toUpperCase()}</div>
              </div>
            ))}
          </div>

          {/* Özellik Önemi */}
          {result.feature_importance && result.feature_importance.length > 0 && (
            <div style={styles.fiSection}>
              <h4 style={styles.fiTitle}>📊 Özellik Önemi</h4>
              {result.feature_importance.map(f => (
                <div key={f.feature} style={styles.fiRow}>
                  <span style={styles.fiName}>{f.feature}</span>
                  <div style={styles.fiBarWrap}>
                    <div style={{ ...styles.fiBar, width: `${f.importance_pct}%` }} />
                  </div>
                  <span style={styles.fiPct}>%{f.importance_pct}</span>
                </div>
              ))}
            </div>
          )}

          {/* SHAP Değerleri */}
          {result.shap_values && result.shap_values.length > 0 && (
            <div style={styles.fiSection}>
              <h4 style={styles.shapTitle}>🔍 SHAP Özellik Etkisi</h4>
              <p style={styles.shapDesc}>Her özelliğin tahmine ortalama katkısı (açıklanabilir AI)</p>
              {result.shap_values.map(s => (
                <div key={s.feature} style={styles.fiRow}>
                  <span style={styles.fiName}>{s.feature}</span>
                  <div style={styles.fiBarWrap}>
                    <div style={{ ...styles.shapBar, width: `${s.shap_pct}%` }} />
                  </div>
                  <span style={styles.fiPct}>%{s.shap_pct}</span>
                </div>
              ))}
            </div>
          )}

          {/* Grafikler */}
          <div style={styles.chartsSection}>
            <h4 style={{ margin: '0 0 12px', color: '#2d3436' }}>📊 Model Grafikleri</h4>
            <div style={styles.chartsGrid}>
              <div>
                <p style={styles.chartLabel}>Özellik Önemi</p>
                <ChartImage src={fiChart} loading={fiChartLoading} height={300} />
              </div>
              <div>
                <p style={styles.chartLabel}>
                  {result.model.model_type === 'classification' ? 'Confusion Matrix' : 'Tahmin vs Gerçek'}
                </p>
                <ChartImage src={evalChart} loading={evalChartLoading} height={300} />
              </div>
            </div>
          </div>

          {/* AI Açıklama */}
          {result.llm_explanation && (
            <div style={styles.explainBox}>
              <h4 style={styles.explainTitle}>🤖 AI Değerlendirmesi</h4>
              <MarkdownText>{result.llm_explanation}</MarkdownText>
            </div>
          )}

          <p style={{ color: '#636e72', fontSize: '13px', marginTop: '8px' }}>
            Tahmin yapmak için aşağıdaki Eğitilmiş Modeller bölümünden bu modeli seçin.
          </p>
        </div>
      )}
      {/* Eğitilmiş Modeller */}
        {trainedModels.length > 0 && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>📦 Eğitilmiş Modeller</h3>
            <p style={{ color: '#636e72', fontSize: '14px', marginBottom: '16px' }}>
              Mevcut bir modeli seçerek yeni veri tahmini yapabilirsiniz.
            </p>
            <div style={styles.modelList}>
              {trainedModels.map(m => (
                <div
                  key={m.id}
                  style={{
                    ...styles.modelCard,
                    ...(selectedModel?.id === m.id ? styles.modelCardActive : {})
                  }}
                  onClick={() => {
                    setSelectedModel(m);
                    setPredResult(null);
                    const initInputs = {};
                    m.feature_columns.forEach(f => initInputs[f] = '');
                    setPredInputs(initInputs);
                  }}
                >
                  <div style={styles.modelCardHeader}>
                    <strong style={{ fontSize: '13px', wordBreak: 'break-all' }}>{m.name}</strong>
                    <span style={{ ...styles.modelTypeBadge, flexShrink: 0, marginLeft: '6px' }}>{m.model_type}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#b2bec3', marginTop: '2px' }}>{m.algorithm}</div>
                  <div style={{ fontSize: '12px', color: '#636e72', marginTop: '6px' }}>
                    Hedef: <strong>{m.target_column}</strong> · Test: %{Math.round(m.train_test_split * 100)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#b2bec3', marginTop: '4px' }}>
                    {new Date(m.created_at).toLocaleDateString('tr-TR')}
                    <button
                      style={styles.modelDeleteBtn}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!window.confirm('Bu modeli silmek istediğinize emin misiniz?')) return;
                        API.delete(`/ml/${m.id}/delete/`).then(() => {
                          setTrainedModels(prev => prev.filter(t => t.id !== m.id));
                          if (selectedModel?.id === m.id) setSelectedModel(null);
                        }).catch(() => alert('Silme başarısız.'));
                      }}
                    >
                      🗑️ Sil
                    </button>
                  </div>

                </div>
              ))}
            </div>
            {selectedModel && (
              <div style={styles.predSection}>
                <h4>🔮 {selectedModel.name} — Yeni Veri Tahmini</h4>
                <p style={styles.predDesc}>Hedef: <strong>{selectedModel.target_column}</strong></p>
                <div style={styles.predGrid}>
                  {selectedModel.feature_columns.map(f => (
                    <div key={f}>
                      <label style={styles.predLabel}>{f}</label>
                      <input
                        type="number"
                        style={styles.predInput}
                        placeholder="Değer girin"
                        value={predInputs[f] || ''}
                        onChange={e => setPredInputs({ ...predInputs, [f]: e.target.value })}
                      />
                    </div>
                  ))}
                </div>
                <button style={styles.predBtn} onClick={handlePredict} disabled={predLoading}>
                  {predLoading ? '⏳ Tahmin ediliyor...' : '🔮 Tahmin Et'}
                </button>
                {predResult && (
                  <div style={styles.predResult}>
                    {predResult.error
                      ? <p style={{ color: 'red' }}>{predResult.error}</p>
                      : <div>
                          <strong>Tahmin Sonucu: </strong>
                          <span style={styles.predValue}>{predResult.prediction}</span>
                        </div>
                    }
                  </div>
                )}
              </div>
            )}
          </div>
        )}

    </div>
  );
}

const styles = {
  pageTitle: { margin: '0 0 24px', color: '#2d3436' },
  card: { background: 'white', padding: '24px', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', marginBottom: '20px' },
  cardTitle: { margin: '0 0 16px', color: '#2d3436' },
  label: { display: 'block', fontWeight: '600', marginBottom: '8px', color: '#2d3436', fontSize: '14px' },
  select: { width: '100%', padding: '10px 14px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', background: 'white', marginBottom: '16px' },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' },
  featureBox: { display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '12px', background: '#f8f9fa', borderRadius: '8px', marginBottom: '16px', alignItems: 'center' },
  featureLabel: { fontSize: '13px', color: '#636e72', fontWeight: '600' },
  featureHint: { fontSize: '11px', color: '#b2bec3', fontStyle: 'italic', width: '100%', marginBottom: '4px' },
  featureTagSelected: { background: '#6c5ce7', color: 'white', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer', userSelect: 'none', transition: 'all 0.15s' },
  featureTagDeselected: { background: '#dfe6e9', color: '#636e72', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer', userSelect: 'none', transition: 'all 0.15s', textDecoration: 'line-through' },
  featureWarning: { fontSize: '12px', color: '#e17055', fontWeight: '600' },
  trainBtnDisabled: { background: '#b2bec3', cursor: 'not-allowed' },
  error: { color: 'red', fontSize: '14px', marginBottom: '12px' },
  trainBtn: { width: '100%', padding: '14px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', fontSize: '16px', cursor: 'pointer', fontWeight: '600' },
  metaRow: { display: 'flex', gap: '24px', marginBottom: '20px', fontSize: '14px', color: '#636e72' },
  metricsGrid: { display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' },
  metricCard: { background: '#f8f9fa', padding: '16px 24px', borderRadius: '10px', textAlign: 'center', minWidth: '120px' },
  metricVal: { fontSize: '28px', fontWeight: 'bold', color: '#6c5ce7' },
  metricName: { fontSize: '12px', color: '#636e72', marginTop: '4px' },
  predSection: { borderTop: '2px solid #f0f2f5', paddingTop: '20px', marginTop: '8px' },
  predDesc: { color: '#636e72', fontSize: '14px', marginBottom: '16px' },
  predGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '12px', marginBottom: '16px' },
  predLabel: { display: 'block', fontSize: '12px', fontWeight: '600', color: '#636e72', marginBottom: '4px' },
  predInput: { width: '100%', padding: '8px 12px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' },
  predBtn: { padding: '12px 32px', background: '#00b894', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer', fontWeight: '600' },
  predResult: { marginTop: '16px', padding: '16px', background: '#f8f9fa', borderRadius: '8px' },
  predValue: { fontSize: '24px', fontWeight: 'bold', color: '#00b894', marginLeft: '8px' },
  modelList: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px', marginBottom: '20px' },
  modelCard: { padding: '14px', border: '2px solid #dfe6e9', borderRadius: '8px', cursor: 'pointer', transition: 'all 0.2s', overflow: 'hidden' },
  modelCardActive: { border: '2px solid #6c5ce7', background: '#f8f6ff' },
  modelCardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  modelTypeBadge: { background: '#6c5ce7', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' },
  modelDeleteBtn: { marginTop: '8px', width: '100%', padding: '4px', background: 'transparent', border: '1px solid #e17055', color: '#e17055', borderRadius: '4px', cursor: 'pointer', fontSize: '11px' },
  fiSection: { marginBottom: '20px' },
  fiTitle: { margin: '0 0 12px', color: '#2d3436' },
  fiRow: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' },
  fiName: { width: '160px', fontSize: '13px', color: '#2d3436', flexShrink: 0 },
  fiBarWrap: { flex: 1, background: '#dfe6e9', borderRadius: '4px', height: '10px' },
  fiBar: { height: '10px', background: '#6c5ce7', borderRadius: '4px', transition: 'width 0.4s' },
  fiPct: { width: '44px', fontSize: '13px', color: '#636e72', textAlign: 'right', flexShrink: 0 },
  explainBox: { background: '#f8f6ff', border: '1px solid #a29bfe', borderRadius: '8px', padding: '16px 20px', marginBottom: '20px' },
  explainTitle: { margin: '0 0 10px', color: '#6c5ce7' },
  shapTitle: { margin: '0 0 4px', color: '#2d3436' },
  shapDesc: { fontSize: '12px', color: '#636e72', marginBottom: '12px' },
  shapBar: { height: '10px', background: '#00b894', borderRadius: '4px', transition: 'width 0.4s' },
  chartsSection: { marginBottom: '20px', paddingTop: '4px' },
  chartsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' },
  chartLabel: { fontSize: '13px', fontWeight: '600', color: '#636e72', margin: '0 0 4px' },
};