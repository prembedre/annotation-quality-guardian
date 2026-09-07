import { useEffect, useState } from 'react';
import api from '../services/api';

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

        const response = await api.get(
          `/projects/${PROJECT_ID}/settings`
        );

        const loadedSettings = {
          gold_threshold:
            response.data.gold_threshold ?? DEFAULT_SETTINGS.gold_threshold,

          kappa_threshold:
            response.data.kappa_threshold ??
            DEFAULT_SETTINGS.kappa_threshold,

          behavior_threshold:
            response.data.behavior_threshold ??
            DEFAULT_SETTINGS.behavior_threshold,

          embedding_threshold:
            response.data.embedding_threshold ??
            DEFAULT_SETTINGS.embedding_threshold,
        };

        setSettings(loadedSettings);
        setSavedSettings(loadedSettings);
      } catch (err) {
        console.error('Failed to load project settings:', err);

        setError(
          err.response?.data?.detail ||
            'Failed to load project settings.'
        );
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

      const response = await api.put(
        `/projects/${PROJECT_ID}/settings`,
        payload
      );

      const updatedSettings = {
        gold_threshold:
          response.data.gold_threshold ?? payload.gold_threshold,

        kappa_threshold:
          response.data.kappa_threshold ?? payload.kappa_threshold,

        behavior_threshold:
          response.data.behavior_threshold ?? payload.behavior_threshold,

        embedding_threshold:
          response.data.embedding_threshold ?? payload.embedding_threshold,
      };

      setSettings(updatedSettings);
      setSavedSettings(updatedSettings);

      setMessage('Project settings saved successfully.');
    } catch (err) {
      console.error('Failed to save project settings:', err);

      setError(
        err.response?.data?.detail ||
          'Failed to save project settings.'
      );
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setSettings(savedSettings);
    setMessage('');
    setError('');
  }

  if (loading) {
    return (
      <div className="settings-page">
        <div className="settings-card">
          <p>Loading project settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <div>
          <h1>Project Settings</h1>

          <p>
            Configure the quality thresholds used to identify
            annotations that need review.
          </p>
        </div>

        <div className="settings-project">
          Project {PROJECT_ID}
        </div>
      </div>

      <div className="settings-card">
        <div className="settings-section-header">
          <div>
            <h2>Quality Thresholds</h2>

            <p>
              Adjust the minimum quality levels for each scoring
              signal.
            </p>
          </div>
        </div>

        <div className="settings-controls">
          {/* Gold Threshold */}
          <div className="setting-control">
            <div className="setting-label-row">
              <div>
                <label htmlFor="gold-threshold">
                  Gold Accuracy Threshold
                </label>

                <p>
                  Minimum acceptable accuracy on gold-standard
                  annotations.
                </p>
              </div>

              <span className="setting-value">
                {percent(settings.gold_threshold)}
              </span>
            </div>

            <input
              id="gold-threshold"
              className="threshold-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value={settings.gold_threshold}
              onChange={(event) =>
                handleChange(
                  'gold_threshold',
                  event.target.value
                )
              }
            />

            <div className="slider-range">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Kappa Threshold */}
          <div className="setting-control">
            <div className="setting-label-row">
              <div>
                <label htmlFor="kappa-threshold">
                  Kappa Threshold
                </label>

                <p>
                  Minimum acceptable inter-annotator agreement.
                </p>
              </div>

              <span className="setting-value">
                {Number(settings.kappa_threshold).toFixed(2)}
              </span>
            </div>

            <input
              id="kappa-threshold"
              className="threshold-slider"
              type="range"
              min="-1"
              max="1"
              step="0.01"
              value={settings.kappa_threshold}
              onChange={(event) =>
                handleChange(
                  'kappa_threshold',
                  event.target.value
                )
              }
            />

            <div className="slider-range">
              <span>-1.00</span>
              <span>1.00</span>
            </div>
          </div>

          {/* Behavioral Threshold */}
          <div className="setting-control">
            <div className="setting-label-row">
              <div>
                <label htmlFor="behavior-threshold">
                  Behavioral Threshold
                </label>

                <p>
                  Minimum acceptable behavioral quality score.
                </p>
              </div>

              <span className="setting-value">
                {percent(settings.behavior_threshold)}
              </span>
            </div>

            <input
              id="behavior-threshold"
              className="threshold-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value={settings.behavior_threshold}
              onChange={(event) =>
                handleChange(
                  'behavior_threshold',
                  event.target.value
                )
              }
            />

            <div className="slider-range">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Embedding Threshold */}
          <div className="setting-control">
            <div className="setting-label-row">
              <div>
                <label htmlFor="embedding-threshold">
                  Embedding Threshold
                </label>

                <p>
                  Minimum acceptable semantic similarity score.
                </p>
              </div>

              <span className="setting-value">
                {percent(settings.embedding_threshold)}
              </span>
            </div>

            <input
              id="embedding-threshold"
              className="threshold-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value={settings.embedding_threshold}
              onChange={(event) =>
                handleChange(
                  'embedding_threshold',
                  event.target.value
                )
              }
            />

            <div className="slider-range">
              <span>0%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {message && (
          <div className="settings-success">
            {message}
          </div>
        )}

        {error && (
          <div className="settings-error">
            {error}
          </div>
        )}

        <div className="settings-actions">
          <button
            type="button"
            className="settings-reset-button"
            onClick={handleReset}
            disabled={saving}
          >
            Reset
          </button>

          <button
            type="button"
            className="settings-save-button"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}