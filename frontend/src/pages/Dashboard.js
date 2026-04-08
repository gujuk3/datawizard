import React, { useEffect, useState } from 'react';
import API from '../api';

export default function Dashboard() {
  const [datasets, setDatasets] = useState([]);
  const [user, setUser] = useState(null);

  useEffect(() => {
    API.get('/auth/me/').then(r => setUser(r.data));
    API.get('/datasets/').then(r => setDatasets(r.data));
  }, []);

  const logout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.logo}>🧙 DataWizard</h2>
        <div>
          <span style={styles.userEmail}>{user?.email}</span>
          <button style={styles.logoutBtn} onClick={logout}>Çıkış</button>
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.actions}>
          <a href="/upload" style={styles.actionBtn}>📂 Veri Yükle</a>
        </div>

        <h3>Veri Setlerim</h3>
        {datasets.length === 0 ? (
          <p style={styles.empty}>Henüz veri seti yüklemediniz.</p>
        ) : (
          datasets.map(ds => (
            <div key={ds.id} style={styles.card}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                <div>
                <strong>{ds.name}</strong>
                <span style={styles.badge}>{ds.status}</span>
                <p style={styles.meta}>{ds.row_count} satır · {ds.column_count} sütun</p>
                </div>
                <a href={`/analysis/${ds.id}`} style={styles.analyzeBtn}>📊 Analiz Et</a>
            </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight:'100vh', background:'#f0f2f5' },
  header: { background:'#6c5ce7', color:'white', padding:'16px 32px', display:'flex', justifyContent:'space-between', alignItems:'center' },
  logo: { margin:0, color:'white' },
  userEmail: { marginRight:'16px', opacity:0.9 },
  logoutBtn: { background:'rgba(255,255,255,0.2)', border:'none', color:'white', padding:'8px 16px', borderRadius:'6px', cursor:'pointer' },
  content: { padding:'32px', maxWidth:'800px', margin:'0 auto' },
  actions: { marginBottom:'24px' },
  actionBtn: { background:'#6c5ce7', color:'white', padding:'12px 24px', borderRadius:'8px', textDecoration:'none', display:'inline-block' },
  card: { background:'white', padding:'16px', borderRadius:'8px', marginBottom:'12px', boxShadow:'0 2px 8px rgba(0,0,0,0.08)' },
  badge: { background:'#00b894', color:'white', padding:'2px 8px', borderRadius:'4px', fontSize:'12px', marginLeft:'12px' },
  meta: { color:'#636e72', margin:'8px 0 0', fontSize:'14px' },
  empty: { color:'#636e72', textAlign:'center', padding:'40px' },
  analyzeBtn: { background:'#6c5ce7', color:'white', padding:'8px 16px', borderRadius:'8px', textDecoration:'none', fontSize:'14px' },
};