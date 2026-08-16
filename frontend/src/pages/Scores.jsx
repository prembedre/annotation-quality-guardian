import React, { useEffect, useState } from 'react';
import { fetchScores } from '../services/api';

function Scores() {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScores()
      .then((data) => setScores(data.scores || []))
      .catch((err) => console.error('Failed to fetch scores:', err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="page-title">Quality Scores</h1>

      {loading ? (
        <p style={{ color: 'var(--color-text-muted)' }}>Loading scores...</p>
      ) : scores.length === 0 ? (
        <div className="card">
          <p style={{ color: 'var(--color-text-muted)' }}>
            No scores computed yet. Trigger a computation via the API.
          </p>
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>Metric</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>Value</th>
              <th style={{ textAlign: 'left', padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>Computed At</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((score, idx) => (
              <tr key={idx}>
                <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>{score.metric}</td>
                <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>{score.value}</td>
                <td style={{ padding: '0.75rem', borderBottom: '1px solid var(--color-border)' }}>{score.computed_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default Scores;
