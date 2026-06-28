import React, { createContext, useState, useContext, useEffect } from 'react';
import authService from '../services/authService';
import userService from '../services/userService';
import { jwtDecode } from 'jwt-decode';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshToken = async () => {
    try {
      const result = await authService.refresh();
      if (result) {
        await fetchFullUserData();
      }
    } catch (error) {
      authService.clearTokens();
      setUser(null);
    }
  };

  const fetchFullUserData = async () => {
    try {
      const userData = await userService.getProfile();
      setUser({
        id: userData.id,
        username: userData.username,
        email: userData.email,
        role: userData.role,
        preview_url: userData.preview_url,
        avatar_url: userData.avatar_url,
      });
    } catch (error) {
      console.error("Failed to fetch full user data", error);
      if (error.response && error.response.status === 401) {
        authService.logout();
        setUser(null);
      }
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = authService.getAccessToken();
      if (token) {
        try {
          const decoded = jwtDecode(token);
          if (decoded.exp * 1000 > Date.now()) {
            setUser({
              id: decoded.user_id,
              username: decoded.username,
              email: decoded.email,
              role: decoded.role
            });
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

            await fetchFullUserData();
          } else {
            await refreshToken();
          }
        } catch (error) {
          authService.clearTokens();
        }
      }
      setLoading(false);
    };

    initAuth();

    const interval = setInterval(async () => {
      const token = authService.getAccessToken();
      if (token) {
        try {
          const decoded = jwtDecode(token);
          if (decoded.exp * 1000 < Date.now() + 5 * 60 * 1000) {
            await refreshToken();
          }
        } catch (error) {
          console.error('Token refresh error:', error);
        }
      }
    }, 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  const login = async (email, password) => {
    const result = await authService.login(email, password);
    await fetchFullUserData();
    return result;
  };

  const register = async (username, email, password) => {
    const result = await authService.register(username, email, password, 'user');
    await fetchFullUserData();
    return result;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const refreshUser = fetchFullUserData;

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};