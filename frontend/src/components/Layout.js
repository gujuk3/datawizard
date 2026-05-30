import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import API from '../api';

export default function Layout() {
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);
  const navigate = useNavigate();

  useEffect(() => {
    API.get('/auth/me/').then(r => setUser(r.data)).catch(() => {
      localStorage.clear();
      navigate('/login');
    });
  }, [navigate]);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  const sidebarStyle = isMobile
    ? {
        ...styles.sidebar,
        position: 'fixed',
        left: 0,
        top: 0,
        height: '100vh',
        zIndex: 1000,
        transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.3s ease',
      }
    : styles.sidebar;

  return (
    <div style={styles.wrapper}>
      {/* Mobile overlay */}
      {isMobile && sidebarOpen && (
        <div style={styles.overlay} onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <div style={sidebarStyle}>
        <div style={styles.logo}>
          <span>🧙 DataWizard</span>
          {isMobile && (
            <button style={styles.closeBtn} onClick={() => setSidebarOpen(false)}>✕</button>
          )}
        </div>
        <nav style={styles.nav}>
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                ...styles.navItem,
                ...(isActive ? styles.navItemActive : {}),
              })}
              onClick={() => isMobile && setSidebarOpen(false)}
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
      <div style={{ ...styles.main, padding: isMobile ? '16px' : '32px' }}>
        {isMobile && (
          <div style={styles.mobileHeader}>
            <button style={styles.hamburger} onClick={() => setSidebarOpen(true)}>☰</button>
            <span style={styles.mobileTitle}>🧙 DataWizard</span>
          </div>
        )}
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
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
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
  main: { flex: 1, overflow: 'auto' },
  mobileHeader: {
    display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px',
  },
  hamburger: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '40px', height: '40px', background: '#2d3436', color: 'white',
    border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '20px',
    flexShrink: 0,
  },
  mobileTitle: {
    fontSize: '18px', fontWeight: 'bold', color: '#2d3436',
  },
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 999,
  },
  closeBtn: {
    background: 'transparent', border: 'none', color: '#a29bfe',
    fontSize: '20px', cursor: 'pointer', padding: '4px', lineHeight: 1,
  },
};
