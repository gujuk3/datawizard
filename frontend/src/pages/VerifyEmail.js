import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import API from '../api';

export default function VerifyEmail() {
  const { token } = useParams();
  const [state, setState] = useState('loading');

  useEffect(() => {
    API.get(`/auth/verify-email/${token}/`)
      .then(res => {
        localStorage.setItem('access', res.data.access);
        localStorage.setItem('refresh', res.data.refresh);
        setState('success');
        setTimeout(() => { window.location.href = '/dashboard'; }, 2000);
      })
      .catch(() => setState('error'));
  }, [token]);

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>🧙 DataWizard</h2>
        {state === 'loading' && (
          <div style={styles.center}>
            <p style={styles.text}>⏳ Doğrulanıyor...</p>
          </div>
        )}
        {state === 'success' && (
          <div style={styles.center}>
            <div style={styles.bigIcon}>✅</div>
            <h3 style={styles.successTitle}>Email Doğrulandı!</h3>
            <p style={styles.text}>Dashboard'a yönlendiriliyorsunuz...</p>
          </div>
        )}
        {state === 'error' && (
          <div style={styles.center}>
            <div style={styles.bigIcon}>❌</div>
            <h3 style={styles.errorTitle}>Doğrulama Başarısız</h3>
            <p style={styles.text}>Bağlantı geçersiz veya daha önce kullanılmış.</p>
            <a href="/register" style={styles.link}>Tekrar kayıt ol</a>
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' },
  card: { background: 'white', padding: '40px', borderRadius: '12px', boxShadow: '0 4px 20px rgba(0,0,0,0.1)', width: '360px' },
  title: { textAlign: 'center', color: '#6c5ce7', marginBottom: '24px' },
  center: { textAlign: 'center' },
  bigIcon: { fontSize: '48px', marginBottom: '12px' },
  successTitle: { color: '#00b894', marginBottom: '8px' },
  errorTitle: { color: '#e17055', marginBottom: '8px' },
  text: { color: '#636e72', fontSize: '14px' },
  link: { display: 'inline-block', marginTop: '16px', color: '#6c5ce7', fontSize: '14px' },
};
