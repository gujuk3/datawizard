import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import API from '../api';

export default function ResetPassword() {
  const { token } = useParams();
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirm) {
      setError('Şifreler eşleşmiyor.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await API.post('/auth/reset-password/', { token, new_password: password });
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.error || 'Bir hata oluştu.');
    }
    setLoading(false);
  };

  if (done) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>🧙 DataWizard</h2>
          <div style={styles.center}>
            <div style={styles.bigIcon}>✅</div>
            <h3 style={styles.successTitle}>Şifre Güncellendi!</h3>
            <p style={styles.text}>Yeni şifrenizle giriş yapabilirsiniz.</p>
            <a href="/login" style={styles.loginBtn}>Giriş Yap</a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🧙 DataWizard</h2>
        <h3 style={styles.subtitle}>Yeni Şifre Belirle</h3>
        {error && <p style={styles.error}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input
            style={styles.input}
            type="password"
            placeholder="Yeni şifre (min 8 karakter)"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Yeni şifre tekrar"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            required
          />
          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? 'Güncelleniyor...' : 'Şifremi Güncelle'}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' },
  card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', width: '360px' },
  title: { textAlign: 'center', color: '#6c5ce7', marginBottom: '4px' },
  subtitle: { textAlign: 'center', color: '#636e72', marginBottom: '24px', fontWeight: 'normal' },
  input: { width: '100%', padding: '12px', marginBottom: '12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  button: { width: '100%', padding: '12px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  error: { color: 'red', textAlign: 'center', marginBottom: '12px', fontSize: '14px' },
  center: { textAlign: 'center' },
  bigIcon: { fontSize: '48px', marginBottom: '12px' },
  successTitle: { color: '#00b894', marginBottom: '8px' },
  text: { color: '#636e72', fontSize: '14px', marginBottom: '20px' },
  loginBtn: { display: 'inline-block', padding: '12px 32px', background: '#6c5ce7', color: 'white', borderRadius: '8px', textDecoration: 'none', fontSize: '15px' },
};
