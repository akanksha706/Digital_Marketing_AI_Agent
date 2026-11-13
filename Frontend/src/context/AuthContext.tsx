import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, AuthResponse } from '../types';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<User>;
  switchAccount: (role: 'admin' | 'creator') => Promise<void>;
  logout: () => void;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Read stored user or null
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem('studio_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('studio_token');
  });

  // Verify session on mount
  useEffect(() => {
    if (token) {
      apiClient
        .get<User>('/auth/me')
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('studio_user', JSON.stringify(res.data));
        })
        .catch(() => {
          // If token expired, clear
          logout();
        });
    }
  }, [token]);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await apiClient.post<AuthResponse>('/auth/login', { email, password });
    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('studio_token', access_token);
    localStorage.setItem('studio_user', JSON.stringify(userData));
    return userData;
  };

  const switchAccount = async (targetRole: 'admin' | 'creator') => {
    const email = targetRole === 'admin' ? 'admin@company.com' : 'creator@company.com';
    const password = targetRole === 'admin' ? 'admin@123' : 'creator@123';
    await login(email, password);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('studio_token');
    localStorage.removeItem('studio_user');
    window.location.href = '/login';
  };

  const changePassword = async (old_password: string, new_password: string) => {
    await apiClient.post('/auth/change-password', { old_password, new_password });
  };

  // Determine actual role dynamically (NEVER hardcoded)
  const isAdmin = user?.role === 'admin';
  const isAuthenticated = !!user && !!token;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        isAdmin,
        login,
        switchAccount,
        logout,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
