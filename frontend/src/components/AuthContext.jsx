/**
 * AuthContext — provides authentication state and helpers to the entire app.
 *
 * Exposes:
 *   user          — current User object or null
 *   token         — JWT string or null
 *   isAuthenticated — boolean
 *   login(email, password) — authenticate and navigate to /
 *   logout()      — clear token and navigate to /login
 */

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  login as authLogin,
  logout as authLogout,
  fetchMe,
  getToken,
} from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getToken);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // On mount (and whenever token changes) try to restore the user session
  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    fetchMe()
      .then((profile) => setUser(profile))
      .catch(() => {
        // Token invalid / expired
        authLogout();
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = useCallback(async (email, password) => {
    const data = await authLogin(email, password);
    setToken(data.access_token);
    setUser(data.user);
    navigate('/');
  }, [navigate]);

  const loginAsDemo = useCallback(async (roleKey) => {
    const demoProfiles = {
      system_admin: { email: 'admin@annotationops.io', password: 'demo12345' },
      product_owner: { email: 'po@annotationops.io', password: 'demo12345' },
      project_manager: { email: 'pm@annotationops.io', password: 'demo12345' },
      annotator_1: { email: 'dave@annotationops.io', password: 'demo12345' },
      annotator_2: { email: 'sarah@annotationops.io', password: 'demo12345' },
      reviewer: { email: 'bob@annotationops.io', password: 'demo12345' },
    };

    const targetUser = demoProfiles[roleKey] || demoProfiles.system_admin;
    const data = await authLogin(targetUser.email, targetUser.password);
    setToken(data.access_token);
    setUser(data.user);
    navigate('/');
  }, [navigate]);

  const logout = useCallback(() => {
    authLogout();
    localStorage.removeItem('aqg_demo_user');
    setToken(null);
    setUser(null);
    navigate('/login');
  }, [navigate]);

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    loading,
    login,
    loginAsDemo,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook for consuming auth state anywhere in the app.
 * Must be used inside <AuthProvider>.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
