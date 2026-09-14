import React, { useState } from 'react';
import {
  Check,
  Edit3,
  AlertTriangle,
  X,
  Eye,
  ShieldCheck,
  CornerDownRight,
  Info,
  CheckSquare,
  Square,
  AlertOctagon,
} from 'lucide-react';
import { Modal } from './Modal';
import { Drawer } from './Drawer';
import { FlagStatusBadge } from './FlagStatusBadge';

function extractTextContent(content) {
  if (!content) return '';
  if (typeof content === 'string') return content;
  if (typeof content === 'object') {
    return content.text || content.body || content.sentence || content.content || JSON.stringify(content);
  }
  return String(content);
}

function getItemLabel(item) {
  if (!item) return '—';
  if (item.label) return String(item.label);
  if (item.gold_label) return String(item.gold_label);
  if (Array.isArray(item.annotations) && item.annotations.length > 0) {
    return item.annotations[0].label || '—';
  }
  return '—';
}

function getItemConfidence(item) {
  if (!item) return null;
  if (item.confidence != null) return item.confidence;
  if (Array.isArray(item.annotations) && item.annotations.length > 0) {
    return item.annotations[0].confidence;
  }
  return null;
}

function getFlagReason(item, breakdown) {
  if (!item.flagged) {
    return 'No active flag';
  }
  if (breakdown?.flag_reason) {
    return breakdown.flag_reason;
  }
  if (item.trust_score != null && item.trust_score < 0.6) {
    return 'Trust score below threshold (60%)';
  }
  if (breakdown?.anomaly_flag === true) {
    return 'Behavioral anomaly detected in click cadence';
  }
  if (breakdown?.is_outlier === true) {
    return 'Embedding outlier distance from cluster centroid';
  }
  if (breakdown?.gold != null && breakdown.gold < 0.5 && item.is_gold === true) {
    return 'Gold label mismatch with benchmark ground-truth';
  }
  return 'Automated quality flag triggered';
}

function getConfidenceBadge(val) {
  if (val == null) return <span className="mono-cell">—</span>;
  const pct = Math.round(val <= 1 ? val * 100 : val);
  let cls = 'badge-good';
  if (pct < 70) cls = 'badge-risk';
  else if (pct < 85) cls = 'badge-medium';

  return (
    <span className={`badge ${cls} mono-cell`}>
      {pct}%
    </span>
  );
}

export function ReviewQueueTable({
  items,
  loading,
  onResolve,
  density = 'comfortable',
}) {
  const [selectedIds, setSelectedIds] = useState([]);
  const [activeDrawerItem, setActiveDrawerItem] = useState(null);
  const [escalateModalItem, setEscalateModalItem] = useState(null);
  const [correctModalItem, setCorrectModalItem] = useState(null);
  const [correctLabel, setCorrectLabel] = useState('');
  const [notes, setNotes] = useState('');
  const [processing, setProcessing] = useState(false);

  const toggleSelectAll = () => {
    if (selectedIds.length === items.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(items.map((i) => i.item_id));
    }
  };

  const toggleSelectRow = (id, e) => {
    e.stopPropagation();
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleConfirm = async (item, e) => {
    e?.stopPropagation();
    try {
      setProcessing(true);
      await onResolve(item.item_id, { action: 'confirm' });
    } finally {
      setProcessing(false);
    }
  };

  const handleEscalateConfirm = async () => {
    if (!escalateModalItem) return;
    try {
      setProcessing(true);
      await onResolve(escalateModalItem.item_id, {
        action: 'escalate',
        notes: notes.trim() || 'Escalated to senior QA reviewer.',
      });
      setEscalateModalItem(null);
      setNotes('');
    } finally {
      setProcessing(false);
    }
  };

  const handleCorrectSubmit = async () => {
    if (!correctModalItem || !correctLabel.trim()) return;
    try {
      setProcessing(true);
      await onResolve(correctModalItem.item_id, {
        action: 'correct',
        correct_label: correctLabel.trim(),
        notes: notes.trim(),
      });
      setCorrectModalItem(null);
      setCorrectLabel('');
      setNotes('');
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkConfirm = async () => {
    try {
      setProcessing(true);
      for (const id of selectedIds) {
        await onResolve(id, { action: 'confirm' });
      }
      setSelectedIds([]);
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkEscalate = async () => {
    try {
      setProcessing(true);
      for (const id of selectedIds) {
        await onResolve(id, {
          action: 'escalate',
          notes: 'Batch escalated via bulk action bar.',
        });
      }
      setSelectedIds([]);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Escalation Confirmation Modal */}
      <Modal
        isOpen={!!escalateModalItem}
        onClose={() => setEscalateModalItem(null)}
        title="Escalate Item to Senior Reviewer"
        subtitle={`Item #${escalateModalItem?.item_id} will be routed to the escalation tier.`}
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setEscalateModalItem(null)}
              disabled={processing}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              style={{ background: 'var(--status-risk-solid)' }}
              onClick={handleEscalateConfirm}
              disabled={processing}
            >
              <AlertOctagon size={14} />
              <span>Confirm Escalation</span>
            </button>
          </>
        }
      >
        <div>
          <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
            Escalation Reason or Internal Notes (Optional):
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Disputed sentiment boundary between 'neutral' and 'mild positive'..."
            style={{
              width: '100%',
              minHeight: '80px',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.5rem',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
            }}
          />
        </div>
      </Modal>

      {/* Correct Label Modal */}
      <Modal
        isOpen={!!correctModalItem}
        onClose={() => setCorrectModalItem(null)}
        title="Override & Correct Label"
        subtitle={`Item #${correctModalItem?.item_id} currently labeled as "${getItemLabel(correctModalItem)}".`}
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setCorrectModalItem(null)}
              disabled={processing}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleCorrectSubmit}
              disabled={processing || !correctLabel.trim()}
            >
              <Check size={14} />
              <span>Apply Correction</span>
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              New Corrected Label:
            </label>
            <input
              type="text"
              value={correctLabel}
              onChange={(e) => setCorrectLabel(e.target.value)}
              placeholder="e.g. positive, negative, neutral..."
              autoFocus
              style={{
                width: '100%',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.5rem',
                color: 'var(--text-primary)',
                fontSize: '0.82rem',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Audit Note (Optional):
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Rationale for overriding initial label..."
              style={{
                width: '100%',
                minHeight: '65px',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.5rem',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
              }}
            />
          </div>
        </div>
      </Modal>

      {/* Item Inspection Slide-Over Drawer */}
      <Drawer
        isOpen={!!activeDrawerItem}
        onClose={() => setActiveDrawerItem(null)}
        eyebrow="Annotation Inspection & Cross-Evaluation"
        title={`Item #${activeDrawerItem?.item_id || ''}`}
        width="600px"
        footer={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="ghost-btn"
              style={{ color: 'var(--status-good-text)' }}
              onClick={() => {
                handleConfirm(activeDrawerItem);
                setActiveDrawerItem(null);
              }}
            >
              <Check size={14} />
              <span>Confirm</span>
            </button>
            <button
              type="button"
              className="ghost-btn"
              style={{ color: 'var(--status-info-text)' }}
              onClick={() => {
                setCorrectModalItem(activeDrawerItem);
                setCorrectLabel(getItemLabel(activeDrawerItem));
                setActiveDrawerItem(null);
              }}
            >
              <Edit3 size={14} />
              <span>Correct</span>
            </button>
            <button
              type="button"
              className="ghost-btn"
              style={{ color: 'var(--status-risk-text)' }}
              onClick={() => {
                setEscalateModalItem(activeDrawerItem);
                setActiveDrawerItem(null);
              }}
            >
              <AlertTriangle size={14} />
              <span>Escalate</span>
            </button>
          </div>
        }
      >
        {activeDrawerItem && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Annotation Content Preview */}
            <div>
              <div className="eyebrow" style={{ marginBottom: '0.4rem' }}>Labeled Text Content</div>
              <div
                style={{
                  padding: '1rem',
                  background: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.88rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)',
                }}
              >
                &ldquo;{extractTextContent(activeDrawerItem.text_content || activeDrawerItem.content || 'Content not available')}&rdquo;
              </div>
            </div>

            {/* Current Verdict Breakdown */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Assigned Label</div>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--accent-brand)', marginTop: '2px' }}>
                  {getItemLabel(activeDrawerItem)}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Confidence</div>
                <div className="mono-cell" style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--status-good-text)', marginTop: '2px' }}>
                  {getItemConfidence(activeDrawerItem) != null
                    ? `${Math.round(getItemConfidence(activeDrawerItem) * 100)}%`
                    : '—'}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Flag Status</div>
                <div style={{ marginTop: '4px' }}>
                  <FlagStatusBadge flagged={activeDrawerItem.flagged} />
                </div>
              </div>
            </div>

            {/* Annotator Responses Side-by-Side Comparison */}
            <div>
              <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>Annotator Agreement Comparison</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Array.isArray(activeDrawerItem.annotations) && activeDrawerItem.annotations.length > 0 ? (
                  activeDrawerItem.annotations.map((ann, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        background: 'var(--bg-subtle)',
                        borderRadius: 'var(--radius-xs)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {ann.annotator_name || `Annotator #${ann.annotator_id}`}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Label: <strong style={{ color: 'var(--text-primary)' }}>&ldquo;{ann.label}&rdquo;</strong>
                        </div>
                      </div>
                      <span className="badge badge-info font-mono">
                        Conf: {Math.round((ann.confidence || 0) * 100)}%
                      </span>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    No multi-annotator comparisons recorded for this item.
                  </div>
                )}
              </div>
            </div>

            {/* Reason for Flag */}
            <div>
              <div className="eyebrow" style={{ marginBottom: '0.35rem' }}>Guardian Diagnostic Flag Reason</div>
              <p
                style={{
                  fontSize: '0.82rem',
                  color: 'var(--status-risk-text)',
                  background: 'var(--status-risk-bg)',
                  border: '1px solid var(--status-risk-border)',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                {getFlagReason(
                  activeDrawerItem,
                  activeDrawerItem.trust_score_breakdown || activeDrawerItem.quality_breakdown || {}
                )}
              </p>
            </div>
          </div>
        )}
      </Drawer>

      {/* Floating Bulk Action Bar when rows are selected */}
      {selectedIds.length > 0 && (
        <div className="sticky-save-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="badge badge-info font-mono">{selectedIds.length} Selected</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-primary)' }}>Bulk arbitration</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleBulkConfirm}
              disabled={processing}
              style={{ color: 'var(--status-good-text)', padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            >
              <Check size={13} />
              <span>Bulk Confirm</span>
            </button>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleBulkEscalate}
              disabled={processing}
              style={{ color: 'var(--status-risk-text)', padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            >
              <AlertTriangle size={13} />
              <span>Bulk Escalate</span>
            </button>
            <button
              type="button"
              className="ghost-btn"
              onClick={() => setSelectedIds([])}
              style={{ fontSize: '0.75rem', padding: '0.35rem 0.5rem' }}
            >
              Deselect
            </button>
          </div>
        </div>
      )}

      {/* Data Grid Table */}
      <div className={`table-wrapper ${density === 'compact' ? 'table-compact' : ''}`}>
        <table>
          <thead>
            <tr>
              <th style={{ width: '40px', textAlign: 'center' }}>
                <input
                  type="checkbox"
                  checked={items.length > 0 && selectedIds.length === items.length}
                  onChange={toggleSelectAll}
                  aria-label="Select all rows"
                />
              </th>
              <th style={{ width: '80px' }}>Item ID</th>
              <th>Content Sample</th>
              <th>Label</th>
              <th>Confidence</th>
              <th>Why Flagged</th>
              <th>Status</th>
              <th style={{ textAlign: 'right', minWidth: '180px' }}>Actions</th>
            </tr>
          </thead>

          <tbody>
            {items.map((item) => {
              const breakdown = item.trust_score_breakdown || item.quality_breakdown || {};
              const flagReason = getFlagReason(item, breakdown);
              const isSelected = selectedIds.includes(item.item_id);
              const contentText = extractTextContent(item.text_content || item.content || `Item #${item.item_id}`);
              const label = getItemLabel(item);
              const confidence = getItemConfidence(item);

              return (
                <tr
                  key={item.item_id}
                  className={`clickable-row ${isSelected ? 'row-selected' : ''}`}
                  onClick={() => setActiveDrawerItem(item)}
                >
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => toggleSelectRow(item.item_id, e)}
                      aria-label={`Select item #${item.item_id}`}
                    />
                  </td>

                  <td>
                    <span className="mono-cell" style={{ fontWeight: 600, color: 'var(--accent-brand)' }}>
                      #{item.item_id}
                    </span>
                  </td>

                  <td style={{ maxWidth: '240px' }}>
                    <div
                      style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        color: 'var(--text-primary)',
                      }}
                      title={contentText}
                    >
                      {contentText}
                    </div>
                  </td>

                  <td>
                    <span className="badge badge-neutral" style={{ fontWeight: 600 }}>
                      {label}
                    </span>
                  </td>

                  <td>{getConfidenceBadge(confidence)}</td>

                  <td style={{ maxWidth: '180px' }}>
                    <div
                      style={{
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        fontSize: '0.75rem',
                        color: item.flagged ? 'var(--status-risk-text)' : 'var(--text-muted)',
                      }}
                      title={flagReason}
                    >
                      {flagReason}
                    </div>
                  </td>

                  <td>
                    <FlagStatusBadge flagged={item.flagged} />
                  </td>

                  <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={(e) => handleConfirm(item, e)}
                        disabled={processing}
                        title="Confirm annotation"
                        style={{ color: 'var(--status-good-text)', padding: '3px 7px', fontSize: '0.75rem' }}
                      >
                        <Check size={13} />
                        <span>Confirm</span>
                      </button>

                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() => {
                          setCorrectModalItem(item);
                          setCorrectLabel(label === '—' ? '' : label);
                        }}
                        disabled={processing}
                        title="Correct label"
                        style={{ color: 'var(--status-info-text)', padding: '3px 7px', fontSize: '0.75rem' }}
                      >
                        <Edit3 size={13} />
                        <span>Correct</span>
                      </button>

                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() => setEscalateModalItem(item)}
                        disabled={processing}
                        title="Escalate item"
                        style={{ color: 'var(--status-risk-text)', padding: '3px 7px', fontSize: '0.75rem' }}
                      >
                        <AlertTriangle size={13} />
                        <span>Escalate</span>
                      </button>
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
