import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Sliders, RotateCcw, Save, CheckCircle2, AlertOctagon, HelpCircle } from 'lucide-react';

const PROJECT_ID = 1;

const DEFAULT_SETTINGS = {
  gold_threshold: 90,
  kappa_threshold: 0.7,
  behavior_threshold: 75,
  embedding_threshold: 80,
};

function percent(value) {
  return `${Number(value).toFixed(0)}%`;
}

function CustomSlider({
  id,
  label,
  description,
  min,
  max,
  step,
  value,
  displayValue,
  unit = '%',
  recommended,
  onChange,
}) {
  // Calculate fill percentage
  const pct = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);

  return (
    <div className="setting-control">
      <div className="setting-label-row">
        <div>
          <label htmlFor={id}>{label}</label>
          <p>{description}</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {recommended && (
            <span
              style={{
                fontSize: '0.7rem',
                color: 'var(--text-muted)',
                fontFamily: 'var(--font-mono)',
              }}
              title="Recommended production baseline"
            >
              Rec: {recommended}
            </span>
          )}
          <span className="setting-value">{displayValue}</span>
        </div>
      </div>

      <input
        id={id}
        className="threshold-slider"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          background: `linear-gradient(to right, var(--accent-500) 0%, var(--accent-500) ${pct}%, var(--bg-surface-elevated) ${pct}%, var(--bg-surface-elevated) 100%)`,
        }}
      />

      <div className="slider-range">
        <span>{min}{unit === '%' ? '%' : ''}</span>
        <span style={{ color: 'var(--accent-300)' }}>Current: {displayValue}</span>
        <span>{max}{unit === '%' ? '%' : ''}</span>
      </div>
    </div>
  );
}

export default function ProjectSettings() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [savedSettings, setSavedSettings] = useState(DEFAULT_SETTINGS);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        setError('');

        const response = await api.get(`/projects/${PROJECT_ID}/settings`);

        const loadedSettings = {
          gold_threshold: response.data.gold_threshold ?? DEFAULT_SETTINGS.gold_threshold,
          kappa_threshold: response.data.kappa_threshold ?? DEFAULT_SETTINGS.kappa_threshold,
          behavior_threshold: response.data.behavior_threshold ?? DEFAULT_SETTINGS.behavior_threshold,
          embedding_threshold: response.data.embedding_threshold ?? DEFAULT_SETTINGS.embedding_threshold,
        };

        setSettings(loadedSettings);
        setSavedSettings(loadedSettings);
      } catch (err) {
        console.error('Failed to load project settings:', err);
        setError(err.response?.data?.detail || 'Failed to load project settings.');
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, []);

  function handleChange(name, value) {
    setSettings((current) => ({
      ...current,
      [name]: Number(value),
    }));
    setMessage('');
    setError('');
  }

  async function handleSave() {
    try {
      setSaving(true);
      setMessage('');
      setError('');

      const payload = {
        gold_threshold: Number(settings.gold_threshold),
        kappa_threshold: Number(settings.kappa_threshold),
        behavior_threshold: Number(settings.behavior_threshold),
        embedding_threshold: Number(settings.embedding_threshold),
      };

      const response = await api.put(`/projects/${PROJECT_ID}/settings`, payload);

      const updatedSettings = {
        gold_threshold: response.data.gold_threshold ?? payload.gold_threshold,
        kappa_threshold: response.data.kappa_threshold ?? payload.kappa_threshold,
        behavior_threshold: response.data.behavior_threshold ?? payload.behavior_threshold,
        embedding_threshold: response.data.embedding_threshold ?? payload.embedding_threshold,
      };

      setSettings(updatedSettings);
      setSavedSettings(updatedSettings);
      setMessage('Project quality thresholds updated and saved successfully.');
    } catch (err) {
      console.error('Failed to save project settings:', err);
      setError(err.response?.data?.detail || 'Failed to save project settings.');
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setSettings(savedSettings);
    setMessage('');
    setError('');
  }

  const hasChanges =
    settings.gold_threshold !== savedSettings.gold_threshold ||
    settings.kappa_threshold !== savedSettings.kappa_threshold ||
    settings.behavior_threshold !== savedSettings.behavior_threshold ||
    settings.embedding_threshold !== savedSettings.embedding_threshold;

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1 className="page-title">Project Settings</h1>
            <p className="page-subtitle">Configure quality thresholds for annotation review.</p>
          </div>
        </div>
        <div className="card">
          <div style={{ padding: '2rem 0' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Project Settings</h1>
          <p className="page-subtitle">
            Configure the automated review triggers and scoring thresholds for Project {PROJECT_ID}.
          </p>
        </div>

        <div className="topbar-badge-project">
          <span>Target:</span>
          <strong style={{ color: 'var(--text-primary)' }}>Project {PROJECT_ID}</strong>
        </div>
      </div>

      {message && (
        <div className="alert-success">
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="alert">
          <AlertOctagon size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Unified Settings Panel */}
      <div className="card">
        <div className="card-header">
          <div>
            <h2>Quality Threshold Triggers</h2>
            <p>
              Annotations falling below any of these minimum levels will automatically be flagged for the Review Queue.
            </p>
          </div>

          {hasChanges && (
            <span className="badge badge-medium">Unsaved Changes</span>
          )}
        </div>

        <div className="settings-controls">
          {/* Gold Accuracy Threshold */}
          <CustomSlider
            id="gold-threshold"
            label="Gold Standard Accuracy"
            description="Minimum acceptable accuracy on known ground-truth benchmark items."
            min={0}
            max={100}
            step={1}
            value={settings.gold_threshold}
            displayValue={percent(settings.gold_threshold)}
            recommended="85%"
            onChange={(val) => handleChange('gold_threshold', val)}
          />

          {/* Kappa Agreement Threshold */}
          <CustomSlider
            id="kappa-threshold"
            label="Cohen's Kappa Agreement"
            description="Minimum acceptable pairwise inter-annotator agreement score."
            min={-1}
            max={1}
            step={0.01}
            unit=""
            value={settings.kappa_threshold}
            displayValue={Number(settings.kappa_threshold).toFixed(2)}
            recommended="0.70"
            onChange={(val) => handleChange('kappa_threshold', val)}
          />

          {/* Behavioral Quality Threshold */}
          <CustomSlider
            id="behavior-threshold"
            label="Behavioral Consistency"
            description="Minimum score for duration, confidence consistency, and fatigue detection."
            min={0}
            max={100}
            step={1}
            value={settings.behavior_threshold}
            displayValue={percent(settings.behavior_threshold)}
            recommended="75%"
            onChange={(val) => handleChange('behavior_threshold', val)}
          />

          {/* Embedding Similarity Threshold */}
          <CustomSlider
            id="embedding-threshold"
            label="Semantic Embedding Similarity"
            description="Minimum semantic similarity to cluster centroids before flagging as an outlier."
            min={0}
            max={100}
            step={1}
            value={settings.embedding_threshold}
            displayValue={percent(settings.embedding_threshold)}
            recommended="80%"
            onChange={(val) => handleChange('embedding_threshold', val)}
          />
        </div>

        {/* Action Buttons */}
        <div className="settings-actions">
          <button
            type="button"
            className="secondary-btn"
            onClick={handleReset}
            disabled={saving || !hasChanges}
          >
            <RotateCcw size={14} />
            <span>Reset</span>
          </button>

          <button
            type="button"
            className="primary-btn"
            onClick={handleSave}
            disabled={saving}
          >
            <Save size={14} />
            <span>{saving ? 'Saving Thresholds...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}