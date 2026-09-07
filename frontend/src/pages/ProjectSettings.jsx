import React, { useEffect, useState } from 'react';
import api from '../services/api';

const PROJECT_ID = 1;

const DEFAULT_SETTINGS = {
  gold_threshold: 90,
  kappa_threshold: 0.7,
  behavior_threshold: 75,
  embedding_threshold: 80,
};

function ProjectSettings() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        setError('');

        const { data } = await api.get(`/projects/${PROJECT_ID}/settings`);

        setSettings({
          gold_threshold: data.gold_threshold,
          kappa_threshold: data.kappa_threshold,
          behavior_threshold: data.behavior_threshold,
          embedding_threshold: data.embedding_threshold,
        });
      } catch (err) {
        console.error('Failed to load project settings:', err);
        setError('Failed to load project settings.');
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setSettings((previous) => ({
      ...previous,
      [name]: value,
    }));

    setSuccess('');
    setError('');
  }

  async function handleSubmit(event) {
    event.preventDefault();

    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const payload = {
        gold_threshold: Number(settings.gold_threshold),
        kappa_threshold: Number(settings.kappa_threshold),
        behavior_threshold: Number(settings.behavior_threshold),
        embedding_threshold: Number(settings.embedding_threshold),
      };

      const { data } = await api.put(
        `/projects/${PROJECT_ID}/settings`,
        payload
      );

      setSettings({
        gold_threshold: data.gold_threshold,
        kappa_threshold: data.kappa_threshold,
        behavior_threshold: data.behavior_threshold,
        embedding_threshold: data.embedding_threshold,
      });

      setSuccess('Project settings saved successfully.');
    } catch (err) {
      console.error('Failed to save project settings:', err);

      const message =
        err.response?.data?.detail || 'Failed to save project settings.';

      setError(message);
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setSettings(DEFAULT_SETTINGS);
    setSuccess('');
    setError('');
  }

  if (loading) {
    return (
      <div>
        <h1 className="page-title">Project Settings</h1>
        <div className="card">
          <p>Loading project settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Project Settings</h1>

      <div className="card">
        <h2>Quality Thresholds</h2>

        <p style={{ marginBottom: '24px' }}>
          Configure the quality thresholds used by the Annotation Quality
          Guardian for Project {PROJECT_ID}.
        </p>

        {error && (
          <div
            style={{
              padding: '12px 16px',
              marginBottom: '20px',
              borderRadius: '6px',
              backgroundColor: '#fee2e2',
              color: '#991b1b',
            }}
          >
            {error}
          </div>
        )}

        {success && (
          <div
            style={{
              padding: '12px 16px',
              marginBottom: '20px',
              borderRadius: '6px',
              backgroundColor: '#dcfce7',
              color: '#166534',
            }}
          >
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '24px' }}>
            <label
              htmlFor="gold_threshold"
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '8px',
              }}
            >
              Gold Threshold (%)
            </label>

            <input
              id="gold_threshold"
              name="gold_threshold"
              type="number"
              min="0"
              max="100"
              step="1"
              value={settings.gold_threshold}
              onChange={handleChange}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '6px',
              }}
            />

            <p style={{ marginTop: '6px', color: '#666' }}>
              Minimum percentage required for gold-label quality.
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label
              htmlFor="kappa_threshold"
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '8px',
              }}
            >
              Kappa Threshold
            </label>

            <input
              id="kappa_threshold"
              name="kappa_threshold"
              type="number"
              min="-1"
              max="1"
              step="0.01"
              value={settings.kappa_threshold}
              onChange={handleChange}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '6px',
              }}
            />

            <p style={{ marginTop: '6px', color: '#666' }}>
              Minimum acceptable inter-annotator agreement score.
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label
              htmlFor="behavior_threshold"
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '8px',
              }}
            >
              Behavioral Threshold (%)
            </label>

            <input
              id="behavior_threshold"
              name="behavior_threshold"
              type="number"
              min="0"
              max="100"
              step="1"
              value={settings.behavior_threshold}
              onChange={handleChange}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '6px',
              }}
            />

            <p style={{ marginTop: '6px', color: '#666' }}>
              Minimum behavioral quality score required for an annotator.
            </p>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label
              htmlFor="embedding_threshold"
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '8px',
              }}
            >
              Embedding Threshold (%)
            </label>

            <input
              id="embedding_threshold"
              name="embedding_threshold"
              type="number"
              min="0"
              max="100"
              step="1"
              value={settings.embedding_threshold}
              onChange={handleChange}
              style={{
                width: '100%',
                maxWidth: '400px',
                padding: '10px',
                border: '1px solid #ccc',
                borderRadius: '6px',
              }}
            />

            <p style={{ marginTop: '6px', color: '#666' }}>
              Minimum embedding-based quality score required.
            </p>
          </div>

          <div
            style={{
              display: 'flex',
              gap: '12px',
              marginTop: '30px',
            }}
          >
            <button
              type="submit"
              disabled={saving}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderRadius: '6px',
                cursor: saving ? 'not-allowed' : 'pointer',
              }}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>

            <button
              type="button"
              onClick={handleReset}
              disabled={saving}
              style={{
                padding: '10px 20px',
                border: '1px solid #ccc',
                borderRadius: '6px',
                backgroundColor: 'white',
                cursor: saving ? 'not-allowed' : 'pointer',
              }}
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProjectSettings;