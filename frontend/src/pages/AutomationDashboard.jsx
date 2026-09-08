import React, { useEffect, useState } from 'react';
import {
  assignReroute,
  fetchPendingReroutes,
} from '../services/reroutingService';

function AutomationDashboard() {
  const [reroutes, setReroutes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [assigningItemId, setAssigningItemId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [selectedAnnotators, setSelectedAnnotators] = useState({});
  const [reasons, setReasons] = useState({});

  async function loadReroutes() {
    try {
      setLoading(true);
      setError('');

      const data = await fetchPendingReroutes();

      setReroutes(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load pending reroutes:', err);
      setError(
        err.response?.data?.detail ||
          'Failed to load pending automated reroutes.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReroutes();
  }, []);

  function handleAnnotatorChange(itemId, value) {
    setSelectedAnnotators((current) => ({
      ...current,
      [itemId]: value,
    }));
  }

  function handleReasonChange(itemId, value) {
    setReasons((current) => ({
      ...current,
      [itemId]: value,
    }));
  }

  async function handleAssign(item) {
    const annotatorId = selectedAnnotators[item.item_id];

    if (!annotatorId) {
      setError('Please enter the annotator ID before assigning the task.');
      setSuccess('');
      return;
    }

    try {
      setAssigningItemId(item.item_id);
      setError('');
      setSuccess('');

      const result = await assignReroute(
        item.item_id,
        annotatorId,
        reasons[item.item_id] || ''
      );

      setSuccess(
        result.message ||
          `Item ${item.item_id} was successfully reassigned.`
      );

      await loadReroutes();

      setSelectedAnnotators((current) => {
        const next = { ...current };
        delete next[item.item_id];
        return next;
      });

      setReasons((current) => {
        const next = { ...current };
        delete next[item.item_id];
        return next;
      });
    } catch (err) {
      console.error('Failed to assign reroute:', err);
      setError(
        err.response?.data?.detail ||
          'Failed to reassign the task.'
      );
      setSuccess('');
    } finally {
      setAssigningItemId(null);
    }
  }

  return (
    <div className="automation-page">
      <div className="page-header">
        <div>
          <h2>Automation Dashboard</h2>
          <p>
            Monitor tasks identified for automatic reassignment and manage
            pending reroutes.
          </p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadReroutes}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="automation-summary">
        <div className="automation-stat-card">
          <span className="stat-label">Pending Reroutes</span>
          <strong>{total}</strong>
          <span className="stat-help">
            Tasks waiting for reassignment
          </span>
        </div>

        <div className="automation-stat-card">
          <span className="stat-label">Automation Status</span>
          <strong>Active</strong>
          <span className="stat-help">
            Monitoring flagged tasks
          </span>
        </div>
      </div>

      <section className="automation-card">
        <div className="section-heading">
          <div>
            <h3>Pending Automated Reroutes</h3>
            <p>
              Tasks flagged by the quality system for reassignment.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="empty-state">
            Loading pending reroutes...
          </div>
        ) : reroutes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✓</div>
            <h4>No pending reroutes</h4>
            <p>
              There are currently no tasks waiting for reassignment.
            </p>
          </div>
        ) : (
          <div className="automation-table-wrapper">
            <table className="automation-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Original Annotator</th>
                  <th>Trust Score</th>
                  <th>Reason</th>
                  <th>Content</th>
                  <th>Status</th>
                  <th>Reassign</th>
                </tr>
              </thead>

              <tbody>
                {reroutes.map((item) => (
                  <tr key={item.item_id}>
                    <td>
                      <strong>#{item.item_id}</strong>
                      <div className="muted-text">
                        {item.external_id || 'Internal item'}
                      </div>
                    </td>

                    <td>
                      <strong>
                        {item.original_annotator_name ||
                          `Annotator ${item.original_annotator_id}`}
                      </strong>
                      <div className="muted-text">
                        ID: {item.original_annotator_id}
                      </div>
                    </td>

                    <td>
                      <span className="trust-score-badge">
                        {(Number(item.trust_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>

                    <td>
                      <span className="reason-text">
                        {item.reason || 'No reason provided'}
                      </span>
                    </td>

                    <td>
                      <div className="content-preview">
                        {item.content?.text ||
                          JSON.stringify(item.content)}
                      </div>
                    </td>

                    <td>
                      <span
                        className={`status-badge status-${String(
                          item.reroute_status || 'PENDING'
                        ).toLowerCase()}`}
                      >
                        {item.reroute_status || 'PENDING'}
                      </span>
                    </td>

                    <td>
                      <div className="assign-controls">
                        <input
                          type="number"
                          min="1"
                          placeholder="Annotator ID"
                          value={
                            selectedAnnotators[item.item_id] || ''
                          }
                          onChange={(event) =>
                            handleAnnotatorChange(
                              item.item_id,
                              event.target.value
                            )
                          }
                        />

                        <input
                          type="text"
                          placeholder="Optional reason"
                          value={reasons[item.item_id] || ''}
                          onChange={(event) =>
                            handleReasonChange(
                              item.item_id,
                              event.target.value
                            )
                          }
                        />

                        <button
                          type="button"
                          className="primary-button"
                          onClick={() => handleAssign(item)}
                          disabled={
                            assigningItemId === item.item_id
                          }
                        >
                          {assigningItemId === item.item_id
                            ? 'Assigning...'
                            : 'Assign'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default AutomationDashboard;