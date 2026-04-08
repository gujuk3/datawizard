import React, { useState } from 'react';
import API from '../api';

export default function Register() {
  const [form, setForm] = useState({ email:'', username:'', password:'' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post('/auth/register/', form);
      localStorage.setItem('access', res.data.access);
      localStorage.setItem('refresh', res.data.refresh);
      window.location.href = '/dashboard';
    } catch (err) {
      setError('Kayıt başarısız. Email zaten kullanımda olabilir.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🧙 DataWizard</h2>
        <h3 style={styles.subtitle}>Kayıt Ol</h3>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input style={styles.input} type="email" placeholder="Email" value={form.email} onChange={e => setForm({...form, email:e.target.value})} required />
          <input style={styles.input} type="text" placeholder="Kullanıcı Adı" value={form.username} onChange={e => setForm({...form, username:e.target.value})} required />
          <input style={styles.input} type="password" placeholder="Şifre (min 8 karakter)" value={form.password} onChange={e => setForm({...form, password:e.target.value})} required />
          <button style={styles.button} type="submit">Kayıt Ol</button>
        </form>
        <p style={styles.link}>Hesabın var mı? <a href="/login">Giriş Yap</a></p>
      </div>
    </div>
  );
}

const styles = {
  container: { display:'flex', justifyContent:'center', alignItems:'center', height:'100vh', background:'#f0f2f5' },
  card: { background:'white', padding:'40px', borderRadius:'12px', boxShadow:'0 4px 20px rgba(0,0,0,0.1)', width:'360px' },
  title: { textAlign:'center', color:'#6c5ce7', marginBottom:'4px' },
  subtitle: { textAlign:'center', color:'#636e72', marginBottom:'24px', fontWeight:'normal' },
  input: { width:'100%', padding:'12px', marginBottom:'12px', border:'1px solid #ddd', borderRadius:'8px', fontSize:'14px', boxSizing:'border-box' },
  button: { width:'100%', padding:'12px', background:'#6c5ce7', color:'white', border:'none', borderRadius:'8px', fontSize:'16px', cursor:'pointer' },
  error: { color:'red', textAlign:'center', marginBottom:'12px' },
  link: { textAlign:'center', marginTop:'16px', color:'#636e72' },
};