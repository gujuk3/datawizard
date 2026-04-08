import React, { useState } from 'react';
import API from '../api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await API.post('/auth/login/', { email, password });
      localStorage.setItem('access', res.data.access);
      localStorage.setItem('refresh', res.data.refresh);
      window.location.href = '/dashboard';
    } catch {
      setError('Geçersiz email veya şifre.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🧙 DataWizard</h2>
        <h3 style={styles.subtitle}>Giriş Yap</h3>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input style={styles.input} type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
          <input style={styles.input} type="password" placeholder="Şifre" value={password} onChange={e => setPassword(e.target.value)} required />
          <button style={styles.button} type="submit">Giriş Yap</button>
        </form>
        <p style={styles.link}>Hesabın yok mu? <a href="/register">Kayıt Ol</a></p>
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