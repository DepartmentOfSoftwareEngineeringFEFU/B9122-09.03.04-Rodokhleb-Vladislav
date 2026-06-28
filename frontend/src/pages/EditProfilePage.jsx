import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import userService from '../services/userService';
import Navbar from '../components/Navbar/Navbar';

const EditProfilePage = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });


  useEffect(() => {
    if (user) setUsername(user.username);
  }, [user]);

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAvatarFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setAvatarPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const formData = new FormData();

      if (username !== user.username) {
        formData.append('username', username);
      }

      if (newPassword) {
        if (newPassword !== confirmPassword) {
          setMessage({ type: 'error', text: 'Пароли не совпадают' });
          setLoading(false);
          return;
        }
        formData.append('password', newPassword);
      }

      if (avatarFile) {
        formData.append('avatar', avatarFile);
      }

      if (username !== user.username || newPassword || avatarFile) {
        await userService.updateProfile(formData);

        await refreshUser();

        setMessage({ type: 'success', text: 'Профиль успешно обновлён!' });
        setTimeout(() => navigate('/profile'), 1500);
      } else {
        setMessage({ type: 'success', text: 'Нет изменений для сохранения' });
        setLoading(false);
      }

    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Ошибка обновления' });
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <Navbar />

      <div style={styles.mainContent}>
        <div style={styles.card}>
          <div style={styles.header}>
            <button style={styles.backButton} onClick={() => navigate('/profile')}>
              ← Назад к профилю
            </button>
            <h1 style={styles.title}>Редактирование профиля</h1>
          </div>

          <form onSubmit={handleSubmit}>
            <div style={styles.avatarSection}>
              <div style={styles.avatarContainer}>
                {avatarPreview ? (
                  <img src={avatarPreview} alt="Preview" style={styles.avatarImage} />
                ) : user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Avatar" style={styles.avatarImage} />
                ) : (
                  <div style={styles.avatarPlaceholder}>
                    <span style={styles.avatarPlaceholderText}>
                      {username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                )}
              </div>
              <label style={styles.avatarButton}>
                <input type="file" accept="image/*" onChange={handleAvatarChange} style={styles.hiddenInput} />
                Изменить аватар
              </label>
              {avatarFile && (
                <span style={styles.fileName}>Выбран файл: {avatarFile.name}</span>
              )}
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Имя пользователя</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={styles.input}
                required
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Email</label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                style={{ ...styles.input, ...styles.inputDisabled }}
              />
            </div>

            <div style={styles.divider}>
              <span style={styles.dividerText}>Смена пароля</span>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Текущий пароль</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                style={styles.input}
                placeholder="Введите текущий пароль"
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Новый пароль</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                style={styles.input}
                placeholder="Введите новый пароль"
              />
            </div>

            <div style={styles.field}>
              <label style={styles.label}>Подтвердите новый пароль</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={styles.input}
                disabled={!newPassword}
              />
            </div>

            {message.text && (
              <div style={{
                ...styles.message,
                background: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                color: message.type === 'success' ? '#10B981' : '#EF4444',
                border: `1px solid ${message.type === 'success' ? '#10B981' : '#EF4444'}33`
              }}>
                {message.text}
              </div>
            )}

            <div style={styles.actions}>
              <button type="button" style={styles.cancelButton} onClick={() => navigate('/profile')}>
                Отмена
              </button>
              <button type="submit" disabled={loading} style={styles.saveButton}>
                {loading ? 'Сохранение...' : 'Сохранить изменения'}
              </button>
            </div>
          </form>
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
  mainContent: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '40px 5%',
    width: '100%',
  },
  card: {
    width: '75%',
    margin: '0 auto',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '20px',
    padding: '48px 56px',
    boxSizing: 'border-box',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    marginBottom: '40px',
    flexWrap: 'wrap',
  },
  backButton: {
    background: 'none',
    border: 'none',
    color: '#4A6CF7',
    fontSize: '16px',
    cursor: 'pointer',
    padding: '8px 0',
  },
  title: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#E2E8F0',
    margin: 0,
  },
  avatarSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '40px',
  },
  avatarContainer: {
    width: '400px',
    height: '400px',
    borderRadius: '50%',
    overflow: 'hidden',
    border: '3px solid #2A3441',
    flexShrink: 0,
    background: '#1E2533',
  },
  avatarImage: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block',
  },
  avatarPlaceholder: {
    width: '100%',
    height: '100%',
    background: '#4A6CF7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarPlaceholderText: {
    fontSize: '56px',
    fontWeight: 700,
    color: 'white',
  },
  avatarButton: {
    padding: '10px 24px',
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '10px',
    cursor: 'pointer',
    color: '#E2E8F0',
    fontSize: '18px',
    transition: 'all 0.2s',
    ':hover': {
      background: '#2A3441',
    },
  },
  fileName: {
    fontSize: '13px',
    color: '#94A3B8',
  },
  hiddenInput: {
    display: 'none',
  },
  field: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    marginBottom: '24px',
  },
  label: {
    width: '180px',
    fontSize: '15px',
    fontWeight: 500,
    color: '#E2E8F0',
    flexShrink: 0,
  },
  input: {
    flex: 1,
    padding: '14px 18px',
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '12px',
    fontSize: '15px',
    color: '#E2E8F0',
    outline: 'none',
    transition: 'border 0.2s',
    ':focus': {
      borderColor: '#4A6CF7',
    },
  },
  inputDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  divider: {
    position: 'relative',
    textAlign: 'center',
    margin: '40px 0 32px',
    borderTop: '1px solid #2A3441',
  },
  dividerText: {
    background: '#161B26',
    padding: '0 20px',
    color: '#94A3B8',
    fontSize: '15px',
    fontWeight: 500,
    position: 'relative',
    top: '-12px',
  },
  message: {
    padding: '16px',
    borderRadius: '12px',
    textAlign: 'center',
    margin: '24px 0',
    fontSize: '14px',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '16px',
    marginTop: '32px',
  },
  cancelButton: {
    padding: '12px 28px',
    background: 'transparent',
    border: '1px solid #2A3441',
    borderRadius: '12px',
    color: '#94A3B8',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 500,
    transition: 'all 0.2s',
    ':hover': {
      borderColor: '#4A6CF7',
      color: '#4A6CF7',
    },
  },
  saveButton: {
    padding: '12px 32px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '12px',
    color: 'white',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '15px',
    transition: 'background 0.2s',
    ':hover': {
      background: '#3A5CD5',
    },
    ':disabled': {
      opacity: 0.6,
      cursor: 'not-allowed',
    },
  },
};

export default EditProfilePage;