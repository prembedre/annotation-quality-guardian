import React, { useEffect, useState } from 'react';
import { fetchScores, computeScores } from '../services/api';
import { Award, Play, RefreshCw, Terminal, CheckCircle2 } from 'lucide-react';

const PROJECT_ID = 1;

function Scores() {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadScores = () => {
    setLoading(true);
    setError('');
    fetchScores({ project_id: PROJECT_ID })
      .then((data) => setScores(data?.scores || (Array.isArray(data) ? data : [])))
      .catch((err) => {
        console.error('Failed to fetch scores:', err);
        setError(err.response?.data?.detail || 'Failed to fetch scores.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadScores();
  }, []);

  const handleCompute = async () => {
    try {
      setComputing(true);
      setMessage('');
      setError('');
      const result = await computeScores(PROJECT_ID);
      setMessage(result?.message || 'Quality scores computed successfully!');
      loadScores();
    } catch (err) {
      console.error('Computation failed:', err);
      setError(err.response?.data?.detail || 'Failed to compute scores.');
    } finally {
      setComputing(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Quality Scores</h1>
          <p className="page-subtitle">
            Calculated quality benchmarks, inter-annotator agreement metrics, and gold reliability scores.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
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
            <Play size={14} />
            <span>{computing ? 'Computing...' : 'Compute Scores'}</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="alert-success">
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      {error && <div className="alert">{error}</div>}

      {loading ? (
        <div className="card">
          <div style={{ padding: '1rem 0' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        </div>
      ) : scores.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">
              <Award size={26} />
            </div>
            <h3>No Scores Computed Yet</h3>
            <p>
              Quality scores have not been generated for Project {PROJECT_ID}. Trigger a computation to evaluate annotator agreement, gold accuracy, and anomaly signals.
            </p>

            <button
              type="button"
              className="primary-btn"
              onClick={handleCompute}
              disabled={computing}
              style={{ marginBottom: '1.5rem' }}
            >
              <Play size={14} />
              <span>{computing ? 'Running Computation...' : 'Compute Quality Scores Now'}</span>
            </button>

            {/* API Code Snippet Help */}
            <div
              style={{
                width: '100%',
                maxWidth: '520px',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                textAlign: 'left',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  marginBottom: '0.5rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                }}
              >
                <Terminal size={14} />
                <span>Or run via HTTP API</span>
              </div>
              <pre
                className="mono-cell"
                style={{
                  background: 'var(--bg-base)',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.78rem',
                  color: 'var(--accent-200)',
                  overflowX: 'auto',
                }}
              >
                curl -X POST &quot;http://localhost:8000/api/scores/compute?project_id={PROJECT_ID}&quot;
              </pre>
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Metric Name</th>
                  <th>Value</th>
                  <th>Computed At</th>
                  <th style={{ textAlign: 'right', paddingRight: '1.5rem' }}>Status</th>
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
                    <td
                      className="mono-cell"
                      style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}
                    >
                      {score.computed_at ? new Date(score.computed_at).toLocaleString() : 'Recent'}
                    </td>
                    <td style={{ textAlign: 'right', paddingRight: '1.5rem' }}>
                      <span className="badge badge-good">Computed</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Scores;
