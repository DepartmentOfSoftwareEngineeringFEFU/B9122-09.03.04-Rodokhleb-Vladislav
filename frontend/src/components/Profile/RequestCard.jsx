import React from 'react';
import { useNavigate } from 'react-router-dom';

const RequestCard = ({ request }) => {
  const navigate = useNavigate();

  const getKeywords = () => {
    if (!request.keywords) return [];

    if (typeof request.keywords === 'object' && !Array.isArray(request.keywords)) {
      return Object.values(request.keywords);
    }

    if (Array.isArray(request.keywords)) {
      return request.keywords;
    }

    if (typeof request.keywords === 'string') {
      try {
        const parsed = JSON.parse(request.keywords);
        if (typeof parsed === 'object' && !Array.isArray(parsed)) {
          return Object.values(parsed);
        }
        if (Array.isArray(parsed)) {
          return parsed;
        }
        return [parsed];
      } catch {
        return [request.keywords];
      }
    }

    return [];
  };

  const keywords = getKeywords();
  const statusColors = {
    pending: { color: '#6B7280', bg: 'rgba(107, 114, 128, 0.1)', text: 'Ожидает' },
    processing: { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)', text: 'В обработке' },
    completed: { color: '#10B981', bg: 'rgba(16, 185, 129, 0.1)', text: 'Завершен' },
    error: { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)', text: 'Ошибка' },
  };

  const statusInfo = statusColors[request.status] || statusColors.pending;

  const handleViewResults = () => {
    if (request.status === 'completed') {
      navigate(`/analysis/${request.id}`);
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <div style={styles.id}>Запрос № {request.id}</div>
        <div style={{ ...styles.status, background: statusInfo.bg, color: statusInfo.color }}>
          {statusInfo.text}
        </div>
      </div>

      <div style={styles.content}>
        <div style={styles.infoRow}>
          <span style={styles.label}>Идентификатор видео:</span>
          <span style={styles.label_value}> {request.video_id}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.label}>Ключевые слова:</span>
          <div style={styles.keywordsContainer}>
            {keywords.length > 0 ? (
              keywords.map((kw, idx) => (
                <span key={idx} style={styles.keywordTag}>{kw}</span>
              ))
            ) : (
              <span style={styles.noKeywords}>Нет ключевых слов</span>
            )}
          </div>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.label}>Создан:</span>
          <span style={styles.value}>
            {new Date(request.created_at).toLocaleString('ru-RU', {
              day: '2-digit',
              month: 'long',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        </div>
        {request.completed_at && (
          <div style={styles.infoRow}>
            <span style={styles.label}>Завершен:</span>
            <span style={styles.value}>
              {new Date(request.completed_at).toLocaleString('ru-RU', {
                day: '2-digit',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
        )}
      </div>

      {request.status === 'completed' && (
        <button style={styles.viewButton} onClick={handleViewResults}>
          Посмотреть результаты
        </button>
      )}
    </div>
  );
};

const styles = {
  card: {
    background: '#161B26',
    border: '1px solid #2A3441',
    borderRadius: '16px',
    padding: '24px',
    transition: 'all 0.2s ease',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  },
  id: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#E2E8F0',
  },
  status: {
    padding: '4px 14px',
    borderRadius: '20px',
    fontSize: '18px',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  content: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    flex: 1,
  },
  infoRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    fontSize: '14px',
  },
  label: {
    color: '#94A3B8',
    fontWeight: 500,
    minWidth: '120px',
    flexShrink: 0,
    fontSize: '18px',
  },
  label_value:{
      fontSize: '18px',
      fontWeight: 500,
  },
  value: {
    color: '#E2E8F0',
    wordBreak: 'break-word',
    fontSize: '18px',
  },
  keywordsContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    flex: 1,
  },
  keywordTag: {
    padding: '2px 12px',
    background: 'rgba(74, 108, 247, 0.15)',
    color: '#4A6CF7',
    borderRadius: '16px',
    fontSize: '18px',
    fontWeight: 500,
  },
  noKeywords: {
    color: '#6B7280',
    fontSize: '18px',
  },
  viewButton: {
    padding: '10px 20px',
    background: '#4A6CF7',
    border: 'none',
    borderRadius: '10px',
    fontSize: '18px',
    fontWeight: 600,
    color: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    marginTop: '4px',
    '&:hover': {
      background: '#3B5DE7',
      transform: 'translateY(-1px)',
    },
  },
};

export default RequestCard;