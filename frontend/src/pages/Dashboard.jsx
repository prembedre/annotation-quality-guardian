import { useEffect, useState } from 'react';
import api from '../services/api';

const PROJECT_ID = 1;

function formatPercent(value) {
  if (value == null) {
    return 'N/A';
  }

  return `${(value * 100).toFixed(1)}%`;
}

function formatDuration(value) {
  if (value == null) {
    return 'N/A';
  }

  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)} s`;
  }

  return `${value.toFixed(0)} ms`;
}

function getTrustClass(value) {
  if (value == null) {
    return '';
  }

  if (value >= 0.85) {
    return 'dashboard-good';
  }

  if (value >= 0.7) {
    return 'dashboard-medium';
  }

  return 'dashboard-low';
}

function AgreementHeatmap({ data }) {
  if (!data || !data.annotators?.length) {
    return (
      <div className="dashboard-empty">
        No agreement data available.
      </div>
    );
  }

  const getCell = (rowIndex, columnIndex) => {
    const value = data.matrix?.[rowIndex]?.[columnIndex];

    if (value == null) {
      return 'N/A';
    }

    return formatPercent(value);
  };

  const getCellClass = (value) => {
    if (value == null) {
      return 'heatmap-cell heatmap-na';
    }

    if (value >= 0.85) {
      return 'heatmap-cell heatmap-high';
    }

    if (value >= 0.7) {
      return 'heatmap-cell heatmap-medium';
    }

    return 'heatmap-cell heatmap-low';
  };

  const getOverlap = (rowIndex, columnIndex) => {
    const rowAnnotatorId = data.annotator_ids?.[rowIndex];
    const columnAnnotatorId = data.annotator_ids?.[columnIndex];

    const cell = data.cells?.find(
      (item) =>
        item.annotator_a_id === rowAnnotatorId &&
        item.annotator_b_id === columnAnnotatorId
    );

    return cell?.overlap_count ?? null;
  };

  return (
    <div className="heatmap-wrapper">
      <div
        className="heatmap-grid"
        style={{
          gridTemplateColumns: `110px repeat(${data.annotators.length}, minmax(85px, 1fr))`,
        }}
      >
        <div className="heatmap-corner" />

        {data.annotators.map((name, index) => (
          <div
            key={`column-${data.annotator_ids[index]}`}
            className="heatmap-label"
          >
            {name}
          </div>
        ))}

        {data.annotators.map((rowName, rowIndex) => (
          <div
            key={`row-${data.annotator_ids[rowIndex]}`}
            className="heatmap-row"
          >
            <div className="heatmap-label heatmap-row-label">
              {rowName}
            </div>

            {data.annotators.map((columnName, columnIndex) => {
              const value = data.matrix?.[rowIndex]?.[columnIndex];
              const overlap = getOverlap(rowIndex, columnIndex);

              return (
                <div
                  key={`${rowIndex}-${columnIndex}`}
                  className={getCellClass(value)}
                  title={`${rowName} ↔ ${columnName}: ${
                    value == null ? 'N/A' : formatPercent(value)
                  }${
                    overlap != null
                      ? ` • ${overlap} overlapping items`
                      : ''
                  }`}
                >
                  {getCell(rowIndex, columnIndex)}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <div className="heatmap-legend">
        <span>
          <span className="legend-box heatmap-low" />
          &lt; 70%
        </span>

        <span>
          <span className="legend-box heatmap-medium" />
          70–84%
        </span>

        <span>
          <span className="legend-box heatmap-high" />
          85%+
        </span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardTotal, setLeaderboardTotal] = useState(0);
  const [heatmap, setHeatmap] = useState(null);

  const [loadingLeaderboard, setLoadingLeaderboard] = useState(true);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);

  const [leaderboardError, setLeaderboardError] = useState('');
  const [heatmapError, setHeatmapError] = useState('');

  useEffect(() => {
    async function loadLeaderboard() {
      try {
        setLoadingLeaderboard(true);
        setLeaderboardError('');

        const response = await api.get(
          `/dashboard/leaderboard?project_id=${PROJECT_ID}`
        );

        setLeaderboard(response.data.leaderboard || []);
        setLeaderboardTotal(response.data.total_annotators || 0);
      } catch (error) {
        console.error('Failed to load leaderboard:', error);

        setLeaderboardError(
          error.response?.data?.detail ||
            'Failed to load annotator leaderboard.'
        );
      } finally {
        setLoadingLeaderboard(false);
      }
    }

    async function loadHeatmap() {
      try {
        setLoadingHeatmap(true);
        setHeatmapError('');

        const response = await api.get(
          `/dashboard/agreement-heatmap?project_id=${PROJECT_ID}`
        );

        setHeatmap(response.data);
      } catch (error) {
        console.error('Failed to load agreement heatmap:', error);

        setHeatmapError(
          error.response?.data?.detail ||
            'Failed to load agreement heatmap.'
        );
      } finally {
        setLoadingHeatmap(false);
      }
    }

    loadLeaderboard();
    loadHeatmap();
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h1>Quality Dashboard</h1>

          <p>
            Monitor annotator performance and inter-annotator agreement.
          </p>
        </div>

        <div className="dashboard-project">
          Project {PROJECT_ID}
        </div>
      </div>

      <section className="dashboard-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Annotator Leaderboard</h2>

            <p>
              Ranked by aggregate trust score, with quality and
              productivity metrics.
            </p>
          </div>

          <div className="dashboard-count">
            {leaderboardTotal} annotators
          </div>
        </div>

        {loadingLeaderboard && (
          <div className="dashboard-loading">
            Loading leaderboard...
          </div>
        )}

        {leaderboardError && (
          <div className="dashboard-error">
            {leaderboardError}
          </div>
        )}

        {!loadingLeaderboard &&
          !leaderboardError &&
          leaderboard.length === 0 && (
            <div className="dashboard-empty">
              No annotator data available.
            </div>
          )}

        {!loadingLeaderboard &&
          !leaderboardError &&
          leaderboard.length > 0 && (
            <div className="dashboard-table-wrapper">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Annotator</th>
                    <th>Annotations</th>
                    <th>Gold Accuracy</th>
                    <th>Confidence</th>
                    <th>Avg Duration</th>
                    <th>Trust Score</th>
                  </tr>
                </thead>

                <tbody>
                  {leaderboard.map((item) => (
                    <tr key={item.annotator_id}>
                      <td>
                        <span className="rank-badge">
                          #{item.rank}
                        </span>
                      </td>

                      <td>
                        <strong>{item.annotator_name}</strong>
                      </td>

                      <td>{item.total_annotations}</td>

                      <td>
                        {formatPercent(item.gold_accuracy)}
                      </td>

                      <td>
                        {formatPercent(item.avg_confidence)}
                      </td>

                      <td>
                        {formatDuration(item.avg_duration_ms)}
                      </td>

                      <td>
                        <span
                          className={`trust-badge ${getTrustClass(
                            item.trust_score
                          )}`}
                        >
                          {formatPercent(item.trust_score)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
      </section>

      <section className="dashboard-card">
        <div className="dashboard-card-header">
          <div>
            <h2>Inter-Annotator Agreement</h2>

            <p>
              Pairwise agreement between annotators on overlapping items.
            </p>
          </div>

          <div className="dashboard-kappa">
            <span>Overall Kappa</span>

            <strong>
              {heatmap?.overall_kappa == null
                ? 'N/A'
                : heatmap.overall_kappa.toFixed(3)}
            </strong>
          </div>
        </div>

        {loadingHeatmap && (
          <div className="dashboard-loading">
            Loading agreement heatmap...
          </div>
        )}

        {heatmapError && (
          <div className="dashboard-error">
            {heatmapError}
          </div>
        )}

        {!loadingHeatmap && !heatmapError && (
          <AgreementHeatmap data={heatmap} />
        )}
      </section>
    </div>
  );
}