import axios from 'axios';

const API_URL = '/api/v1/analysis';

class AnalysisService {
  async startAnalysis(videoId, keywords, fps = 2, confidence = 0.35) {
    const response = await axios.post(`${API_URL}/start`, {
      keywords: keywords,
      fps: fps,
      confidence: confidence
    }, {
      params: { video_id: videoId }
    });
    return response.data;
  }

  async getStatus(requestId) {
    const response = await axios.get(`${API_URL}/status/${requestId}`);
    return response.data;
  }

  async getResults(requestId) {
    const response = await axios.get(`${API_URL}/result/${requestId}`);
    return response.data;
  }

  async getFragmentUrls(requestId, expiresIn = 3600) {
    const response = await axios.get(`${API_URL}/result/${requestId}/fragments`, {
      params: { expires_in: expiresIn }
    });
    return response.data;
  }
}

export default new AnalysisService();