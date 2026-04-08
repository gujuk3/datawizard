import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import API from '../api';

export default function Analysis() {
  const { id } = useParams();
  const [stats, setStats] = useState(null);
  const [missing, setMissing] = useState(null);
  const [corr, setCorr] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      API.get(`/analytics/${id}/statistics/`),
      API.get(`/analytics/${id}/missing/`),
      API.get(`/analytics/${id}/correlation/`),
    ]).then(([s, m, c]) => {
      setStats(s.data.statistics);
      setMissing(m.data.missing_values);
      setCorr(c.data.correlation);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div style={styles.loading}>Yükleniyor...</div>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <a href="/dashboard" style={styles.back}>← Dashboard</a>
        <h2 style={styles.logo}>🧙 DataWizard — Analiz</h2>
        <a href={`/train/${id}`} style={styles.trainBtn}>🤖 Model Eğit</a>
      </div>

      <div style={styles.content}>

        {/* Eksik Veri */}
        <div style={styles.card}>
          <h3>Eksik Veri Raporu</h3>
          <p>Toplam eksik: <strong>{missing.total_missing}</strong> / {missing.total_cells} hücre (%{missing.total_missing_pct})</p>
          <table style={styles.table}>
            <thead><tr><th>Sütun</th><th>Eksik</th><th>%</th></tr></thead>
            <tbody>
              {missing.columns.map(col => (
                <tr key={col.name} style={col.missing_count > 0 ? styles.rowWarn : {}}>
                  <td>{col.name}</td>
                  <td>{col.missing_count}</td>
                  <td>{col.missing_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sayısal İstatistikler */}
        <div style={styles.card}>
          <h3>Sayısal Sütun İstatistikleri</h3>
          <table style={styles.table}>
            <thead><tr><th>Sütun</th><th>Ort</th><th>Medyan</th><th>Std</th><th>Min</th><th>Max</th></tr></thead>
            <tbody>
              {Object.entries(stats.numeric).map(([col, s]) => (
                <tr key={col}>
                  <td><strong>{col}</strong></td>
                  <td>{s.mean}</td>
                  <td>{s.median}</td>
                  <td>{s.std}</td>
                  <td>{s.min}</td>
                  <td>{s.max}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Korelasyon */}
        <div style={styles.card}>
          <h3>Korelasyon Matrisi</h3>
          <table style={styles.table}>
            <thead>
              <tr>
                <th></th>
                {corr.columns.map(c => <th key={c}>{c}</th>)}
              </tr>
            </thead>
            <tbody>
              {corr.columns.map((row, i) => (
                <tr key={row}>
                  <td><strong>{row}</strong></td>
                  {corr.matrix[i].map((val, j) => (
                    <td key={j} style={{
                      background: `rgba(108,92,231,${Math.abs(val)})`,
                      color: Math.abs(val) > 0.5 ? 'white' : 'black',
                      textAlign: 'center',
                    }}>
                      {val}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}

const styles = {
  loading: { display:'flex', justifyContent:'center', alignItems:'center', height:'100vh', fontSize:'18px' },
  container: { minHeight:'100vh', background:'#f0f2f5' },
  header: { background:'#6c5ce7', color:'white', padding:'16px 32px', display:'flex', justifyContent:'space-between', alignItems:'center' },
  back: { color:'white', textDecoration:'none', opacity:0.9 },
  logo: { margin:0, color:'white' },
  trainBtn: { background:'#00b894', color:'white', padding:'8px 16px', borderRadius:'8px', textDecoration:'none' },
  content: { padding:'32px', maxWidth:'900px', margin:'0 auto' },
  card: { background:'white', padding:'24px', borderRadius:'8px', boxShadow:'0 2px 8px rgba(0,0,0,0.08)', marginBottom:'24px' },
  table: { width:'100%', borderCollapse:'collapse', fontSize:'14px' },
  rowWarn: { background:'#fff3cd' },
};