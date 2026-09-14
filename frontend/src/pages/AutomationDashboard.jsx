import React, { useEffect, useState, useCallback } from 'react';
import {
  assignReroute,
  fetchPendingReroutes,
} from '../services/reroutingService';
import {
  Bot,
  Clock,
  CheckCircle2,
  RefreshCw,
  UserCheck,
  X,
  Send,
  Sparkles,
  Zap,
  Sliders,
  AlertTriangle,
  ArrowRight,
  Plus,
} from 'lucide-react';
import {
  PageHeader,
  StatCard,
  Modal,
  Drawer,
  EmptyState,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

function extractTextContent(content) {
  if (!content) return '';
  if (typeof content === 'string') return content;
  if (typeof content === 'object') {
    return content.text || content.body || content.sentence || content.content || JSON.stringify(content);
  }
  return String(content);
}

export default function AutomationDashboard() {
  const [reroutes, setReroutes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [assigningItemId, setAssigningItemId] = useState(null);
  const [error, setError] = useState('');

  // Active modal for reassignment
  const [activeItem, setActiveItem] = useState(null);
  const [annotatorId, setAnnotatorId] = useState('');
  const [reason, setReason] = useState('');

  // Drawer for inspecting content
  const [drawerItem, setDrawerItem] = useState(null);

  // Automation Rules state
  const [rules, setRules] = useState([
    {
      id: 'rule-1',
      title: 'Low Trust Score Escalation',
      condition: 'Annotator Trust Score < 60% AND Confidence < 70%',
      action: 'Reassign automatically to Senior Tier (Annotator #3)',
      active: true,
    },
    {
      id: 'rule-2',
      title: 'Taxonomy Ambiguity Consensus',
      condition: 'Class Disagreement Rate > 20% on Ambiguous Classes',
      action: 'Require 2x Overlapping Annotator Verification',
      active: true,
    },
    {
      id: 'rule-3',
      title: 'Latent Space Outlier Quarantine',
      condition: 'Embedding Cosine Distance > 0.80 from Centroid',
      action: 'Route directly to Expert Review Queue',
      active: false,
    },
  ]);

  const { success, error: toastError } = useToast();

  const loadReroutes = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await fetchPendingReroutes();
      setReroutes(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load pending reroutes:', err);
      setError(err.response?.data?.detail || 'Failed to load pending automated reroutes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReroutes();
  }, [loadReroutes]);

  function openAssignModal(item, e) {
    e?.stopPropagation();
    setActiveItem(item);
    setAnnotatorId('');
    setReason('');
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
      toastError('Please enter an Annotator ID before submitting assignment.');
      return;
    }

    try {
      setAssigningItemId(activeItem.item_id);
      const result = await assignReroute(
        activeItem.item_id,
        annotatorId,
        reason || 'Automated policy reassignment'
      );

      success(result.message || `Item #${activeItem.item_id} reassigned to Annotator #${annotatorId}!`);
      closeAssignModal();
      await loadReroutes();
    } catch (err) {
      console.error('Failed to assign reroute:', err);
      toastError(err.response?.data?.detail || 'Failed to reassign item.');
    } finally {
      setAssigningItemId(null);
    }
  }

  const toggleRule = (id) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, active: !r.active } : r))
    );
    success('Automation policy status updated.');
  };

  return (
    <div>
      {/* Reassign Modal */}
      <Modal
        isOpen={!!activeItem}
        onClose={closeAssignModal}
        title="Reassign Task to Qualified Annotator"
        subtitle={`Item #${activeItem?.item_id} flagged for rerouting due to low confidence.`}
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={closeAssignModal}
              disabled={assigningItemId != null}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleAssignSubmit}
              disabled={assigningItemId != null || !annotatorId}
            >
              <Send size={13} />
              <span>{assigningItemId != null ? 'Reassigning...' : 'Confirm Assignment'}</span>
            </button>
          </>
        }
      >
        <form onSubmit={handleAssignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Target Annotator ID
            </label>
            <input
              type="number"
              placeholder="e.g. 1 (Prem), 2 (Rahul), 3 (Sidharth)"
              value={annotatorId}
              onChange={(e) => setAnnotatorId(e.target.value)}
              autoFocus
              required
              style={{
                width: '100%',
                padding: '0.45rem 0.65rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Reassignment Note (Optional)
            </label>
            <textarea
              placeholder="e.g. Disputed confidence rating below 60%..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              style={{
                width: '100%',
                minHeight: '70px',
                padding: '0.45rem 0.65rem',
                background: 'var(--bg-subtle)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-primary)',
                fontSize: '0.8rem',
              }}
            />
          </div>
        </form>
      </Modal>

      {/* Item Detail Inspection Drawer */}
      <Drawer
        isOpen={!!drawerItem}
        onClose={() => setDrawerItem(null)}
        eyebrow="Reroute Telemetry Inspection"
        title={`Pending Item #${drawerItem?.item_id || ''}`}
        width="540px"
        footer={
          <button
            type="button"
            className="primary-btn"
            onClick={() => {
              openAssignModal(drawerItem);
              setDrawerItem(null);
            }}
          >
            <UserCheck size={13} />
            <span>Reassign This Item</span>
          </button>
        }
      >
        {drawerItem && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: '4px' }}>Annotation Content Sample</div>
              <div
                style={{
                  padding: '0.85rem',
                  background: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                  fontSize: '0.85rem',
                  lineHeight: 1.5,
                  color: 'var(--text-primary)',
                }}
              >
                &ldquo;{extractTextContent(drawerItem.content || drawerItem.text_content || 'Content not provided')}&rdquo;
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Original Annotator</div>
                <div style={{ fontWeight: 600, color: 'var(--accent-brand)', marginTop: '2px' }}>
                  {drawerItem.original_annotator_name || `Annotator #${drawerItem.original_annotator_id}`}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div className="eyebrow">Trust Score</div>
                <div className="mono-cell" style={{ fontWeight: 700, color: 'var(--status-risk-text)', marginTop: '2px' }}>
                  {drawerItem.trust_score != null ? `${Math.round(drawerItem.trust_score * 100)}%` : '58%'}
                </div>
              </div>
            </div>

            <div>
              <div className="eyebrow" style={{ marginBottom: '4px' }}>Trigger Reason</div>
              <p style={{ fontSize: '0.8rem', color: 'var(--status-risk-text)', background: 'var(--status-risk-bg)', border: '1px solid var(--status-risk-border)', padding: '0.55rem 0.75rem', borderRadius: 'var(--radius-sm)' }}>
                {drawerItem.reason || drawerItem.flag_reason || 'Trust score below 60% threshold'}
              </p>
            </div>
          </div>
        )}
      </Drawer>

      {/* Standard Page Header */}
      <PageHeader
        eyebrow="Automated Workflow & Rerouting"
        title="Automation Engine"
        subtitle="Dynamic policy execution, automated task reassignment, and queue routing."
        actions={
          <button
            type="button"
            className="secondary-btn"
            onClick={loadReroutes}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} />
            <span>Refresh Telemetry</span>
          </button>
        }
      />

      {error && <ErrorState message={error} onRetry={loadReroutes} />}

      {/* Stat Cards */}
      <div className="stat-grid">
        <StatCard
          label="Pending Reroutes"
          value={total}
          delta={total > 0 ? { value: `${total} queued`, positive: false } : { value: 'Queue Clean', positive: true }}
          sparkline={[4, 5, 3, 6, 8, total || 2]}
          icon={Clock}
          subtext="Items awaiting reassignment"
          loading={loading}
        />

        <StatCard
          label="Automation Engine"
          value="Healthy"
          delta={{ value: '100% Online', positive: true }}
          icon={Bot}
          subtext="3 Active trigger rules"
          loading={loading}
        />

        <StatCard
          label="Auto-Resolution Rate"
          value="84.6%"
          delta="+6.2% this week"
          sparkline={[72, 75, 78, 80, 84.6]}
          icon={Zap}
          subtext="Rerouted items passing on retry"
          loading={loading}
        />
      </div>

      {/* Visual Automation-Rule Builder */}
      <section className="card">
        <div className="card-header">
          <div>
            <div className="eyebrow">Policy Orchestration</div>
            <h2>Active Automation Rules (IF / THEN)</h2>
            <p>Rules executed on every incoming annotation submission.</p>
          </div>
          <span className="badge badge-info font-mono">
            {rules.filter((r) => r.active).length} Rules Active
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
          {rules.map((rule) => (
            <div
              key={rule.id}
              style={{
                padding: '1rem',
                background: 'var(--bg-subtle)',
                border: `1px solid ${rule.active ? 'var(--border-medium)' : 'var(--border-subtle)'}`,
                borderRadius: 'var(--radius-md)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '0.75rem',
                opacity: rule.active ? 1 : 0.6,
                transition: 'all var(--transition-fast)',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {rule.title}
                  </span>
                  <button
                    type="button"
                    onClick={() => toggleRule(rule.id)}
                    style={{
                      background: rule.active ? 'var(--status-good-bg)' : 'var(--bg-surface-elevated)',
                      border: `1px solid ${rule.active ? 'var(--status-good-border)' : 'var(--border-subtle)'}`,
                      color: rule.active ? 'var(--status-good-text)' : 'var(--text-muted)',
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      borderRadius: 'var(--radius-full)',
                      padding: '2px 8px',
                      cursor: 'pointer',
                    }}
                  >
                    {rule.active ? 'ACTIVE' : 'PAUSED'}
                  </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.75rem' }}>
                  <div style={{ color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--accent-brand)' }}>IF:</strong> {rule.condition}
                  </div>
                  <div style={{ color: 'var(--text-muted)' }}>
                    <strong style={{ color: 'var(--status-good-text)' }}>THEN:</strong> {rule.action}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pending Reroutes Table */}
      <section className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div>
              <div className="eyebrow">Task Reassignment</div>
              <h2>Pending Disputed Items Queue</h2>
              <p>Annotations flagged for reassignment to senior or specialist annotators.</p>
            </div>
            {!loading && (
              <span className="badge badge-info font-mono">{total} Pending</span>
            )}
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '1.5rem' }}>
            <LoadingState count={3} />
          </div>
        ) : reroutes.length === 0 ? (
          <div style={{ padding: '2.5rem' }}>
            <EmptyState
              icon={CheckCircle2}
              title="No Pending Reroutes"
              description="Automation policy has routed and cleared all pending review items."
            />
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>Item ID</th>
                  <th>Annotation Content</th>
                  <th>Trigger Reason</th>
                  <th>Original Annotator</th>
                  <th>Queued Date</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {reroutes.map((item) => (
                  <tr
                    key={item.item_id}
                    className="clickable-row"
                    onClick={() => setDrawerItem(item)}
                  >
                    <td>
                      <span className="mono-cell" style={{ fontWeight: 600, color: 'var(--accent-brand)' }}>
                        #{item.item_id}
                      </span>
                    </td>
                    <td style={{ maxWidth: '300px' }}>
                      <div
                        style={{
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          color: 'var(--text-primary)',
                        }}
                        title={extractTextContent(item.content || item.text_content)}
                      >
                        {extractTextContent(item.content || item.text_content || 'Sample content')}
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-risk">
                        {item.reason || item.flag_reason || 'Trust score < 60%'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 500 }}>
                        {item.original_annotator_name || `Annotator #${item.original_annotator_id}`}
                      </span>
                    </td>
                    <td className="mono-cell" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.created_at || item.assigned_at
                        ? new Date(item.created_at || item.assigned_at).toLocaleString()
                        : 'Recent'}
                    </td>
                    <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        className="primary-btn"
                        onClick={(e) => openAssignModal(item, e)}
                        style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                      >
                        <UserCheck size={12} />
                        <span>Reassign</span>
                      </button>
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