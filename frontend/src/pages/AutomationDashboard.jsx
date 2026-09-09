import React, { useEffect, useState } from 'react';
import {
  assignReroute,
  fetchPendingReroutes,
} from '../services/reroutingService';
import {
  Bot,
  Clock,
  CheckCircle2,
  AlertOctagon,
  RefreshCw,
  UserCheck,
  X,
  Send,
  Sparkles,
} from 'lucide-react';

function AutomationDashboard() {
  const [reroutes, setReroutes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [assigningItemId, setAssigningItemId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Active modal for reassignment
  const [activeItem, setActiveItem] = useState(null);
  const [annotatorId, setAnnotatorId] = useState('');
  const [reason, setReason] = useState('');

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
        err.response?.data?.detail || 'Failed to load pending automated reroutes.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReroutes();
  }, []);

  function openAssignModal(item) {
    setActiveItem(item);
    setAnnotatorId('');
    setReason('');
    setError('');
    setSuccess('');
  }

  function closeAssignModal() {
    setActiveItem(null);
    setAnnotatorId('');
    setReason('');
  }

  async function handleAssignSubmit(e) {
    e.preventDefault();
    if (!activeItem) return;

    if (!annotatorId) {
      setError('Please enter an Annotator ID before submitting the assignment.');
      return;
    }

    try {
      setAssigningItemId(activeItem.item_id);
      setError('');
      setSuccess('');

      const result = await assignReroute(
        activeItem.item_id,
        annotatorId,
        reason || ''
      );

      setSuccess(
        result.message || `Item #${activeItem.item_id} reassigned successfully to Annotator #${annotatorId}.`
      );

      closeAssignModal();
      await loadReroutes();
    } catch (err) {
      console.error('Failed to assign reroute:', err);
      setError(err.response?.data?.detail || 'Failed to reassign task.');
    } finally {
      setAssigningItemId(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Automation &amp; Rerouting</h1>
          <p className="page-subtitle">
            Autonomous task routing for low-trust or anomalous annotations requiring senior annotator reassignment.
          </p>
        </div>

        <button
          type="button"
          className="secondary-btn"
          onClick={loadReroutes}
          disabled={loading}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Tasks</span>
        </button>
      </div>

      {error && (
        <div className="alert">
          <AlertOctagon size={16} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert-success">
          <CheckCircle2 size={16} />
          <span>{success}</span>
        </div>
      )}

      {/* Top Stat Summary Tiles */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Pending Reroutes</span>
            <div className="stat-icon" style={{ background: 'var(--status-risk-bg)', color: 'var(--status-risk-text)' }}>
              <Clock size={16} />
            </div>
          </div>
          <div className="stat-value">{total}</div>
          <div className="stat-subtext">Tasks awaiting re-labeling assignment</div>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-label">Automation Engine</span>
            <div className="stat-icon">
              <Bot size={16} />
            </div>
          </div>
          <div className="stat-value" style={{ fontSize: '1.4rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="project-status-dot" />
            <span>Active</span>
          </div>
          <div className="stat-subtext">
            <span className="badge badge-good">Realtime Monitoring</span>
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div>
              <h2>Flagged Reroute Queue</h2>
              <p>Items flagged by scoring signals awaiting expert annotator reassignment.</p>
            </div>
            <span className="badge badge-info">{total} pending</span>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '1.5rem' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : reroutes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon" style={{ background: 'var(--status-good-bg)', color: 'var(--status-good-text)' }}>
              <CheckCircle2 size={26} />
            </div>
            <h3>Zero Pending Reroutes</h3>
            <p>All flagged items have been reassigned or resolved. The queue is completely clear.</p>
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Item ID</th>
                  <th>Original Annotator</th>
                  <th>Trust Score</th>
                  <th>Flag Rationale</th>
                  <th>Annotation Content</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right', paddingRight: '1.5rem' }}>Action</th>
                </tr>
              </thead>

              <tbody>
                {reroutes.map((item) => (
                  <tr key={item.item_id}>
                    <td>
                      <span className="mono-cell" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        #{item.item_id}
                      </span>
                      <div
                        className="mono-cell"
                        style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}
                      >
                        {item.external_id || 'Internal item'}
                      </div>
                    </td>

                    <td>
                      <strong>
                        {item.original_annotator_name || `Annotator ${item.original_annotator_id}`}
                      </strong>
                      <div
                        className="mono-cell"
                        style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}
                      >
                        ID #{item.original_annotator_id}
                      </div>
                    </td>

                    <td>
                      <span className="badge badge-risk mono-cell">
                        {(Number(item.trust_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>

                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>
                        {item.reason || 'Anomalous score below threshold'}
                      </span>
                    </td>

                    <td style={{ maxWidth: '280px' }}>
                      <div
                        style={{
                          fontSize: '0.78rem',
                          color: 'var(--text-secondary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          fontFamily: 'var(--font-mono)',
                          background: 'var(--bg-subtle)',
                          padding: '3px 6px',
                          borderRadius: 'var(--radius-sm)',
                        }}
                        title={item.content?.text || JSON.stringify(item.content)}
                      >
                        {item.content?.text || JSON.stringify(item.content)}
                      </div>
                    </td>

                    <td>
                      <span className="badge badge-medium">
                        {item.reroute_status || 'PENDING'}
                      </span>
                    </td>

                    <td style={{ textAlign: 'right', paddingRight: '1.5rem' }}>
                      <button
                        type="button"
                        className="primary-btn"
                        onClick={() => openAssignModal(item)}
                        style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                      >
                        <UserCheck size={13} />
                        <span>Reassign</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Clean Reassignment Modal */}
      {activeItem && (
        <div className="modal-backdrop" onClick={closeAssignModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Reassign Task #{activeItem.item_id}</h2>
                <p>Route this task to a qualified annotator for verified review.</p>
              </div>
              <button
                type="button"
                className="modal-close"
                onClick={closeAssignModal}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAssignSubmit} className="modal-body">
              <div
                style={{
                  background: 'var(--bg-subtle)',
                  padding: '0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1.25rem',
                  fontSize: '0.8rem',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Original Annotator:</span>
                  <strong>{activeItem.original_annotator_name || `ID #${activeItem.original_annotator_id}`}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Trust Score:</span>
                  <span className="badge badge-risk mono-cell">
                    {(Number(activeItem.trust_score || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Flag Reason:</span>
                  <span>{activeItem.reason || 'Threshold breach'}</span>
                </div>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="target-annotator-id">Target Annotator ID *</label>
                <input
                  id="target-annotator-id"
                  type="number"
                  min="1"
                  placeholder="e.g. 104"
                  value={annotatorId}
                  onChange={(e) => setAnnotatorId(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="assign-reason">Routing Note / Reason (Optional)</label>
                <input
                  id="assign-reason"
                  type="text"
                  placeholder="e.g. Routed to Senior Annotator for tie-breaker"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={closeAssignModal}
                  disabled={assigningItemId === activeItem.item_id}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={assigningItemId === activeItem.item_id || !annotatorId}
                >
                  <Send size={13} />
                  <span>
                    {assigningItemId === activeItem.item_id ? 'Assigning...' : 'Confirm Assignment'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AutomationDashboard;