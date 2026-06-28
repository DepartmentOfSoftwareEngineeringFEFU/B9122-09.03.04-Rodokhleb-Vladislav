import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import userService from '../services/userService';
import RequestCard from '../components/Profile/RequestCard';
import Navbar from '../components/Navbar/Navbar';

const ProfilePage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const [profileData, statsData] = await Promise.all([
          userService.getProfile(),
          userService.getProfileStats()
        ]);
        console.log("Данные профиля с бэкенда:", profileData);
        setProfile(profileData);
        setStats(statsData);
      } catch (error) {
        console.error('Error fetching profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  useEffect(() => {
    console.log('ProfilePage: Данные пользователя из контекста:', user);
    console.log('ProfilePage: user.preview_url:', user?.preview_url);
  }, [user]);

  useEffect(() => {
    const fetchRequests = async () => {
      setRequestsLoading(true);
      try {
        const data = await userService.getUserRequests(page, 10);
        setRequests(data.items || []);
        setTotalPages(data.pages || 1);
      } catch (error) {
        console.error('Error fetching requests:', error);
      } finally {
        setRequestsLoading(false);
      }
    };

    fetchRequests();
  }, [page]);

  const handleDeleteRequest = async (requestId) => {
    if (window.confirm('Вы уверены, что хотите удалить этот запрос и все его результаты?')) {
      try {
        await userService.deleteRequest(requestId);
        setRequests(requests.filter(r => r.id !== requestId));
      } catch (error) {
        console.error('Error deleting request:', error);
        alert('Ошибка при удалении запроса');
      }
    }
  };

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner}></div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Navbar />

      <div style={styles.mainContent}>
        <div style={styles.profileCard}>
          <div style={styles.profileHeader}>
            <div style={styles.avatarLarge}>
              {profile?.avatar_url ? (
                <img src={profile.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }} />
              ) : (
                <span style={styles.avatarLargeText}>
                  {profile?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              )}
            </div>
            <div style={styles.profileInfo}>
              <div style={styles.profileName}>{profile?.username}</div>
              <div style={styles.profileEmail}>
                  Почта: {profile?.email}</div>
              <div style={styles.profileDate}>
                Зарегистрирован: {new Date(profile?.created_at).toLocaleDateString('ru-RU')}
              </div>
            </div>
          </div>
        </div>

        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statValue}>{stats?.videos_count || 0}</div>
            <div style={styles.statLabel}>Видео загружено</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statValue}>{stats?.search_requests_count || 0}</div>
            <div style={styles.statLabel}>Поисковых запросов</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statValue}>
              {requests.filter(r => r.status === 'completed').length}
            </div>
            <div style={styles.statLabel}>Завершенных анализов</div>
          </div>
        </div>

        <div style={styles.historySection}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>История поисковых запросов</h2>
          </div>

          {requestsLoading ? (
            <div style={styles.loadingRequests}>
              <div style={styles.spinnerSmall}></div>
              <span>Загрузка запросов...</span>
            </div>
          ) : requests.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={styles.emptyStateIcon}>🔍</div>
              <div style={styles.emptyStateTitle}>Нет поисковых запросов</div>
              <div style={styles.emptyStateText}>
                Начните анализ видео, чтобы увидеть историю запросов
              </div>
              <button
                style={styles.emptyStateButton}
                onClick={() => navigate('/analysis/new')}
              >
                Новый анализ видеоряда
              </button>
            </div>
          ) : (
            <>
              {requests.map((request) => (
                <RequestCard
                  key={request.id}
                  request={request}
                  onDelete={handleDeleteRequest}
                />
              ))}

              {totalPages > 1 && (
                <div style={styles.pagination}>
                  <button
                    style={{ ...styles.pageButton, ...(page === 1 ? styles.pageButtonDisabled : {}) }}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    ← Назад
                  </button>
                  <span style={styles.pageInfo}>
                    Страница {page} из {totalPages}
                  </span>
                  <button
                    style={{ ...styles.pageButton, ...(page === totalPages ? styles.pageButtonDisabled : {}) }}
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    Вперед →
                  </button>
                </div>
              )}
            </>
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
  mainContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '32px 5%',
  },
  loadingContainer: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0F1117',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid #2A3441',
    borderTopColor: '#4A6CF7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  profileCard: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '32px',
    marginBottom: '32px',
  },
  profileHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '28px',
  },
  avatarLarge: {
    width: '150px',
    height: '150px',
    borderRadius: '50%',
    background: '#4A6CF7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarLargeText: {
    color: 'white',
    fontSize: '42px',
    fontWeight: 700,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: '35px',
    fontWeight: 700,
    color: '#E2E8F0',
    marginBottom: '15px',
  },
  profileEmail: {
    fontSize: '20px',
    color: '#94A3B8',
    marginBottom: '6px',
  },
  profileDate: {
    fontSize: '20px',
    color: '#94A3B8',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
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
  historySection: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '32px',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '25px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: 0,
  },
  loadingRequests: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '60px',
    color: '#94A3B8',
  },
    avatarImage: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block',
  },
  avatarPreview: {
    width: '140px',
    height: '140px',
    borderRadius: '50%',
    overflow: 'hidden',
    border: '3px solid #2A3441',
    position: 'relative',
  },
  spinnerSmall: {
    width: '24px',
    height: '24px',
    border: '3px solid #2A3441',
    borderTopColor: '#4A6CF7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  emptyState: {
    textAlign: 'center',
    padding: '80px 20px',
  },
  emptyStateIcon: {
    fontSize: '52px',
    marginBottom: '16px',
  },
  emptyStateTitle: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '8px',
  },
  emptyStateText: {
    fontSize: '15px',
    color: '#94A3B8',
    marginBottom: '28px',
    maxWidth: '340px',
    marginLeft: 'auto',
    marginRight: 'auto',
  },
  emptyStateButton: {
    padding: '12px 28px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: 500,
    cursor: 'pointer',
    color: 'white',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '20px',
    marginTop: '32px',
  },
  pageButton: {
    padding: '10px 20px',
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '8px',
    fontSize: '14px',
    cursor: 'pointer',
    color: '#E2E8F0',
  },
  pageButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  pageInfo: {
    fontSize: '15px',
    color: '#94A3B8',
  },
};

export default ProfilePage;