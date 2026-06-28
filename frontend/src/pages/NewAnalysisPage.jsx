import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar/Navbar';
import videoService from '../services/videoService';
import analysisService from '../services/analysisService';

const NewAnalysisPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialVideoId = searchParams.get('videoId');

  const [videos, setVideos] = useState([]);
  const [selectedVideoId, setSelectedVideoId] = useState('');
  const [keywords, setKeywords] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [analysisStarted, setAnalysisStarted] = useState(false);
  const [requestId, setRequestId] = useState(null);
  const [status, setStatus] = useState(null);
  const [fps, setFps] = useState(5);
  const [confidence, setConfidence] = useState(0.4);

  const fetchVideos = async () => {
    try {
      setLoadingVideos(true);
      const response = await videoService.getUserVideos(1, 100);
      setVideos(response.items || []);
      if (response.items && response.items.length > 0 && !selectedVideoId) {
        setSelectedVideoId(response.items[0].id);
      }
    } catch (err) {
      console.error('Error fetching videos:', err);
      setError('Не удалось загрузить список видео');
    } finally {
      setLoadingVideos(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

    useEffect(() => {
    if (initialVideoId && videos.length > 0) {
      const videoExists = videos.find(v => v.id.toString() === initialVideoId);
      if (videoExists) {
        setSelectedVideoId(videoExists.id);
      }
    }
  }, [videos, initialVideoId]);

  useEffect(() => {
    if (!analysisStarted || !requestId) return;

    const checkStatus = async () => {
      try {
        const statusData = await analysisService.getStatus(requestId);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          navigate(`/analysis/${requestId}`);
        } else if (statusData.status === 'error') {
          setError(statusData.error_message || 'Ошибка при выполнении анализа');
          setAnalysisStarted(false);
        }
      } catch (err) {
        console.error('Error checking status:', err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, [analysisStarted, requestId, navigate]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const result = await videoService.uploadVideo(file);
      await fetchVideos();
      setSelectedVideoId(result.video_id);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при загрузке видео');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');
  setLoading(true);

  let keywordsList = [];

  if (keywords.includes('\n')) {
    keywordsList = keywords.split('\n')
      .map(k => k.trim())
      .filter(k => k.length > 0);
  }

  else if (keywords.includes(',')) {
    keywordsList = keywords.split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);
  }

  else {
    keywordsList = [keywords.trim()];
  }

  if (keywordsList.length === 0) {
    setError('Введите хотя бы одно ключевое слово');
    setLoading(false);
    return;
  }

  if (!selectedVideoId) {
    setError('Выберите видео для анализа');
    setLoading(false);
    return;
  }

  try {
    const result = await analysisService.startAnalysis(
      selectedVideoId,
      keywordsList,
      fps,
      confidence
    );
    setRequestId(result.request_id);
    setAnalysisStarted(true);
  } catch (err) {
    setError(err.response?.data?.detail || 'Ошибка при запуске анализа');
  } finally {
    setLoading(false);
  }
};

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (analysisStarted) {
    const progressPercent = status ? Math.round((status.progress || 0) * 100) : 0;

    return (
      <div style={styles.container}>
        <Navbar />
        <div style={styles.content}>
          <div style={styles.statusCard}>
            <div style={styles.statusIcon}>🔍</div>
            <h2 style={styles.statusTitle}>Анализ видео запущен</h2>
            <p style={styles.statusText}>
              Пожалуйста, подождите. Анализ может занять несколько минут.
            </p>

            <div style={styles.progressContainer}>
              <div style={styles.progressBar}>
                <div style={{ ...styles.progressFill, width: `${progressPercent}%` }} />
              </div>
              <div style={styles.progressText}>{progressPercent}%</div>
            </div>

            {status?.status === 'processing' && (
              <div style={styles.statusBadge}>Обработка...</div>
            )}

            {status?.status === 'error' && (
              <div style={{ ...styles.statusBadge, ...styles.statusBadgeError }}>
                Ошибка: {status.error_message}
              </div>
            )}

            <button
              style={styles.cancelButton}
              onClick={() => navigate('/profile')}
            >
              Вернуться в профиль
            </button>
          </div>
        </div>
      </div>
    );
  }

    return (
    <div style={styles.container}>
      <Navbar />

      <div style={styles.content}>
        <div style={styles.header}>
          <h1 style={styles.title}>Новый анализ видеоряда</h1>
          <p style={styles.subtitle}>
            Выберите видео и задайте ключевые слова для поиска объектов
          </p>
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Выберите видео</h2>

          {loadingVideos ? (
            <div style={styles.loadingVideos}>
              <div style={styles.spinnerSmall}></div>
              <span>Загрузка видео...</span>
            </div>
          ) : videos.length === 0 ? (
            <div style={styles.emptyVideos}>
              <div style={styles.emptyIcon}>🎬</div>
              <div style={styles.emptyTitle}>Нет загруженных видео</div>
              <div style={styles.emptyText}>
                Загрузите видео, чтобы начать анализ
              </div>
              <label style={styles.uploadButton}>
                <input
                  type="file"
                  accept="video/mp4,video/avi,video/mov,video/mkv,video/webm"
                  onChange={handleFileUpload}
                  style={styles.hiddenInput}
                  disabled={uploading}
                />
                {uploading ? 'Загрузка...' : '📤 Загрузить видео'}
              </label>
            </div>
          ) : (
            <>
              <div style={styles.videoList}>
                {videos.map((video) => (
                  <div
                    key={video.id}
                    style={{
                      ...styles.videoItem,
                      ...(selectedVideoId === video.id ? styles.videoItemSelected : {})
                    }}
                    onClick={() => setSelectedVideoId(video.id)}
                  >
                    <div style={styles.videoItemIcon}></div>
                    <div style={styles.videoItemInfo}>
                      <div style={styles.videoItemName}>{video.filename}</div>
                      <div style={styles.videoItemMeta}>
                        Размер: {formatFileSize(video.file_size)}
                      </div>
                      <div style={styles.videoItemMeta}>
                        Продолжительность: {formatDuration(video.duration)} мин.
                      </div>
                    </div>
                    {selectedVideoId === video.id && (
                      <div style={styles.videoItemCheck}>✓</div>
                    )}
                  </div>
                ))}
              </div>

              <div style={styles.uploadNewContainer}>
                <label style={styles.uploadNewButton}>
                  <input
                    type="file"
                    accept="video/mp4,video/avi,video/mov,video/mkv,video/webm"
                    onChange={handleFileUpload}
                    style={styles.hiddenInput}
                    disabled={uploading}
                  />
                  {uploading ? '⏳ Загрузка...' : '+ Загрузить видео'}
                </label>
              </div>
            </>
          )}
        </div>

        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Параметры анализа</h2>

          <form onSubmit={handleSubmit}>
            <div style={styles.field}>
              <label style={styles.label}>
                Ключевые слова
                <span style={styles.required}>*</span>
              </label>
              <textarea
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                style={styles.textarea}
                placeholder="Введите ключевые слова (каждое с новой строки или через запятую)"
                rows={6}
                required
              />
              <span style={styles.hint}>
                Модель будет искать эти объекты в видео
              </span>
            </div>

            <div style={styles.field}>
              <label style={styles.label}>
                Количество кадров в секунду (FPS)
                <span style={styles.valueDisplay}>{fps} fps</span>
              </label>
              <input
                type="range"
                min="5"
                max="30"
                step="1"
                value={fps}
                onChange={(e) => setFps(parseInt(e.target.value))}
                style={styles.slider}
              />
              <span style={styles.hint}>
                Число кадров, анализируемое в 1 секунде видеофайла
              </span>
            </div>



            {error && (
              <div style={styles.errorMessage}>{error}</div>
            )}

            <button
              type="submit"
              disabled={loading || videos.length === 0}
              style={styles.submitButton}
            >
              {loading ? 'Запуск анализа...' : 'Запустить анализ'}
            </button>
          </form>
        </div>

        <div style={styles.infoCard}>
          <h3 style={styles.infoCardTitle}>Советы по анализу видеоряда:</h3>
          <ul style={styles.infoList}>
            <li>Используйте существительные на русском языке: <code>человек, машина, море</code></li>
            <li>Для описания обьекта можно использовать прилагательные: <code>красная машина, рыжеволосый человек, белая кошка</code></li>
            <li>Вводите ключевые слова для поиска в нижнем регистре</li>
          </ul>
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
  content: {
    padding: '32px 5%',
    maxWidth: '1200px',
    margin: '0 auto',
    width: '100%',
  },
  header: {
    marginBottom: '32px',
  },
  title: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#E2E8F0',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '16px',
    color: '#94A3B8',
  },

  card: {
    width: '100%',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '24px',
    boxSizing: 'border-box',
  },
  cardTitle: {
    fontSize: '25px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '20px',
  },
  videoList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    maxHeight: '350px',
    overflowY: 'auto',
    marginBottom: '16px',
  },
  videoItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    background: '#1E2533',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    border: '1px solid transparent',
  },
  videoItemSelected: {
    borderColor: '#4A6CF7',
    background: 'rgba(74, 108, 247, 0.1)',
  },
  videoItemIcon: {
    fontSize: '24px',
  },
  videoItemInfo: {
    flex: 1,
  },
  videoItemName: {
    fontSize: '24px',
    fontWeight: 500,
    color: '#E2E8F0',
    marginBottom: '4px',
    wordBreak: 'break-word',
  },
  videoItemMeta: {
    fontSize: '18px',
    color: '#94A3B8',
  },
  videoItemCheck: {
    width: '24px',
    height: '24px',
    borderRadius: '12px',
    background: '#4A6CF7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '14px',
  },
  uploadNewContainer: {
    borderTop: '1px solid #2A3441',
    paddingTop: '16px',
    marginTop: '4px',
  },
  uploadNewButton: {
    display: 'block',
    width: '100%',
    padding: '12px',
    background: '#1E2533',
    border: '1px dashed #2A3441',
    borderRadius: '10px',
    fontSize: '20px',
    fontWeight: 500,
    cursor: 'pointer',
    color: '#4A6CF7',
    textAlign: 'center',
    transition: 'all 0.2s',
  },
  uploadButton: {
    display: 'inline-block',
    padding: '12px 24px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    color: 'white',
    textAlign: 'center',
  },
  hiddenInput: {
    display: 'none',
  },
  field: {
    marginBottom: '24px',
  },
  label: {
    display: 'block',
    fontSize: '18px',
    fontWeight: 500,
    color: '#E2E8F0',
    marginBottom: '8px',
  },
  required: {
    color: '#EF4444',
    marginLeft: '4px',
  },
  textarea: {
    width: '100%',
    padding: '12px 16px',
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '10px',
    fontSize: '14px',
    color: '#E2E8F0',
    resize: 'vertical',
    fontFamily: 'monospace',
    boxSizing: 'border-box',
  },
  checkbox: {
    marginRight: '8px',
    transform: 'scale(1.1)',
    cursor: 'pointer',
  },
  hint: {
    display: 'block',
    fontSize: '16px',
    color: '#6B7280',
    marginTop: '6px',
  },
  errorMessage: {
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '10px',
    color: '#EF4444',
    fontSize: '14px',
    marginBottom: '20px',
  },
  submitButton: {
    width: '100%',
    padding: '14px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '22px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
    transition: 'background 0.2s',
  },
  infoCard: {
    width: '100%',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '20px 24px',
    marginTop: '0',
    boxSizing: 'border-box',
  },
  infoCardTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '12px',
  },
  infoList: {
    margin: 0,
    paddingLeft: '20px',
    color: '#94A3B8',
    fontSize: '16px',
    lineHeight: 1.6,
  },
  loadingVideos: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: '40px',
    color: '#94A3B8',
  },
  spinnerSmall: {
    width: '20px',
    height: '20px',
    border: '2px solid #2A3441',
    borderTopColor: '#4A6CF7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  emptyVideos: {
    textAlign: 'center',
    padding: '40px 20px',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '14px',
    color: '#94A3B8',
    marginBottom: '20px',
  },
  statusCard: {
    maxWidth: '500px',
    margin: '0 auto',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '40px',
    textAlign: 'center',
  },
  statusIcon: {
    fontSize: '64px',
    marginBottom: '20px',
  },
  statusTitle: {
    fontSize: '24px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '12px',
  },
  statusText: {
    fontSize: '14px',
    color: '#94A3B8',
    marginBottom: '24px',
  },
  progressContainer: {
    marginBottom: '24px',
  },
  progressBar: {
    height: '8px',
    background: '#2A3441',
    borderRadius: '4px',
    overflow: 'hidden',
    marginBottom: '8px',
  },
  progressFill: {
    height: '100%',
    background: '#4A6CF7',
    borderRadius: '4px',
    transition: 'width 0.3s',
  },
  progressText: {
    fontSize: '14px',
    color: '#94A3B8',
  },
  statusBadge: {
    display: 'inline-block',
    padding: '8px 16px',
    background: 'rgba(245, 158, 11, 0.1)',
    border: '1px solid rgba(245, 158, 11, 0.3)',
    borderRadius: '20px',
    fontSize: '14px',
    color: '#F59E0B',
    marginBottom: '24px',
  },
  statusBadgeError: {
    background: 'rgba(239, 68, 68, 0.1)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
    color: '#EF4444',
  },
  cancelButton: {
    padding: '12px 24px',
    background: 'transparent',
    border: '1px solid #2A3441',
    borderRadius: '10px',
    fontSize: '14px',
    cursor: 'pointer',
    color: '#94A3B8',
  },
    slider: {
      width: '100%',
      height: '6px',
      borderRadius: '3px',
      background: '#2A3441',
      outline: 'none',
      WebkitAppearance: 'none',
      cursor: 'pointer',
      margin: '10px 0 6px 0',
    },
    valueDisplay: {
      float: 'right',
      color: '#4A6CF7',
      fontWeight: 600,
      fontSize: '14px',
    },
};

export default NewAnalysisPage;