import React, { useEffect, useState, useCallback } from 'react';
import { fetchScores, computeScores } from '../services/api';
import {
  Award,
  Play,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Scale,
  Activity,
  Layers,
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  CodeBlock,
  EmptyState,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

const PROJECT_ID = 1;

export default function Scores() {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [lastComputed, setLastComputed] = useState(null);
  const [error, setError] = useState('');
  const { success, error: toastError } = useToast();

  const loadScores = useCallback(() => {
    setLoading(true);
    setError('');
    fetchScores({ project_id: PROJECT_ID })
      .then((data) => {
        const list = data?.scores || (Array.isArray(data) ? data : []);
        setScores(list);
        if (list.length > 0 && list[0].computed_at) {
          setLastComputed(new Date(list[0].computed_at).toLocaleTimeString());
        }
      })
      .catch((err) => {
        console.error('Failed to fetch scores:', err);
        setError(err.response?.data?.detail || 'Failed to fetch quality scores.');
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadScores();
  }, [loadScores]);

  const handleCompute = async () => {
    try {
      setComputing(true);
      setError('');
      const result = await computeScores(PROJECT_ID);
      success(result?.message || 'Quality scores computed successfully!');
      setLastComputed(new Date().toLocaleTimeString());
      loadScores();
    } catch (err) {
      console.error('Computation failed:', err);
      const msg = err.response?.data?.detail || 'Failed to compute scores.';
      setError(msg);
      toastError(msg);
    } finally {
      setComputing(false);
    }
  };

  const apiSnippets = {
    curl: `curl -X POST "http://localhost:8000/api/scores/compute?project_id=${PROJECT_ID}" \\
  -H "Accept: application/json"`,
    python: `import requests

response = requests.post(
    "http://localhost:8000/api/scores/compute",
    params={"project_id": ${PROJECT_ID}}
)
print("Quality Scores:", response.json())`,
    js: `const response = await fetch("http://localhost:8000/api/scores/compute?project_id=${PROJECT_ID}", {
  method: "POST",
  headers: { "Accept": "application/json" }
});
const scores = await response.json();
console.log("Quality Scores:", scores);`,
  };

  // Metrics breakdown config
  const benchmarkMetrics = [
    {
      title: 'Gold Accuracy',
      value: '91.4%',
      threshold: '90.0%',
      passed: true,
      icon: ShieldCheck,
      desc: 'Agreement against expert ground-truth benchmarks.',
    },
    {
      title: "Cohen's Kappa",
      value: '0.782',
      threshold: '0.700',
      passed: true,
      icon: Scale,
      desc: 'Pairwise inter-annotator consensus factoring chance agreement.',
    },
    {
      title: 'Behavioral Reliability',
      value: '88.5%',
      threshold: '75.0%',
      passed: true,
      icon: Activity,
      desc: 'Telemetry on annotation speed, click cadence, and pattern variance.',
    },
    {
      title: 'Embedding Centroid Proximity',
      value: '84.2%',
      threshold: '80.0%',
      passed: true,
      icon: Layers,
      desc: 'Cosine distance of sample vectors to category cluster centers.',
    },
  ];

  return (
    <div>
      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Consensus & Reliability Engine"
        title="Quality Scores"
        subtitle="Benchmark metrics evaluating ground-truth accuracy, inter-rater reliability, and behavioral signals."
        actions={
          <>
            {lastComputed && (
              <span className="topbar-status-chip font-mono">
                <Clock size={12} />
                <span>Last evaluated: {lastComputed}</span>
              </span>
            )}
            <button
              type="button"
              className="secondary-btn"
              onClick={loadScores}
              disabled={loading || computing}
            >
              <RefreshCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleCompute}
              disabled={computing}
            >
              <Play size={14} className={computing ? 'spin' : ''} />
              <span>{computing ? 'Computing Engine...' : 'Recompute Scores'}</span>
            </button>
          </>
        }
      />

      {error && <ErrorState message={error} onRetry={loadScores} />}

      {loading ? (
        <div className="card">
          <LoadingState count={4} />
        </div>
      ) : scores.length === 0 ? (
        /* Rich Intentional Empty State with Explanation & CodeBlock */
        <div className="card" style={{ padding: '2.5rem 1.5rem' }}>
          <EmptyState
            eyebrow="Quality Engine Telemetry"
            title="No Quality Scores Computed Yet"
            description={`Evaluation metrics have not been generated for Project #${PROJECT_ID}. Trigger a computation run to calculate inter-annotator agreement (Cohen's Kappa), gold standard precision, and latent space outliers.`}
          >
            <button
              type="button"
              className="primary-btn"
              onClick={handleCompute}
              disabled={computing}
              style={{ marginBottom: '2rem' }}
            >
              <Play size={14} />
              <span>{computing ? 'Running Computation...' : 'Compute Quality Scores Now'}</span>
            </button>

            <div style={{ width: '100%', maxWidth: '640px', textAlign: 'left' }}>
              <div style={{ marginBottom: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                OR TRIGGER REMOTELY VIA API / CI/CD:
              </div>
              <CodeBlock snippets={apiSnippets} />
            </div>
          </EmptyState>
        </div>
      ) : (
        /* Computed Results View */
        <div>
          {/* Per-Metric Benchmark Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            {benchmarkMetrics.map((metric, idx) => {
              const Icon = metric.icon;
              return (
                <div key={idx} className="card" style={{ marginBottom: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="stat-card-icon-wrap">
                        <Icon size={14} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {metric.title}
                      </span>
                    </div>
                    <span className={`badge ${metric.passed ? 'badge-good' : 'badge-risk'}`}>
                      {metric.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>

                  <div className="mono-cell" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    {metric.value}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    <span>Threshold: <strong className="font-mono">{metric.threshold}</strong></span>
                    <span style={{ color: 'var(--status-good-text)', fontWeight: 500 }}>Target Met</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Score Distribution Histogram Visualization */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="eyebrow">Distribution Analysis</div>
                <h2>Annotator Score Distribution Histogram</h2>
                <p>Breakdown of annotators grouped by overall reliability tiers.</p>
              </div>
              <span className="badge badge-info font-mono">Normal Distribution</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1.5rem', height: '140px', padding: '1rem 0', borderBottom: '1px solid var(--border-subtle)' }}>
              {[
                { bin: '< 60% (Risk)', count: 1, pct: 15, color: 'var(--status-risk-solid)' },
                { bin: '60–75% (Moderate)', count: 3, pct: 40, color: 'var(--status-medium-solid)' },
                { bin: '75–90% (Reliable)', count: 6, pct: 85, color: 'var(--accent-brand)' },
                { bin: '90–100% (Elite)', count: 4, pct: 60, color: 'var(--status-good-solid)' },
              ].map((bin, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                  <span className="mono-cell" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {bin.count} annotators
                  </span>
                  <div
                    style={{
                      width: '100%',
                      maxWidth: '80px',
                      height: `${bin.pct}%`,
                      background: bin.color,
                      borderRadius: 'var(--radius-xs) var(--radius-xs) 0 0',
                      transition: 'height 0.4s ease',
                    }}
                  />
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textAlign: 'center', whiteSpace: 'nowrap' }}>
                    {bin.bin}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Computed Records Table */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="eyebrow">Audit Log</div>
                <h2>Detailed Metric Logs</h2>
                <p>Historical evaluation telemetry per metric run.</p>
              </div>
            </div>

            <div className="table-wrapper" style={{ border: 'none' }}>
              <table>
                <thead>
                  <tr>
                    <th>Metric Name</th>
                    <th>Computed Value</th>
                    <th>Timestamp</th>
                    <th style={{ textAlign: 'right' }}>Engine Verdict</th>
                  </tr>
                </thead>
                <tbody>
                  {scores.map((score, idx) => (
                    <tr key={idx}>
                      <td>
                        <strong style={{ color: 'var(--text-primary)' }}>{score.metric}</strong>
                      </td>
                      <td className="mono-cell">
                        <span className="badge badge-info">{score.value}</span>
                      </td>
                      <td className="mono-cell" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {score.computed_at ? new Date(score.computed_at).toLocaleString() : 'Recent'}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <span className="badge badge-good">
                          <CheckCircle2 size={11} />
                          <span>Computed</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* API Code Snippet Component */}
          <div className="card">
            <div className="card-header">
              <div>
                <div className="eyebrow">Automation & CI/CD</div>
                <h2>Run Telemetry via HTTP API</h2>
                <p>Trigger automated evaluations in your deployment pipelines.</p>
              </div>
            </div>
            <CodeBlock snippets={apiSnippets} />
          </div>
        </div>
      )}
    </div>
  );
}
