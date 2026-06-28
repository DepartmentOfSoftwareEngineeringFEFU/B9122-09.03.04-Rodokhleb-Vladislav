import axios from 'axios';

const API_URL = '/api/v1';

class UserService {
  async getProfile() {
    const response = await axios.get(`${API_URL}/users/me`);
    return response.data;
  }

  async updateProfile(formData) {
    const response = await axios.put(`${API_URL}/users/me`, formData);
    return response.data;
  }

  async getProfileStats() {
    const response = await axios.get(`${API_URL}/users/me/stats`);
    return response.data;
  }

  async getUserRequests(page = 1, size = 20) {
    const response = await axios.get(`${API_URL}/fragments/requests`, {
      params: { page, size }
    });
    return response.data;
  }

  async getRequestFragments(requestId) {
    const response = await axios.get(`${API_URL}/fragments/requests/${requestId}`);
    return response.data;
  }

  async getRequestStatus(requestId) {
    const response = await axios.get(`${API_URL}/analysis/status/${requestId}`);
    return response.data;
  }

  async deleteRequest(requestId) {
    const response = await axios.delete(`${API_URL}/fragments/requests/${requestId}`);
    return response.data;
  }

  async getAvatarBlob() {
    const response = await axios.get(`${API_URL}/users/me/avatar`, {
      responseType: 'blob'
    });
    return response.data;
  }
}



export default new UserService();