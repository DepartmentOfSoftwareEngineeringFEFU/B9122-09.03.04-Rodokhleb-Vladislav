import axios from 'axios';

const API_URL = '/api/v1/videos';

class VideoService {
  async getUserVideos(page = 1, size = 50) {
    const response = await axios.get(`${API_URL}/`, {
      params: { page, size }
    });
    return response.data;
  }

  async getVideo(videoId) {
    const response = await axios.get(`${API_URL}/${videoId}`);
    return response.data;
  }

  async getVideoUrl(videoId, expiresIn = 3600) {
    const response = await axios.get(`${API_URL}/${videoId}/url`, {
      params: { expires_in: expiresIn }
    });
    return response.data.url;
  }

  async uploadVideo(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async deleteVideo(videoId) {
    const response = await axios.delete(`${API_URL}/${videoId}`);
    return response.data;
  }

  async getVideoInfo(videoId) {
    const response = await axios.get(`${API_URL}/${videoId}/info`);
    return response.data;
  }
}

export default new VideoService();