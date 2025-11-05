import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessToken, setAccessToken] = useState(localStorage.getItem('access_token'));
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'));

  // Axios 인터셉터 설정
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        if (accessToken && config.url.startsWith(API_BASE_URL)) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // 401 에러이고 토큰 갱신 시도하지 않은 경우
        if (error.response?.status === 401 && !originalRequest._retry && refreshToken) {
          originalRequest._retry = true;

          try {
            const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
              refresh_token: refreshToken
            });

            const { access_token, refresh_token: new_refresh_token } = response.data;

            setAccessToken(access_token);
            setRefreshToken(new_refresh_token);
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', new_refresh_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return axios(originalRequest);
          } catch (refreshError) {
            // 토큰 갱신 실패 - 로그아웃
            logout();
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, [accessToken, refreshToken]);

  // 사용자 정보 로드
  useEffect(() => {
    const loadUser = async () => {
      if (accessToken) {
        try {
          const [userRes, tenantRes] = await Promise.all([
            axios.get(`${API_BASE_URL}/api/auth/me`),
            axios.get(`${API_BASE_URL}/api/auth/tenant`)
          ]);

          setUser(userRes.data);
          setTenant(tenantRes.data);
        } catch (error) {
          console.error('Failed to load user:', error);
          // 토큰이 유효하지 않으면 로그아웃
          if (error.response?.status === 401) {
            logout();
          }
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [accessToken]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      });

      const { access_token, refresh_token } = response.data;

      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // 사용자 정보 로드
      const [userRes, tenantRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${access_token}` }
        }),
        axios.get(`${API_BASE_URL}/api/auth/tenant`, {
          headers: { Authorization: `Bearer ${access_token}` }
        })
      ]);

      setUser(userRes.data);
      setTenant(tenantRes.data);

      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || '로그인에 실패했습니다'
      };
    }
  };

  const register = async (data) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, data);

      const { access_token, refresh_token } = response.data;

      setAccessToken(access_token);
      setRefreshToken(refresh_token);
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // 사용자 정보 로드
      const [userRes, tenantRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${access_token}` }
        }),
        axios.get(`${API_BASE_URL}/api/auth/tenant`, {
          headers: { Authorization: `Bearer ${access_token}` }
        })
      ]);

      setUser(userRes.data);
      setTenant(tenantRes.data);

      return { success: true };
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        error: error.response?.data?.detail || '회원가입에 실패했습니다'
      };
    }
  };

  const logout = () => {
    setUser(null);
    setTenant(null);
    setAccessToken(null);
    setRefreshToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  };

  const value = {
    user,
    tenant,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
