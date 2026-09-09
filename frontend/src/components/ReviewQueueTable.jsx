import React, { useState } from 'react';
import { ScoreIndicator } from './ScoreIndicator';
import { FlagStatusBadge } from './FlagStatusBadge';
import { Check, Edit3, AlertTriangle, X, CornerDownRight } from 'lucide-react';

function getFlagReason(item, breakdown) {
  if (!item.flagged) {
    return 'No active flag';
  }
  if (breakdown.flag_reason) {
    return breakdown.flag_reason;
  }
  if (item.trust_score != null && item.trust_score < 0.6) {
    return 'Trust score below threshold (60%)';
  }
  if (breakdown.anomaly_flag === true) {
    return 'Behavioral anomaly detected';
  }
  if (breakdown.is_outlier === true) {
    return 'Embedding outlier detected';
  }
  if (breakdown.gold != null && breakdown.gold < 0.5 && item.is_gold === true) {
    return 'Gold label mismatch';
  }
  return 'Quality issue detected';
}

function ReviewActions({ item, onResolve }) {
  const [showCorrect, setShowCorrect] = useState(false);
  const [correctLabel, setCorrectLabel] = useState('');
  const [notes, setNotes] = useState('');
  const [processing, setProcessing] = useState(false);

  async function handleAction(action) {
    if (!onResolve) return;

    if (action === 'correct' && !correctLabel.trim()) {
      window.alert('Please enter a corrected label.');
      return;
    }

    try {
      setProcessing(true);
      const payload = { action };

      if (action === 'correct') {
        payload.correct_label = correctLabel.trim();
      }
      if (notes.trim()) {
        payload.notes = notes.trim();
      }

      await onResolve(item.item_id, payload);
      setShowCorrect(false);
      setCorrectLabel('');
      setNotes('');
    } catch (error) {
      console.error('Reviewer action failed:', error);
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* Segmented compact action group */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
        }}
      >
        <button
          type="button"
          onClick={() => handleAction('confirm')}
          disabled={processing}
          title="Confirm Annotation"
          style={{
            background: 'none',
            border: 'none',
            borderRight: '1px solid var(--border-subtle)',
            padding: '5px 9px',
            fontSize: '0.75rem',
            color: 'var(--status-good-text)',
            borderRadius: 0,
          }}
        >
          <Check size={13} />
          <span>Confirm</span>
        </button>

        <button
          type="button"
          onClick={() => setShowCorrect((prev) => !prev)}
          disabled={processing}
          title="Correct Label"
          style={{
            background: showCorrect ? 'var(--bg-surface-hover)' : 'none',
            border: 'none',
            borderRight: '1px solid var(--border-subtle)',
            padding: '5px 9px',
            fontSize: '0.75rem',
            color: 'var(--status-medium-text)',
            borderRadius: 0,
          }}
        >
          <Edit3 size={13} />
          <span>{showCorrect ? 'Cancel' : 'Correct'}</span>
        </button>

        <button
          type="button"
          onClick={() => handleAction('escalate')}
          disabled={processing}
          title="Escalate Issue"
          style={{
            background: 'none',
            border: 'none',
            padding: '5px 9px',
            fontSize: '0.75rem',
            color: 'var(--status-risk-text)',
            borderRadius: 0,
          }}
        >
          <AlertTriangle size={13} />
          <span>Escalate</span>
        </button>
      </div>

      {/* Inline Correction Form */}
      {showCorrect && (
        <div
          style={{
            marginTop: '4px',
            padding: '12px',
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-sm)',
            width: '240px',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div style={{ marginBottom: '8px' }}>
            <label
              htmlFor={`correct-label-${item.item_id}`}
              style={{ fontSize: '0.7rem', marginBottom: '3px' }}
            >
              Corrected Label *
            </label>
            <input
              id={`correct-label-${item.item_id}`}
              type="text"
              value={correctLabel}
              onChange={(e) => setCorrectLabel(e.target.value)}
              placeholder="e.g. valid_category"
              disabled={processing}
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.55rem' }}
              autoFocus
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label
              htmlFor={`reviewer-notes-${item.item_id}`}
              style={{ fontSize: '0.7rem', marginBottom: '3px' }}
            >
              Reviewer Notes
            </label>
            <textarea
              id={`reviewer-notes-${item.item_id}`}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Rationale / observation..."
              rows={2}
              disabled={processing}
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.55rem' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setShowCorrect(false)}
              disabled={processing}
              style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={() => handleAction('correct')}
              disabled={processing}
              style={{ padding: '0.25rem 0.65rem', fontSize: '0.72rem' }}
            >
              <CornerDownRight size={12} />
              <span>{processing ? 'Saving...' : 'Apply'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function ReviewQueueTable({
  items = [],
  loading = false,
  onResolve,
}) {
  if (loading) {
    return (
      <div className="card">
        <div style={{ padding: '1rem 0' }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="skeleton-row" />
          ))}
        </div>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="card">
        <div className="empty-state">
          <div className="empty-state-icon">
            <Check size={24} />
          </div>
          <h3>All Caught Up</h3>
          <p>No items match the current review filters.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Gold</th>
              <th>Kappa</th>
              <th>Behavioral</th>
              <th>Embedding</th>
              <th>Trust Score</th>
              <th>Flag Status</th>
              <th>Why Flagged</th>
              <th style={{ textAlign: 'right', paddingRight: '1.5rem' }}>Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.map((item) => {
              const breakdown = item.trust_score_breakdown || {};
              const flagReason = getFlagReason(item, breakdown);

              return (
                <tr key={item.item_id}>
                  {/* ID */}
                  <td>
                    <span className="mono-cell" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                      #{item.item_id}
                    </span>
                  </td>

                  {/* Gold */}
                  <td>
                    <ScoreIndicator
                      trustScore={breakdown.gold != null ? breakdown.gold * 100 : null}
                    />
                  </td>

                  {/* Kappa */}
                  <td>
                    <ScoreIndicator
                      trustScore={breakdown.agreement != null ? breakdown.agreement * 100 : null}
                    />
                  </td>

                  {/* Behavioral */}
                  <td>
                    <ScoreIndicator
                      trustScore={breakdown.behavioral != null ? breakdown.behavioral * 100 : null}
                    />
                  </td>

                  {/* Embedding */}
                  <td>
                    <ScoreIndicator
                      trustScore={breakdown.embedding != null ? breakdown.embedding * 100 : null}
                    />
                  </td>

                  {/* Overall Trust Score */}
                  <td>
                    <ScoreIndicator
                      trustScore={item.trust_score != null ? item.trust_score * 100 : null}
                    />
                  </td>

                  {/* Flag Status */}
                  <td>
                    <FlagStatusBadge isFlagged={item.flagged} />
                  </td>

                  {/* Flag Reason */}
                  <td>
                    <span
                      style={{
                        fontSize: '0.8rem',
                        color: item.flagged ? 'var(--text-primary)' : 'var(--text-muted)',
                      }}
                    >
                      {flagReason}
                    </span>
                  </td>

                  {/* Actions */}
                  <td style={{ textAlign: 'right', verticalAlign: 'top', paddingRight: '1.5rem' }}>
                    <div style={{ display: 'inline-block', textAlign: 'left' }}>
                      <ReviewActions item={item} onResolve={onResolve} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ReviewQueueTable;
