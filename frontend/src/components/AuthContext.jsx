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

    if (token.startsWith('demo_token_')) {
      try {
        const storedDemo = localStorage.getItem('aqg_demo_user');
        if (storedDemo) {
          setUser(JSON.parse(storedDemo));
        }
      } catch (e) {
        console.error('Failed to parse demo user', e);
      }
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
      system_admin: { id: 1, email: 'admin@annotationops.io', full_name: 'Admin User', role: 'admin' },
      product_owner: { id: 2, email: 'po@annotationops.io', full_name: 'Product Owner', role: 'product_owner' },
      project_manager: { id: 3, email: 'pm@annotationops.io', full_name: 'Project Manager', role: 'project_manager' },
      annotator_1: { id: 4, email: 'dave@annotationops.io', full_name: 'Annotator 1', role: 'annotator' },
      annotator_2: { id: 5, email: 'sarah@annotationops.io', full_name: 'Annotator 2', role: 'annotator' },
      reviewer: { id: 6, email: 'bob@annotationops.io', full_name: 'Reviewer', role: 'reviewer' },
    };

    const targetUser = demoProfiles[roleKey] || demoProfiles.system_admin;

    try {
      // Attempt actual backend login if credentials exist
      const data = await authLogin(targetUser.email, 'demo12345');
      setToken(data.access_token);
      setUser(data.user);
    } catch {
      // Fallback: seed simulated demo session in localStorage
      const mockToken = `demo_token_${targetUser.role}_${Date.now()}`;
      localStorage.setItem('aqg_auth_token', mockToken);
      localStorage.setItem('aqg_demo_user', JSON.stringify(targetUser));
      setToken(mockToken);
      setUser(targetUser);
    }
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
