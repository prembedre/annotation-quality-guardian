/**
 * ProtectedRoute — guards pages requiring authentication and/or specific roles.
 *
 * Usage:
 *   <ProtectedRoute>                          // Any authenticated user
 *   <ProtectedRoute allowedRoles={['admin']}> // Admin only
 */

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

/**
 * @param {object} props
 * @param {React.ReactNode} props.children
 * @param {string[]} [props.allowedRoles]  — list of UserRole values that may access this route
 */
export function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // While the session is being restored, render nothing (avoids flash redirects)
  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          color: 'var(--text-muted)',
          fontSize: '0.875rem',
        }}
      >
        Loading…
      </div>
    );
  }

  // Not authenticated → send to /login, preserving the intended destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Authenticated but wrong role → send to /unauthorized
  if (allowedRoles && allowedRoles.length > 0 && user) {
    if (!allowedRoles.includes(user.role)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
}
