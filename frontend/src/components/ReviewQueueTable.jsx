import React, { useState } from 'react';
import { ScoreIndicator } from './ScoreIndicator';

function getFlagReason(item, breakdown) {
  // If the item is not currently flagged, there is no active issue.
  if (!item.flagged) {
    return 'No active flag';
  }

  // Use a specific reason supplied by the backend when available.
  if (breakdown.flag_reason) {
    return breakdown.flag_reason;
  }

  // Fallback reasons for flagged items.
  if (item.trust_score != null && item.trust_score < 0.6) {
    return 'Trust score below threshold (60%)';
  }

  if (breakdown.anomaly_flag === true) {
    return 'Behavioral anomaly detected';
  }

  if (breakdown.is_outlier === true) {
    return 'Embedding outlier detected';
  }

  if (
    breakdown.gold != null &&
    breakdown.gold < 0.5 &&
    item.is_gold === true
  ) {
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
    if (!onResolve) {
      return;
    }

    if (action === 'correct' && !correctLabel.trim()) {
      window.alert('Please enter a corrected label.');
      return;
    }

    try {
      setProcessing(true);

      const payload = {
        action,
      };

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
    <div
      style={{
        minWidth: '230px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '6px',
          flexWrap: 'wrap',
        }}
      >
        <button
          type="button"
          onClick={() => handleAction('confirm')}
          disabled={processing}
          style={{
            padding: '6px 10px',
            border: '1px solid #ccc',
            borderRadius: '5px',
            cursor: processing ? 'not-allowed' : 'pointer',
          }}
        >
          {processing ? '...' : 'Confirm'}
        </button>

        <button
          type="button"
          onClick={() => setShowCorrect((current) => !current)}
          disabled={processing}
          style={{
            padding: '6px 10px',
            border: '1px solid #ccc',
            borderRadius: '5px',
            cursor: processing ? 'not-allowed' : 'pointer',
          }}
        >
          {showCorrect ? 'Cancel' : 'Correct'}
        </button>

        <button
          type="button"
          onClick={() => handleAction('escalate')}
          disabled={processing}
          style={{
            padding: '6px 10px',
            border: '1px solid #ccc',
            borderRadius: '5px',
            cursor: processing ? 'not-allowed' : 'pointer',
          }}
        >
          {processing ? '...' : 'Escalate'}
        </button>
      </div>

      {showCorrect && (
        <div
          style={{
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            backgroundColor: '#f8f9fa',
          }}
        >
          <div style={{ marginBottom: '10px' }}>
            <label
              htmlFor={`correct-label-${item.item_id}`}
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '5px',
              }}
            >
              Corrected Label
            </label>

            <input
              id={`correct-label-${item.item_id}`}
              type="text"
              value={correctLabel}
              onChange={(event) =>
                setCorrectLabel(event.target.value)
              }
              placeholder="Enter correct label"
              disabled={processing}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '5px',
              }}
            />
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label
              htmlFor={`reviewer-notes-${item.item_id}`}
              style={{
                display: 'block',
                fontWeight: '600',
                marginBottom: '5px',
              }}
            >
              Reviewer Notes
            </label>

            <textarea
              id={`reviewer-notes-${item.item_id}`}
              value={notes}
              onChange={(event) =>
                setNotes(event.target.value)
              }
              placeholder="Optional reviewer notes"
              rows="3"
              disabled={processing}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '5px',
                resize: 'vertical',
              }}
            />
          </div>

          <button
            type="button"
            onClick={() => handleAction('correct')}
            disabled={processing}
            style={{
              padding: '7px 12px',
              border: '1px solid #ccc',
              borderRadius: '5px',
              cursor: processing ? 'not-allowed' : 'pointer',
            }}
          >
            {processing ? 'Saving...' : 'Save Correction'}
          </button>
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
        <p>Loading review queue...</p>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="card">
        <p>No review items found.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div
        style={{
          overflowX: 'auto',
          width: '100%',
        }}
      >
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
          }}
        >
          <thead>
            <tr>
              <th>Review ID</th>
              <th>Gold</th>
              <th>Kappa</th>
              <th>Behavioral</th>
              <th>Embedding</th>
              <th>Trust Score</th>
              <th>Flag</th>
              <th>Why Flagged</th>
              <th>Reviewer Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.map((item) => {
              const breakdown =
                item.trust_score_breakdown || {};

              const flagReason = getFlagReason(
                item,
                breakdown
              );

              return (
                <tr key={item.item_id}>
                  <td>{item.item_id}</td>

                  <td>
                    <ScoreIndicator
                      trustScore={
                        breakdown.gold != null
                          ? breakdown.gold * 100
                          : null
                      }
                      label="Gold"
                    />
                  </td>

                  <td>
                    <ScoreIndicator
                      trustScore={
                        breakdown.agreement != null
                          ? breakdown.agreement * 100
                          : null
                      }
                      label="Kappa"
                    />
                  </td>

                  <td>
                    <ScoreIndicator
                      trustScore={
                        breakdown.behavioral != null
                          ? breakdown.behavioral * 100
                          : null
                      }
                      label="Behavioral"
                    />
                  </td>

                  <td>
                    <ScoreIndicator
                      trustScore={
                        breakdown.embedding != null
                          ? breakdown.embedding * 100
                          : null
                      }
                      label="Embedding"
                    />
                  </td>

                  <td>
                    <ScoreIndicator
                      trustScore={
                        item.trust_score != null
                          ? item.trust_score * 100
                          : null
                      }
                      label="Trust Score"
                    />
                  </td>

                  <td>
                    {item.flagged ? (
                      <span>🚩 Flagged</span>
                    ) : (
                      <span>✓ Not Flagged</span>
                    )}
                  </td>

                  <td>{flagReason}</td>

                  <td>
                    <ReviewActions
                      item={item}
                      onResolve={onResolve}
                    />
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


