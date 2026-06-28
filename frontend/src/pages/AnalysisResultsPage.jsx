import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar/Navbar';
import analysisService from '../services/analysisService';
import videoService from '../services/videoService';

const AnalysisResultsPage = () => {
  const { requestId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusData, setStatusData] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);

  const [keywords, setKeywords] = useState([]);
  const [fragments, setFragments] = useState([]);
  const [fragmentUrls, setFragmentUrls] = useState({});
  const [totalFragments, setTotalFragments] = useState(0);
  const [videoId, setVideoId] = useState(null);
  const [translationMap, setTranslationMap] = useState({});

  const fetchData = async () => {
    try {
      if (!statusData) setLoading(true);

      const status = await analysisService.getStatus(requestId);
      setStatusData(status);

      if (status.status === 'completed') {
        const fragmentsData = await analysisService.getFragmentUrls(requestId);

        const tMap = fragmentsData.translation_map || {};
        setTranslationMap(tMap);
        const englishKeywords = Object.keys(tMap);
        setKeywords(englishKeywords);

        const allFragments = fragmentsData.fragments || [];
        setFragments(allFragments);

        const urlMap = {};
        allFragments.forEach(f => {
          urlMap[f.id] = f.url;
        });
        setFragmentUrls(urlMap);
        setTotalFragments(allFragments.length);

        try {
          const resultsData = await analysisService.getResults(requestId);
          if (resultsData && resultsData.video_id) {
            setVideoId(resultsData.video_id);
            const vUrl = await videoService.getVideoUrl(resultsData.video_id);
            setVideoUrl(vUrl);
          }
        } catch (e) {
          console.warn('Could not load original video URL:', e);
        }
      }

      setError('');
    } catch (err) {
      console.error('Error fetching analysis data:', err);
      setError('Не удалось загрузить результаты анализа');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [requestId]);

  useEffect(() => {
    if (!statusData) return;
    const isFinished = statusData.status === 'completed' || statusData.status === 'error';
    if (!isFinished) {
      const interval = setInterval(fetchData, 3000);
      return () => clearInterval(interval);
    }
  }, [statusData]);

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit', month: 'long', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const handleDownloadFragment = (url, filename) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.target = '_blank';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadAll = () => {
    Object.entries(fragmentUrls).forEach(([id, url], index) => {
      setTimeout(() => {
        handleDownloadFragment(url, `fragment_${id}.mp4`);
      }, index * 500);
    });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed': return { text: 'Завершен', color: '#10B981', bg: 'rgba(16, 185, 129, 0.1)' };
      case 'processing': return { text: 'В обработке', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)' };
      case 'pending': return { text: 'Ожидает', color: '#6B7280', bg: 'rgba(107, 114, 128, 0.1)' };
      case 'error': return { text: 'Ошибка', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)' };
      default: return { text: status, color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.1)' };
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <Navbar />
        <div style={styles.loadingContainer}>
          <div style={styles.spinner}></div>
          <span>Загрузка результатов...</span>
        </div>
      </div>
    );
  }

  if (statusData && statusData.status !== 'completed' && statusData.status !== 'error') {
    const progressPercent = Math.round((statusData.progress || 0) * 100);
    const statusBadge = getStatusBadge(statusData.status);

    return (
      <div style={styles.container}>
        <Navbar />
        <div style={styles.mainContent}>
          <button style={styles.backButton} onClick={() => navigate('/profile')}>
            ← Назад к запросам
          </button>
          <div style={styles.processingCard}>
            <div style={styles.processingIcon}>🔍</div>
            <h2 style={styles.processingTitle}>Результат анализа номер {requestId}</h2>
            <div style={{ ...styles.statusBadge, background: statusBadge.bg, color: statusBadge.color }}>
              {statusBadge.text}
            </div>
            <p style={styles.processingText}>Анализ видео выполняется. Пожалуйста, подождите...</p>
            <div style={styles.progressContainer}>
              <div style={styles.progressBar}>
                <div style={{ ...styles.progressFill, width: `${progressPercent}%` }}></div>
              </div>
              <span style={styles.progressText}>{progressPercent}%</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (statusData && statusData.status === 'error') {
    return (
      <div style={styles.container}>
        <Navbar />
        <div style={styles.mainContent}>
          <button style={styles.backButton} onClick={() => navigate('/profile')}>
            ← Назад к запросам
          </button>
          <div style={styles.errorCard}>
            <div style={styles.errorIcon}></div>
            <h2 style={styles.errorTitle}>Результат анализа номер {requestId}</h2>
            <p style={styles.errorText}>Произошла ошибка при выполнении анализа</p>
            {statusData.error_message && (
              <div style={styles.errorDetail}>{statusData.error_message}</div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Navbar />
      <div style={styles.mainContent}>
        <button style={styles.backButton} onClick={() => navigate('/profile')}>
          ← Назад к запросам
        </button>

        <h1 style={styles.pageTitle}>Результат анализа № {requestId}</h1>

        {videoUrl && (
          <div style={styles.videoSection}>
            <h2 style={styles.sectionTitle}>Исходное видео</h2>
            <div style={styles.videoPlayerContainer}>
              <video src={videoUrl} controls preload="metadata" style={styles.videoPlayer} />
            </div>
          </div>
        )}

        <div style={styles.metadataCard}>
          <h2 style={styles.sectionTitle}>Информация об анализе</h2>
          <div style={styles.metadataGrid}>
            <div style={styles.metadataItem}>
              <span style={styles.metadataLabel}>Дата начала анализа:</span>
              <span style={styles.metadataValue}>{formatDate(statusData?.created_at)}</span>
            </div>
            <div style={styles.metadataItem}>
              <span style={styles.metadataLabel}>Дата завершения анализа:</span>
              <span style={styles.metadataValue}>{formatDate(statusData?.completed_at)}</span>
            </div>
            <div style={styles.metadataItem}>
              <span style={styles.metadataLabel}>Ключевые слова в анализе:</span>
              <div style={styles.keywordsList}>
                {keywords.map((kw, idx) => {

                  const displayName = translationMap[kw] || kw;
                  return (
                    <span key={idx} style={styles.keywordTag}>
                      {displayName}
                    </span>
                  );
                })}
              </div>
            </div>
            <div style={styles.metadataItem}>
              <span style={styles.metadataLabel}>Всего найдено фрагментов:</span>
              <span style={styles.metadataValueHighlight}>{totalFragments}</span>
            </div>
          </div>

          <div style={styles.summarySection}>
            <h3 style={styles.summaryTitle}>Найдено фрагментов по каждому ключевому слову</h3>
            <div style={styles.summaryGrid}>
              {keywords.map((engKw, idx) => {

                const count = fragments.filter(f => {
                  const fKeywords = f.keywords_en || [];
                  return fKeywords.includes(engKw);
                }).length;

                const displayName = translationMap[engKw] || engKw;

                return (
                  <div key={idx} style={styles.summaryItem}>
                    <span style={styles.summaryKeyword}>{displayName}</span>
                    <span style={count > 0 ? styles.summaryCount : styles.summaryCountZero}>
                      {count} фрагмент
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div style={styles.resultsSection}>
          <h2 style={styles.sectionTitle}>Найденные фрагменты</h2>

          {keywords.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}></div>
              <h3 style={styles.emptyTitle}>Ключевые слова не указаны</h3>
            </div>
          ) : (
            keywords.map((engKw, kwIdx) => {

              const frags = fragments.filter(f => {
                const fKeywords = f.keywords_en || [];
                return fKeywords.includes(engKw);
              });

              const displayName = translationMap[engKw] || engKw;

              return (
                <div key={kwIdx} style={styles.keywordSection}>
                  <div style={styles.keywordHeader}>
                    <h3 style={styles.keywordTitle}>
                      Ключевое слово «{displayName}»
                      <span style={styles.keywordCount}>
                        ({frags.length} {frags.length === 1 ? 'фрагмент' : 'фрагментов'})
                      </span>
                    </h3>
                  </div>

                  {frags.length === 0 ? (
                    <div style={styles.noFragments}>

                      <span>Фрагментов со словом «{displayName}» не найдено</span>
                    </div>
                  ) : (
                    <div style={styles.fragmentsList}>
                      {frags.map((frag) => {
                        const url = fragmentUrls[frag.id] || frag.url;
                        return (
                          <div key={frag.id} style={styles.fragmentCard}>
                            <div style={styles.fragmentVideoContainer}>
                              {url ? (
                                <video src={url} controls preload="metadata" style={styles.fragmentVideo} />
                              ) : (
                                <div style={styles.fragmentVideoPlaceholder}>Загрузка видео...</div>
                              )}
                            </div>
                            <div style={styles.fragmentInfo}>

                              {url && (
                                <button
                                  style={styles.downloadButton}
                                  onClick={() => handleDownloadFragment(url, `fragment_${engKw}_${frag.id}.mp4`)}
                                >
                                  ⬇ Скачать фрагмент
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {totalFragments > 0 && Object.keys(fragmentUrls).length > 0 && (
          <div style={styles.downloadAllSection}>
            <button style={styles.downloadAllButton} onClick={handleDownloadAll}>
              ⬇ Скачать все фрагменты ({totalFragments})
            </button>
          </div>
        )}
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
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    padding: '100px 0',
    color: '#94A3B8',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid #2A3441',
    borderTopColor: '#4A6CF7',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  backButton: {
    background: 'none',
    border: 'none',
    color: '#4A6CF7',
    fontSize: '15px',
    cursor: 'pointer',
    padding: '0 0 16px 0',
    fontWeight: 500,
  },
  pageTitle: {
    fontSize: '36px',
    fontWeight: 700,
    color: '#E2E8F0',
    marginBottom: '32px',
  },
  sectionTitle: {
    fontSize: '25px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: '0 0 20px 0',
  },
  videoSection: { marginBottom: '32px' },
  videoPlayerContainer: {
    background: '#000',
    borderRadius: '16px',
    overflow: 'hidden',
    border: '1px solid #2A3441',
  },
  videoPlayer: { width: '100%', maxHeight: '500px', display: 'block' },
  metadataCard: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '28px',
    marginBottom: '32px',
  },
  metadataGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '20px',
    marginBottom: '24px',
  },
  metadataItem: { display: 'flex', flexDirection: 'column', gap: '6px' },
  metadataLabel: { fontSize: '18px', color: '#94A3B8', fontWeight: 500 },
  metadataValue: { fontSize: '18px', color: '#E2E8F0', fontWeight: 500 },
  metadataValueHighlight: { fontSize: '24px', color: '#4A6CF7', fontWeight: 700 },
  keywordsList: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  keywordTag: {
    padding: '4px 14px',
    background: 'rgba(74, 108, 247, 0.15)',
    color: '#4A6CF7',
    borderRadius: '20px',
    fontSize: '18px',
    fontWeight: 600,
  },
  summarySection: { borderTop: '1px solid #2A3441', paddingTop: '20px' },
  summaryTitle: { fontSize: '24px', fontWeight: 600, color: '#E2E8F0', margin: '0 0 12px 0' },
  summaryGrid: { display: 'flex', flexWrap: 'wrap', gap: '12px' },
  summaryItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    background: '#1E2533',
    borderRadius: '10px',
    border: '1px solid #2A3441',
  },
  summaryKeyword: { fontSize: '18px', color: '#E2E8F0', fontWeight: 500 },
  summaryCount: {
    fontSize: '13px',
    color: '#10B981',
    fontWeight: 600,
    padding: '2px 8px',
    background: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '12px',
  },
  summaryCountZero: {
    fontSize: '13px',
    color: '#6B7280',
    fontWeight: 600,
    padding: '2px 8px',
    background: 'rgba(107, 114, 128, 0.1)',
    borderRadius: '12px',
  },
  resultsSection: { marginBottom: '32px' },
  keywordSection: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '20px',
  },
  keywordHeader: { marginBottom: '16px' },
  keywordTitle: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#E2E8F0',
    margin: 0,
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    flexWrap: 'wrap',
  },
  keywordCount: { fontSize: '18px', color: '#94A3B8', fontWeight: 400 },
  noFragments: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '24px',
    background: '#1E2533',
    borderRadius: '12px',
    color: '#6B7280',
    fontSize: '18px',
  },
  noFragmentsIcon: { fontSize: '24px' },
  fragmentsList: { display: 'flex', flexDirection: 'column', gap: '16px' },
  fragmentCard: {
    background: '#1E2533',
    border: '1px solid #2A3441',
    borderRadius: '12px',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  },
  fragmentVideoContainer: {
    width: '100%',
    aspectRatio: '16/9',
    background: '#000',
    position: 'relative',
  },
  fragmentVideo: { width: '100%', height: '100%', objectFit: 'contain', display: 'block' },
  fragmentVideoPlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#6B7280',
    fontSize: '14px',
  },
  fragmentInfo: {
    padding: '16px 20px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  },
  fragmentMeta: { display: 'flex', gap: '16px', flexWrap: 'wrap' },
  fragmentMetaItem: { fontSize: '18px', color: '#94A3B8' },
  downloadButton: {
    padding: '8px 18px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '8px',
    fontSize: '18px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
    whiteSpace: 'nowrap',

  },
  downloadAllSection: { textAlign: 'center', padding: '32px 0', borderTop: '1px solid #2A3441' },
  downloadAllButton: {
    padding: '16px 40px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '12px',
    fontSize: '18px',
    fontWeight: 600,
    cursor: 'pointer',
    color: 'white',
  },
  processingCard: {
    maxWidth: '500px',
    margin: '60px auto',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '40px',
    textAlign: 'center',
  },
  processingIcon: { fontSize: '64px', marginBottom: '20px' },
  processingTitle: { fontSize: '22px', fontWeight: 600, color: '#E2E8F0', marginBottom: '16px' },
  processingText: { fontSize: '14px', color: '#94A3B8', marginBottom: '24px' },
  statusBadge: {
    display: 'inline-block',
    padding: '6px 16px',
    borderRadius: '20px',
    fontSize: '13px',
    fontWeight: 600,
    marginBottom: '16px',
  },
  progressContainer: { display: 'flex', alignItems: 'center', gap: '12px' },
  progressBar: { flex: 1, height: '8px', background: '#2A3441', borderRadius: '4px', overflow: 'hidden' },
  progressFill: { height: '100%', background: '#4A6CF7', borderRadius: '4px', transition: 'width 0.5s ease' },
  progressText: { fontSize: '14px', color: '#E2E8F0', fontWeight: 600, minWidth: '40px' },
  errorCard: {
    maxWidth: '500px',
    margin: '60px auto',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '40px',
    textAlign: 'center',
  },
  errorIcon: { fontSize: '64px', marginBottom: '20px' },
  errorTitle: { fontSize: '22px', fontWeight: 600, color: '#E2E8F0', marginBottom: '12px' },
  errorText: { fontSize: '14px', color: '#94A3B8', marginBottom: '16px' },
  errorDetail: {
    padding: '12px 16px',
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '10px',
    color: '#EF4444',
    fontSize: '13px',
  },
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
  },
  emptyIcon: { fontSize: '48px', marginBottom: '12px' },
  emptyTitle: { fontSize: '18px', fontWeight: 600, color: '#E2E8F0' },
};

const styleSheet = document.createElement("style");
styleSheet.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);

export default AnalysisResultsPage;