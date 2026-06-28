import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h1 style={styles.title}>Добро пожаловать</h1>
        <div style={styles.tabsWrapper}>
          <div style={{ ...styles.tab, ...styles.tabActive }}>Вход</div>
          <Link to="/register" style={{ ...styles.tab, textDecoration: 'none' }}>Регистрация</Link>
        </div>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
            required
          />
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            required
          />
          {error && <div style={styles.error}>{error}</div>}
          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
        <div style={styles.footer}>
          Нет аккаунта? <Link to="/register" style={styles.link}>Зарегистрироваться</Link>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0F1117',
  },
  card: {
    background: '#161B26',
    width: '380px',
    padding: '40px 32px',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.4)',
    border: '1px solid #2A3441',
  },
  title: {
    textAlign: 'center',
    margin: '0 0 32px',
    fontSize: '24px',
    fontWeight: 600,
    color: '#E2E8F0',
  },
  tabsWrapper: {
    display: 'flex',
    marginBottom: '32px',
    borderBottom: '1px solid #2A3441',
  },
  tab: {
    flex: 1,
    padding: '12px',
    textAlign: 'center',
    fontWeight: 500,
    color: '#94A3B8',
    display: 'block',
  },
  tabActive: {
    color: '#E2E8F0',
    borderBottom: '3px solid #4A6CF7',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    marginBottom: '20px',
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '10px',
    fontSize: '16px',
    color: '#E2E8F0',
    boxSizing: 'border-box',
  },
  button: {
    width: '100%',
    padding: '14px',
    background: '#4A6CF7',
    color: 'white',
    border: 'none',
    borderRadius: '10px',
    fontSize: '16px',
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: '8px',
  },
  error: {
    color: '#EF4444',
    fontSize: '14px',
    marginBottom: '16px',
    textAlign: 'center',
  },
  footer: {
    textAlign: 'center',
    marginTop: '24px',
    fontSize: '14px',
    color: '#94A3B8',
  },
  link: {
    color: '#4A6CF7',
    textDecoration: 'none',
  },
};

export default Login;