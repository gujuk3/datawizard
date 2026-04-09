import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import API from '../api';

export default function Layout() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    API.get('/auth/me/').then(r => setUser(r.data)).catch(() => {
      localStorage.clear();
      navigate('/login');
    });
  }, [navigate]);

  const logout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: '🏠', label: 'Dashboard' },
    { path: '/upload', icon: '📂', label: 'Veri Yükle' },
    { path: '/analytics', icon: '📊', label: 'Veri Analizi' },
    { path: '/training', icon: '🤖', label: 'Model Eğitimi' },
    { path: '/datasets', icon: '🗄️', label: 'Veri Setlerim' },
  ];

  return (
    <div style={styles.wrapper}>
      {/* Sidebar */}
      <div style={styles.sidebar}>
        <div style={styles.logo}>🧙 DataWizard</div>
        <nav style={styles.nav}>
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {}),
              })}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div style={styles.userSection}>
          <div style={styles.userEmail}>{user?.email}</div>
          <button style={styles.logoutBtn} onClick={logout}>Çıkış Yap</button>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.main}>
        <Outlet />
      </div>
    </div>
  );
}

const styles = {
  wrapper: { display: 'flex', minHeight: '100vh', background: '#f0f2f5' },
  sidebar: {
    width: '240px', minHeight: '100vh', background: '#2d3436',
    display: 'flex', flexDirection: 'column', padding: '0', flexShrink: 0,
  },
  logo: {
    padding: '24px 20px', fontSize: '20px', fontWeight: 'bold',
    color: '#a29bfe', borderBottom: '1px solid #3d4146',
  },
  nav: { flex: 1, padding: '16px 0' },
  navItem: {
    display: 'flex', alignItems: 'center', padding: '12px 20px',
    color: '#b2bec3', textDecoration: 'none', fontSize: '14px',
    transition: 'all 0.2s', gap: '10px',
  },
  navItemActive: {
    color: 'white', background: '#6c5ce7',
    borderRight: '3px solid #a29bfe',
  },
  navIcon: { fontSize: '18px' },
  userSection: {
    padding: '16px 20px', borderTop: '1px solid #3d4146',
  },
  userEmail: { color: '#636e72', fontSize: '12px', marginBottom: '8px', wordBreak: 'break-all' },
  logoutBtn: {
    width: '100%', padding: '8px', background: 'transparent',
    border: '1px solid #636e72', color: '#b2bec3', borderRadius: '6px',
    cursor: 'pointer', fontSize: '13px',
  },
  main: { flex: 1, padding: '32px', overflow: 'auto' },
};