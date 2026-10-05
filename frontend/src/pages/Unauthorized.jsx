/**
 * Unauthorized page — shown when a user's role lacks access to a route.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldOff, ArrowLeft } from 'lucide-react';
import { useAuth } from '../components/AuthContext';

export default function Unauthorized() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <div className="unauth-page">
      <div className="unauth-card">
        <div className="unauth-icon">
          <ShieldOff size={40} />
        </div>
        <h1 className="unauth-code">403</h1>
        <h2 className="unauth-title">Access Denied</h2>
        <p className="unauth-description">
          Your role{user ? ` (${user.role.replace('_', ' ')})` : ''} does not have permission
          to access this page.
        </p>

        <div className="unauth-actions">
          <button
            id="unauth-go-back-btn"
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft size={15} />
            Go Back
          </button>
          <button
            id="unauth-go-home-btn"
            type="button"
            className="btn btn-primary"
            onClick={() => navigate('/')}
          >
            Go to Dashboard
          </button>
        </div>

        <button
          id="unauth-logout-btn"
          type="button"
          className="unauth-logout-link"
          onClick={logout}
        >
          Sign in as a different account
        </button>
      </div>
    </div>
  );
}
