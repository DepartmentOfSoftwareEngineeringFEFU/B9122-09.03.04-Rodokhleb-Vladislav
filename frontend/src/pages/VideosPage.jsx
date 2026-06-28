import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Navbar from '../components/Navbar/Navbar';
import videoService from '../services/videoService';

const VideosPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [videos, setVideos] = useState([]);
  const [videoUrls, setVideoUrls] = useState({});
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const [selectedVideo, setSelectedVideo] = useState(null);
  const [playerUrl, setPlayerUrl] = useState(null);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const response = await videoService.getUserVideos(1, 100);
      const videosList = response.items || [];
      setVideos(videosList);

      const urls = {};
      await Promise.all(videosList.map(async (v) => {
        try {
          urls[v.id] = await videoService.getVideoUrl(v.id);
        } catch (err) {
          console.error(`Failed to get URL for video ${v.id}`, err);
        }
      }));
      setVideoUrls(urls);

    } catch (err) {
      console.error('Error fetching videos:', err);
      setError('Не удалось загрузить список видео');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError('');
    try {
      await videoService.uploadVideo(file);
      await fetchVideos();
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при загрузке видео');
    } finally {
      setUploading(false);
      e.target.value = null;
    }
  };

  const handleDelete = async (e, videoId, filename) => {
    e.stopPropagation();
    if (window.confirm(`Вы уверены, что хотите удалить видео "${filename}"?`)) {
      try {
        await videoService.deleteVideo(videoId);
        setVideos(videos.filter(v => v.id !== videoId));
        setVideoUrls(prev => {
          const newUrls = { ...prev };
          delete newUrls[videoId];
          return newUrls;
        });
      } catch (err) {
        alert('Ошибка при удалении видео');
      }
    }
  };

  const handleVideoClick = async (video) => {
    setSelectedVideo(video);
    if (videoUrls[video.id]) {
      setPlayerUrl(videoUrls[video.id]);
    } else {
      try {
        const url = await videoService.getVideoUrl(video.id);
        setPlayerUrl(url);
        setVideoUrls(prev => ({ ...prev, [video.id]: url }));
      } catch (err) {
        console.error(err);
      }
    }
  };

  const closeModal = () => {
    setSelectedVideo(null);
    setPlayerUrl(null);
  };

  const handleAnalyze = (e, videoId) => {
    e.stopPropagation();
    navigate(`/analysis/new?videoId=${videoId}`);
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

  return (
    <div style={styles.container}>
      <Navbar />

      <div style={styles.mainContent}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>Список видео пользователя</h1>
            <p style={styles.subtitle}>Нажмите на видео, чтобы просмотреть его</p>
          </div>
          <label style={styles.uploadButton}>
            <input type="file" accept="video/mp4,video/avi,video/mov,video/mkv,video/webm" onChange={handleFileUpload} style={styles.hiddenInput} disabled={uploading} />
            {uploading ? 'Загрузка...' : 'Загрузить видео'}
          </label>
        </div>

        {error && <div style={styles.errorMessage}>{error}</div>}

        {loading ? (
          <div style={styles.loadingContainer}>
            <div style={styles.spinner}></div>
            <span>Загрузка видео...</span>
          </div>
        ) : videos.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🎞️</div>
            <h2 style={styles.emptyTitle}>У вас пока нет видео</h2>
            <label style={styles.emptyUploadButton}>
              <input type="file" accept="video/mp4,video/avi,video/mov,video/mkv,video/webm" onChange={handleFileUpload} style={styles.hiddenInput} disabled={uploading} />
              {uploading ? 'Загрузка...' : '📤 Выбрать файл'}
            </label>
          </div>
        ) : (
          <div style={styles.videoGrid}>
            {videos.map((video) => (
              <div
                key={video.id}
                style={styles.videoCard}
                onClick={() => handleVideoClick(video)}
              >
                <div style={styles.thumbnailContainer}>
                  {videoUrls[video.id] ? (
                    <video
                      src={videoUrls[video.id]}
                      preload="metadata"
                      style={styles.thumbnailVideo}
                      muted
                    />
                  ) : (
                    <div style={styles.thumbnailPlaceholder}>🎥</div>
                  )}
                  <div style={styles.playOverlay}>▶</div>
                </div>

                <div style={styles.cardBody}>
                  <div style={styles.videoName} title={video.filename}>
                    {video.filename}
                  </div>
                  <div style={styles.videoMeta}>
                    Размер: {formatFileSize(video.file_size)}
                  </div>
                  <div style={styles.videoMeta}>
                    Продолжительность: {formatDuration(video.duration)} мин.
                  </div>
                </div>

                <div style={styles.cardActions}>
                  <button
                    style={styles.analyzeButton}
                    onClick={(e) => handleAnalyze(e, video.id)}
                  >
                    Анализ
                  </button>
                  <button
                    style={styles.deleteButton}
                    onClick={(e) => handleDelete(e, video.id, video.filename)}
                    title="Удалить видео"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedVideo && (
        <div style={styles.modalOverlay} onClick={closeModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <button style={styles.closeButton} onClick={closeModal}>✕</button>

            <video
              src={playerUrl}
              controls
              autoPlay
              style={styles.modalVideo}
            />

            <div style={styles.modalInfo}>
              <h3 style={styles.modalTitle}>{selectedVideo.filename}</h3>
              <div style={styles.modalMeta}>
                 Размер: {formatFileSize(selectedVideo.file_size)}
              </div>
              <div style={styles.modalMeta}>
                Продолжительность: {formatDuration(selectedVideo.duration)} мин.
              </div>

              <button
                style={styles.modalAnalyzeBtn}
                onClick={() => { closeModal(); navigate(`/analysis/new?videoId=${selectedVideo.id}`); }}
              >
                Анализ видео
              </button>
            </div>
          </div>
        </div>
      )}
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '32px',
    flexWrap: 'wrap',
    gap: '16px',
  },
  title: {
    fontSize: '35px',
    fontWeight: 700,
    color: '#E2E8F0',
    margin: '0 0 8px 0',
  },
  subtitle: {
    fontSize: '18px',
    color: '#94A3B8',
    margin: 0,
  },
  uploadButton: {
    padding: '12px 24px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '18px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
    display: 'inline-block',
  },
  hiddenInput: {
    display: 'none',
  },
  errorMessage: {
    padding: '12px 16px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '10px',
    color: '#EF4444',
    fontSize: '14px',
    marginBottom: '24px',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    padding: '80px 0',
    color: '#94A3B8',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid #2A3441',
    borderTopColor: '#4A6CF7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  emptyState: {
    textAlign: 'center',
    padding: '80px 20px',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  emptyTitle: {
    fontSize: '22px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '24px',
  },
  emptyUploadButton: {
    padding: '12px 28px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: 500,
    cursor: 'pointer',
    color: 'white',
    display: 'inline-block',
  },
  videoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
    gap: '24px',
  },
  videoCard: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    overflow: 'hidden',
    transition: 'transform 0.2s, border-color 0.2s',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
  },
  videoCardHover: {
    transform: 'translateY(-4px)',
    borderColor: '#4A6CF7',
  },
  thumbnailContainer: {
    position: 'relative',
    width: '100%',
    aspectRatio: '16/9',
    background: '#1E2533',
    overflow: 'hidden',
  },
  thumbnailVideo: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  thumbnailPlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '48px',
    color: '#4A6CF7',
  },
  playOverlay: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '56px',
    height: '56px',
    background: 'rgba(74, 108, 247, 0.85)',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '20px',
    opacity: 0,
    transition: 'opacity 0.2s',
  },
  cardBody: {
    padding: '16px 20px 12px',
  },
  videoName: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#E2E8F0',
    marginBottom: '6px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  videoMeta: {
    fontSize: '15px',
    color: '#94A3B8',
  },
  cardActions: {
    display: 'flex',
    gap: '12px',
    padding: '0 20px 20px',
    marginTop: 'auto',
  },
  analyzeButton: {
    flex: 1,
    padding: '10px 16px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '8px',
    fontSize: '18px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
  },
  deleteButton: {
    padding: '10px 14px',
    background: 'transparent',
    border: '1px solid #2A3441',
    borderRadius: '8px',
    fontSize: '18px',
    cursor: 'pointer',
    color: '#EF4444',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '20px',
  },
  modalContent: {
    background: '#161B26',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '900px',
    overflow: 'hidden',
    position: 'relative',
    border: '1px solid #2A3441',
    boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
  },
  closeButton: {
    position: 'absolute',
    top: '16px',
    right: '16px',
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    background: 'rgba(0,0,0,0.6)',
    border: 'none',
    color: 'white',
    fontSize: '18px',
    cursor: 'pointer',
    zIndex: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalVideo: {
    width: '100%',
    maxHeight: '70vh',
    background: '#000',
    display: 'block',
  },
  modalInfo: {
    padding: '24px',
  },
  modalTitle: {
    fontSize: '22px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: '0 0 12px 0',
    wordBreak: 'break-word',
  },
  modalMeta: {
    display: 'flex',
    gap: '20px',
    fontSize: '18px',
    color: '#94A3B8',
    marginBottom: '15px',
  },
  modalAnalyzeBtn: {
    padding: '12px 24px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '25px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
    width: '100%',
  },
};

export default VideosPage;