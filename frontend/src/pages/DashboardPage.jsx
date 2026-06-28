import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Панель управления</h1>

        <div style={styles.userMenuContainer} ref={menuRef}>
          <div
            style={styles.userAvatar}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <span style={styles.userAvatarText}>
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>

          {isMenuOpen && (
            <div style={styles.dropdownMenu}>
              <div style={styles.userInfo}>
                <div style={styles.userName}>{user?.username}</div>
                <div style={styles.userEmail}>{user?.email}</div>
                <div style={user?.role === 'admin' ? styles.userRoleAdmin : styles.userRoleUser}>
                  {user?.role === 'admin' ? 'Администратор' : 'Пользователь'}
                </div>
              </div>
              <div style={styles.menuDivider}></div>
              <button onClick={handleLogout} style={styles.logoutButton}>
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Видеоаналитика</h2>
          <p style={styles.cardText}>Загружайте видео, задавайте ключевые слова и находите нужные фрагменты.</p>
          <button style={styles.button}>Загрузить видео</button>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>История запросов</h2>
          <p style={styles.cardText}>Просмотр ранее выполненных анализов и их результатов.</p>
          <button style={styles.buttonOutline}>Перейти к истории</button>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    background: '#0F1117',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    background: '#161B26',
    padding: '20px 5%',
    borderBottom: '1px solid #2A3441',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: 0,
  },
  userMenuContainer: {
    position: 'relative',
  },
  userAvatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    background: '#4A6CF7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    '&:hover': {
      transform: 'scale(1.05)',
      boxShadow: '0 0 10px rgba(74, 108, 247, 0.5)',
    },
  },
  userAvatarText: {
    color: 'white',
    fontSize: '18px',
    fontWeight: 600,
  },
  dropdownMenu: {
    position: 'absolute',
    top: '50px',
    right: '0',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '12px',
    minWidth: '220px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.4)',
    zIndex: 1000,
    overflow: 'hidden',
  },
  userInfo: {
    padding: '16px',
    textAlign: 'center',
  },
  userName: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '4px',
  },
  userEmail: {
    fontSize: '13px',
    color: '#94A3B8',
    marginBottom: '8px',
  },
  userRoleAdmin: {
    display: 'inline-block',
    background: '#4A6CF7',
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '11px',
    color: 'white',
  },
  userRoleUser: {
    display: 'inline-block',
    background: '#1E2533',
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '11px',
    color: '#94A3B8',
  },
  menuDivider: {
    height: '1px',
    background: '#2A3441',
  },
  logoutButton: {
    width: '100%',
    padding: '12px',
    background: 'transparent',
    color: '#EF4444',
    border: 'none',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background 0.2s',
    textAlign: 'center',
    '&:hover': {
      background: 'rgba(239, 68, 68, 0.1)',
    },
  },
  content: {
    padding: '32px 5%',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
    gap: '24px',
  },
  card: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '24px',
  },
  cardTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: '0 0 12px',
  },
  cardText: {
    fontSize: '14px',
    color: '#94A3B8',
    margin: '0 0 20px',
    lineHeight: 1.5,
  },
  button: {
    background: '#4A6CF7',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background 0.2s',
    '&:hover': {
      background: '#3A5CD5',
    },
  },
  buttonOutline: {
    background: 'transparent',
    color: '#4A6CF7',
    border: '1px solid #4A6CF7',
    borderRadius: '10px',
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
    '&:hover': {
      background: 'rgba(74, 108, 247, 0.1)',
    },
  },
};

export default DashboardPage;