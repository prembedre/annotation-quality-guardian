import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import {
  Sliders,
  RotateCcw,
  Save,
  CheckCircle2,
  ShieldCheck,
  Scale,
  Activity,
  Layers,
  AlertTriangle,
} from 'lucide-react';
import {
  PageHeader,
  ThresholdSlider,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

const PROJECT_ID = 1;

const DEFAULT_SETTINGS = {
  gold_threshold: 90,
  kappa_threshold: 0.7,
  behavior_threshold: 75,
  embedding_threshold: 80,
};

export default function ProjectSettings() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [savedSettings, setSavedSettings] = useState(DEFAULT_SETTINGS);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const { success, error: toastError } = useToast();

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const response = await api.get(`/projects/${PROJECT_ID}/settings`);
      const loadedSettings = {
        gold_threshold:
          response.data.gold_threshold != null
            ? Math.round(Number(response.data.gold_threshold))
            : DEFAULT_SETTINGS.gold_threshold,
        kappa_threshold:
          response.data.kappa_threshold != null
            ? Number(response.data.kappa_threshold)
            : DEFAULT_SETTINGS.kappa_threshold,
        behavior_threshold:
          response.data.behavior_threshold != null
            ? Math.round(Number(response.data.behavior_threshold))
            : DEFAULT_SETTINGS.behavior_threshold,
        embedding_threshold:
          response.data.embedding_threshold != null
            ? Math.round(Number(response.data.embedding_threshold))
            : DEFAULT_SETTINGS.embedding_threshold,
      };

      setSettings(loadedSettings);
      setSavedSettings(loadedSettings);
    } catch (err) {
      console.error('Failed to load project settings:', err);
      setError(err.response?.data?.detail || 'Failed to load project settings.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  // Determine if settings are dirty
  const isDirty = JSON.stringify(settings) !== JSON.stringify(savedSettings);

  const handleSliderChange = (key, value) => {
    setSettings((prev) => ({
      ...prev,
      [key]: key === 'kappa_threshold' ? Number(value) : Math.round(Number(value)),
    }));
  };

  const handleDiscard = () => {
    setSettings(savedSettings);
  };

  const handleSave = async (e) => {
    e?.preventDefault();
    try {
      setSaving(true);
      setError('');

      const payload = {
        gold_threshold: Number(settings.gold_threshold),
        kappa_threshold: Number(settings.kappa_threshold),
        behavior_threshold: Number(settings.behavior_threshold),
        embedding_threshold: Number(settings.embedding_threshold),
      };

      const response = await api.put(`/projects/${PROJECT_ID}/settings`, payload);

      const updated = {
        gold_threshold: Math.round(Number(response.data.gold_threshold)),
        kappa_threshold: Number(response.data.kappa_threshold),
        behavior_threshold: Math.round(Number(response.data.behavior_threshold)),
        embedding_threshold: Math.round(Number(response.data.embedding_threshold)),
      };

      setSettings(updated);
      setSavedSettings(updated);
      success('Project quality thresholds updated and persisted!');
    } catch (err) {
      console.error('Failed to save project settings:', err);
      const msg = err.response?.data?.detail || 'Failed to save project settings.';
      setError(msg);
      toastError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      {/* Sticky Save Changes Bar when Dirty */}
      {isDirty && (
        <div className="sticky-save-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="badge badge-medium">Unsaved Changes</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
              Threshold modifications have not been saved.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              type="button"
              className="ghost-btn"
              onClick={handleDiscard}
              disabled={saving}
              style={{ fontSize: '0.78rem' }}
            >
              Discard
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleSave}
              disabled={saving}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.78rem' }}
            >
              <Save size={13} />
              <span>{saving ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>
      )}

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Governance & Threshold Config"
        title="Project Settings"
        subtitle="Configure automated quality gates, agreement trigger points, and anomaly limits for Project #1."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleDiscard}
              disabled={!isDirty || saving}
            >
              <RotateCcw size={14} />
              <span>Reset</span>
            </button>

            <button
              type="button"
              className="primary-btn"
              onClick={handleSave}
              disabled={!isDirty || saving}
            >
              <Save size={14} />
              <span>{saving ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>
        }
      />

      {error && <ErrorState message={error} onRetry={loadSettings} />}

      {loading ? (
        <div className="card">
          <LoadingState count={4} />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.25rem' }}>
          {/* Group 1: Consensus & Reliability */}
          <div className="card" style={{ marginBottom: 0 }}>
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div className="stat-card-icon-wrap">
                  <Scale size={15} />
                </div>
                <div>
                  <h2>Agreement &amp; Ground Truth</h2>
                  <p>Thresholds controlling dispute detection and accuracy checks.</p>
                </div>
              </div>
            </div>

            <ThresholdSlider
              id="gold_threshold"
              label="Gold Benchmark Accuracy"
              description="Minimum agreement score against verified expert ground-truth samples."
              tooltipHelp="Annotators below this threshold are automatically flagged for review."
              min={50}
              max={100}
              step={1}
              value={settings.gold_threshold}
              recommended={90}
              unit="%"
              onChange={(val) => handleSliderChange('gold_threshold', val)}
            />

            <ThresholdSlider
              id="kappa_threshold"
              label="Cohen's Kappa Reliability Baseline"
              description="Minimum pairwise consensus metric accounting for chance agreement."
              tooltipHelp="Overall project kappa dropping below this value triggers quality alerts."
              min={0.3}
              max={1.0}
              step={0.05}
              value={settings.kappa_threshold}
              displayValue={settings.kappa_threshold.toFixed(2)}
              recommended={0.7}
              unit=""
              onChange={(val) => handleSliderChange('kappa_threshold', val)}
            />
          </div>

          {/* Group 2: Anomaly & Latent Space */}
          <div className="card" style={{ marginBottom: 0 }}>
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <div className="stat-card-icon-wrap">
                  <Activity size={15} />
                </div>
                <div>
                  <h2>Behavioral &amp; Embedding Outliers</h2>
                  <p>Telemetry metrics monitoring timing cadences and vector drift.</p>
                </div>
              </div>
            </div>

            <ThresholdSlider
              id="behavior_threshold"
              label="Behavioral Consistency Baseline"
              description="Minimum score checking annotation duration variance and click cadences."
              tooltipHelp="Protects against rapid random clicking or bot-like speed anomalies."
              min={50}
              max={100}
              step={1}
              value={settings.behavior_threshold}
              recommended={75}
              unit="%"
              onChange={(val) => handleSliderChange('behavior_threshold', val)}
            />

            <ThresholdSlider
              id="embedding_threshold"
              label="Embedding Cluster Proximity"
              description="Cosine similarity bound relative to category cluster centroid."
              tooltipHelp="Flags label instances whose text semantics diverge drastically from the category center."
              min={50}
              max={100}
              step={1}
              value={settings.embedding_threshold}
              recommended={80}
              unit="%"
              onChange={(val) => handleSliderChange('embedding_threshold', val)}
            />
          </div>
        </div>
      )}
    </div>
  );
}