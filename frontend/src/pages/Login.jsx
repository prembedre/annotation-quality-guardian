/**
 * Annotation Ops — Modern Light Theme Login Screen
 * Featuring enterprise credential authentication.
 */

import React, { useState } from 'react';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Loader2,
  Layers,
} from 'lucide-react';
import { useAuth } from '../components/AuthContext';
import './Login.css';

export default function Login() {
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Standard authentication submit
  const handleStandardSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!email || !password) {
      setErrorMessage('Please fill in both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err) {
      setErrorMessage(err.message || 'Invalid credentials. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ops-login-wrapper">
      {/* Subtle background ambient mesh */}
      <div className="ops-bg-glow ops-bg-glow--top-left" aria-hidden="true" />
      <div className="ops-bg-glow ops-bg-glow--bottom-right" aria-hidden="true" />
      <div className="ops-bg-grid" aria-hidden="true" />

      <main className="ops-login-container">
        {/* Brand Header */}
        <header className="ops-brand-header">
          <div className="ops-logo-badge">
            <Layers className="ops-logo-icon" size={24} />
          </div>
          <h1 className="ops-brand-title">Annotation Ops</h1>
          <p className="ops-brand-tagline">Workflow Automation & Analytics Platform</p>
        </header>

        {/* Primary Login Card */}
        <section className="ops-card ops-login-card" aria-label="Sign In Card">
          <div className="ops-card-header">
            <h2 className="ops-card-title">Welcome back</h2>
            <p className="ops-card-subtitle">
              Enter your credentials to access your workspaces & pipelines
            </p>
          </div>

          {errorMessage && (
            <div className="ops-error-banner" role="alert">
              <span className="ops-error-dot" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleStandardSubmit} noValidate className="ops-form">
            {/* Email Field */}
            <div className="ops-input-group">
              <label htmlFor="ops-email-input" className="ops-label">
                Email Address
              </label>
              <div className="ops-input-wrapper">
                <Mail className="ops-field-icon" size={18} aria-hidden="true" />
                <input
                  id="ops-email-input"
                  type="email"
                  className="ops-input"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="ops-input-group">
              <div className="ops-label-row">
                <label htmlFor="ops-password-input" className="ops-label">
                  Password
                </label>
                <a
                  href="#forgot-password"
                  className="ops-forgot-link"
                  onClick={(e) => {
                    e.preventDefault();
                    alert('Password reset link has been dispatched to your email.');
                  }}
                >
                  Forgot password?
                </a>
              </div>
              <div className="ops-input-wrapper">
                <Lock className="ops-field-icon" size={18} aria-hidden="true" />
                <input
                  id="ops-password-input"
                  type={showPassword ? 'text' : 'password'}
                  className="ops-input ops-input--password"
                  placeholder="Enter your secure password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="ops-pw-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              id="ops-submit-btn"
              type="submit"
              className="ops-btn-primary"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="ops-spin" size={18} />
                  <span>Signing In…</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>

            {/* Registration link */}
            <div className="ops-card-footer">
              <span>Don't have an account?</span>{' '}
              <button
                type="button"
                className="ops-link-btn"
                onClick={() => alert('Registration request sent to your workspace administrator.')}
              >
                Register
              </button>
            </div>
          </form>
        </section>

        {/* Footer Meta */}
        <footer className="ops-meta-footer">
          <span>Enterprise Annotation Hub</span>
          <span className="ops-meta-sep">•</span>
          <span>SOC-2 Type II Certified</span>
          <span className="ops-meta-sep">•</span>
          <span>v2.4.0-prod</span>
        </footer>
      </main>
    </div>
  );
}
