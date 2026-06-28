import axios from 'axios';

const API_URL = '/api/v1/auth';

class AuthService {
  async register(username, email, password, role = 'user') {
    const response = await axios.post(`${API_URL}/register`, {
      username,
      email,
      password,
      role
    });
    if (response.data.access_token) {
      this.setTokens(response.data);
    }
    return response.data;
  }

  async login(email, password) {
    const response = await axios.post(`${API_URL}/login`, {
      email: email,
      password
    });
    if (response.data.access_token) {
      this.setTokens(response.data);
    }
    return response.data;
  }

  async refresh() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return null;

    const response = await axios.post(`${API_URL}/refresh`, {
      refresh_token: refreshToken
    });
    if (response.data.access_token) {
      this.setTokens(response.data);
    }
    return response.data;
  }

  setTokens(tokens) {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`;
  }

  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete axios.defaults.headers.common['Authorization'];
  }

  logout() {
    this.clearTokens();
  }

  getAccessToken() {
    return localStorage.getItem('access_token');
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }
}

export default new AuthService();