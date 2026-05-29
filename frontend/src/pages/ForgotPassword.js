import React, { useState } from 'react';
import API from '../api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await API.post('/auth/forgot-password/', { email });
    } catch {}
    setSent(true);
    setLoading(false);
  };

  if (sent) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>🧙 DataWizard</h2>
          <div style={styles.center}>
            <div style={styles.bigIcon}>📧</div>
            <h3 style={styles.successTitle}>Bağlantı Gönderildi</h3>
            <p style={styles.text}>Eğer bu email kayıtlıysa şifre sıfırlama bağlantısı gönderildi. Lütfen gelen kutunuzu kontrol edin.</p>
          </div>
          <p style={styles.link}><a href="/login">Giriş sayfasına dön</a></p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🧙 DataWizard</h2>
        <h3 style={styles.subtitle}>Şifremi Unuttum</h3>
        <p style={styles.desc}>Email adresinizi girin, size sıfırlama bağlantısı gönderelim.</p>
        <form onSubmit={handleSubmit}>
          <input
            style={styles.input}
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? 'Gönderiliyor...' : 'Sıfırlama Bağlantısı Gönder'}
          </button>
        </form>
        <p style={styles.link}><a href="/login">Giriş sayfasına dön</a></p>
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' },
  card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', width: '360px' },
  title: { textAlign: 'center', color: '#6c5ce7', marginBottom: '4px' },
  subtitle: { textAlign: 'center', color: '#636e72', marginBottom: '8px', fontWeight: 'normal' },
  desc: { textAlign: 'center', color: '#b2bec3', fontSize: '13px', marginBottom: '20px' },
  input: { width: '100%', padding: '12px', marginBottom: '12px', border: '1px solid #ddd', borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  button: { width: '100%', padding: '12px', background: '#6c5ce7', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', cursor: 'pointer' },
  link: { textAlign: 'center', marginTop: '16px', color: '#636e72', fontSize: '14px' },
  center: { textAlign: 'center', padding: '8px 0 16px' },
  bigIcon: { fontSize: '48px', marginBottom: '12px' },
  successTitle: { color: '#00b894', marginBottom: '8px' },
  text: { color: '#636e72', fontSize: '14px', lineHeight: '1.6' },
};
