import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import userService from '../../services/userService';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);



  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/profile', label: 'Профиль',},
    { path: '/videos', label: 'Видео пользователя',  },
    { path: '/analysis/new', label: 'Новый анализ',  },
  ];

  return (
    <div style={styles.navbar}>
      <div style={styles.navbarContent}>
        <div style={styles.logo}>
          <span style={styles.logoText}>Сервис анализа видео</span>
        </div>

        <div style={styles.navLinks}>
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              style={{
                ...styles.navLink,
                ...(location.pathname === item.path ? styles.navLinkActive : {}),
              }}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </div>

        <div style={styles.userSection} ref={menuRef}>
          <div style={styles.userInfo} onClick={() => setIsMenuOpen(!isMenuOpen)}>
            <div style={styles.userAvatar}>
              {user?.avatar_url ? (
                <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
              ) : (
                <span style={styles.userAvatarText}>
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              )}
            </div>
            <span style={styles.userName}>{user?.username}</span>
          </div>

          {isMenuOpen && (
            <div style={styles.dropdownMenu}>
              <button
                style={styles.dropdownItem}
                onClick={() => {
                  setIsMenuOpen(false);
                  navigate('/profile/edit');
                }}
              >
                Редактировать профиль
              </button>
              {user?.role === 'admin' && (
                <button
                  style={styles.dropdownItem}
                  onClick={() => {
                    setIsMenuOpen(false);
                    navigate('/admin');
                  }}
                >
                  Админ-панель
                </button>
              )}
              <div style={styles.dropdownDivider}></div>
              <button style={{ ...styles.dropdownItem, ...styles.logoutItem }} onClick={handleLogout}>
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  navbar: {
    background: '#161B26',
    borderBottom: '1px solid #2A3441',
    padding: '0 5%',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  navbarContent: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    height: '64px',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
  },
  logoIcon: {
    fontSize: '24px',
  },
  logoText: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#E2E8F0',
  },
  navLinks: {
    display: 'flex',
    gap: '32px',
    alignItems: 'center',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    color: '#94A3B8',
    textDecoration: 'none',
    fontSize: '22px',
    fontWeight: 500,
    borderRadius: '8px',
    transition: 'all 0.2s',
  },
  navLinkActive: {
    color: '#4A6CF7',
    background: 'rgba(74, 108, 247, 0.1)',
  },
  navIcon: {
    fontSize: '16px',
  },
  userSection: {
    position: 'relative',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    cursor: 'pointer',
    padding: '6px 12px',
    borderRadius: '40px',
    transition: 'background 0.2s',
  },
  userAvatar: {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    background: '#4A6CF7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userAvatarText: {
    color: 'white',
    fontSize: '14px',
    fontWeight: 600,
  },
  userName: {
    fontSize: '20px',
    fontWeight: 500,
    color: '#E2E8F0',
  },
  dropdownMenu: {
    position: 'absolute',
    top: '58px',
    right: '0',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '12px',
    minWidth: '220px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.4)',
    zIndex: 1000,
    overflow: 'hidden',
  },
  dropdownItem: {
    width: '100%',
    padding: '14px 20px',
    background: 'transparent',
    border: 'none',
    fontSize: '18px',
    textAlign: 'left',
    cursor: 'pointer',
    color: '#E2E8F0',
    transition: 'background 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  logoutItem: {
    color: '#EF4444',
  },
  dropdownDivider: {
    height: '1px',
    background: '#2A3441',
    margin: '6px 0',
  },
};

export default Navbar;