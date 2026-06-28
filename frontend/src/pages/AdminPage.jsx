import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const AdminPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
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

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setTimeout(() => {
        setUsers([
          { id: 1, username: 'admin@example.com', role: 'admin', created_at: '2026-01-01' },
          { id: 2, username: 'user1@example.com', role: 'user', created_at: '2026-01-15' },
          { id: 3, username: 'user2@example.com', role: 'user', created_at: '2026-02-01' },
        ]);
        setLoading(false);
      }, 500);
    };
    fetchUsers();
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Админ-панель</h1>

        <div style={styles.userMenuContainer} ref={menuRef}>
          <div
            style={styles.userAvatar}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <span style={styles.userAvatarText}>
              {user?.username?.charAt(0).toUpperCase() || 'A'}
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
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statValue}>3</div>
            <div style={styles.statLabel}>Всего пользователей</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statValue}>2</div>
            <div style={styles.statLabel}>Обычных пользователей</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statValue}>1</div>
            <div style={styles.statLabel}>Администраторов</div>
          </div>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Пользователи системы</h2>
          {loading ? (
            <p style={styles.loading}>Загрузка...</p>
          ) : (
            <table style={styles.table}>
              <thead>
                <tr><th style={styles.th}>ID</th><th style={styles.th}>Email</th><th style={styles.th}>Роль</th><th style={styles.th}>Дата регистрации</th></tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td style={styles.td}>{u.id}</td>
                    <td style={styles.td}>{u.username}</td>
                    <td style={styles.td}>
                      <span style={u.role === 'admin' ? styles.badgeAdmin : styles.badgeUser}>
                        {u.role === 'admin' ? 'Администратор' : 'Пользователь'}
                      </span>
                    </td>
                    <td style={styles.td}>{u.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
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
    '&:hover': {
      background: 'rgba(239, 68, 68, 0.1)',
    },
  },
  content: {
    padding: '32px 5%',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '32px',
  },
  statCard: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '24px',
    textAlign: 'center',
  },
  statValue: {
    fontSize: '32px',
    fontWeight: 700,
    color: '#4A6CF7',
    marginBottom: '8px',
  },
  statLabel: {
    fontSize: '14px',
    color: '#94A3B8',
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
    margin: '0 0 20px',
  },
  loading: {
    color: '#94A3B8',
    textAlign: 'center',
    padding: '40px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    borderBottom: '1px solid #2A3441',
    color: '#94A3B8',
    fontWeight: 500,
  },
  td: {
    padding: '12px',
    borderBottom: '1px solid #2A3441',
    color: '#E2E8F0',
  },
  badgeAdmin: {
    background: '#4A6CF7',
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '12px',
    color: 'white',
  },
  badgeUser: {
    background: '#1E2533',
    padding: '4px 10px',
    borderRadius: '20px',
    fontSize: '12px',
    color: '#94A3B8',
  },
};

export default AdminPage;