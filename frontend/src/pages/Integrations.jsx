import React, { useEffect, useState } from 'react';
import {
  createConnector,
  updateConnector,
  deleteConnector,
  fetchConnectors,
  syncConnector,
  testConnector,
} from '../services/integrationService';
import {
  Database,
  Plus,
  Play,
  RotateCw,
  Trash2,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Server,
  Activity,
  Layers,
  ArrowRight,
  HardDrive,
  Pencil,
  Clock,
  Wifi,
  WifiOff,
  AlertTriangle,
} from 'lucide-react';
import {
  PageHeader,
  Modal,
  EmptyState,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

// ── Constants ──────────────────────────────────────────────────────────────

const INITIAL_FORM = {
  connection_name: '',
  database_type: 'postgresql',
  host: '',
  port: 5432,
  database_name: '',
  username: '',
  password: '',
  status: 'active',
};

const INITIAL_ERRORS = {
  connection_name: '',
  host: '',
  port: '',
  database_name: '',
  username: '',
  password: '',
};

function getDatabasePort(databaseType) {
  if (databaseType === 'mysql') return 3306;
  if (databaseType === 'sqlite') return '';
  return 5432;
}

function isSqlite(form) {
  return form.database_type === 'sqlite';
}

// ── Field styling helpers ──────────────────────────────────────────────────

const baseInputStyle = {
  width: '100%',
  padding: '0.45rem 0.65rem',
  background: 'var(--bg-subtle)',
  border: '1px solid var(--border-subtle)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text-primary)',
};

const errorInputStyle = {
  ...baseInputStyle,
  border: '1px solid var(--status-risk-border, #f87171)',
};

const labelStyle = {
  fontSize: '0.78rem',
  fontWeight: 600,
  display: 'block',
  marginBottom: '3px',
};

const inlineErrorStyle = {
  fontSize: '0.7rem',
  color: 'var(--status-risk-text, #ef4444)',
  marginTop: '3px',
};

function FieldError({ msg }) {
  if (!msg) return null;
  return <div style={inlineErrorStyle}>{msg}</div>;
}

// ── Status badge ───────────────────────────────────────────────────────────

function StatusBadge({ connector, testResult }) {
  // Prefer fresh test result if available
  const effectiveStatus = testResult
    ? testResult.status
    : connector.status === 'active' && connector.last_tested_at
    ? 'success'
    : connector.status === 'error'
    ? 'error'
    : 'untested';

  if (effectiveStatus === 'success') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <div className="pulsing-dot" />
        <span style={{ fontSize: '0.7rem', color: 'var(--status-good-text)', fontWeight: 500 }}>Connected</span>
      </div>
    );
  }
  if (effectiveStatus === 'error') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <WifiOff size={11} color="var(--status-risk-text)" />
        <span style={{ fontSize: '0.7rem', color: 'var(--status-risk-text)', fontWeight: 500 }}>Error</span>
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <AlertTriangle size={11} color="var(--text-muted)" />
      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>Untested</span>
    </div>
  );
}

// ── Connector form (shared between create and edit) ───────────────────────

function ConnectorForm({ form, errors, onChange, onDbTypeChange, submitError }) {
  return (
    <form style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {/* Connection Name */}
      <div>
        <label style={labelStyle}>
          Connection Name <span style={{ color: 'var(--status-risk-text)' }}>*</span>
        </label>
        <input
          id="conn-name"
          type="text"
          name="connection_name"
          placeholder="e.g. Primary Production Warehouse"
          value={form.connection_name}
          onChange={onChange}
          style={errors.connection_name ? errorInputStyle : baseInputStyle}
        />
        <FieldError msg={errors.connection_name} />
      </div>

      {/* DB Type + DB Name row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
        <div>
          <label style={labelStyle}>Database Type</label>
          <select
            id="conn-db-type"
            name="database_type"
            value={form.database_type}
            onChange={onDbTypeChange}
            style={baseInputStyle}
          >
            <option value="postgresql">PostgreSQL (15+)</option>
            <option value="mysql">MySQL / MariaDB</option>
            <option value="sqlite">SQLite Local File</option>
          </select>
        </div>

        <div>
          <label style={labelStyle}>
            Database Name / File <span style={{ color: 'var(--status-risk-text)' }}>*</span>
          </label>
          <input
            id="conn-db-name"
            type="text"
            name="database_name"
            placeholder={isSqlite(form) ? 'aqg_dev.db' : 'aqg_warehouse'}
            value={form.database_name}
            onChange={onChange}
            style={errors.database_name ? errorInputStyle : baseInputStyle}
          />
          <FieldError msg={errors.database_name} />
        </div>
      </div>

      {/* Host + Port + Credentials — only for non-SQLite */}
      {!isSqlite(form) && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={labelStyle}>
                Host <span style={{ color: 'var(--status-risk-text)' }}>*</span>
              </label>
              <input
                id="conn-host"
                type="text"
                name="host"
                placeholder="localhost or db.internal.net"
                value={form.host}
                onChange={onChange}
                style={errors.host ? errorInputStyle : baseInputStyle}
              />
              <FieldError msg={errors.host} />
            </div>
            <div>
              <label style={labelStyle}>
                Port <span style={{ color: 'var(--status-risk-text)' }}>*</span>
              </label>
              <input
                id="conn-port"
                type="number"
                name="port"
                value={form.port}
                onChange={onChange}
                style={errors.port ? errorInputStyle : baseInputStyle}
              />
              <FieldError msg={errors.port} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={labelStyle}>
                Username <span style={{ color: 'var(--status-risk-text)' }}>*</span>
              </label>
              <input
                id="conn-username"
                type="text"
                name="username"
                placeholder="postgres"
                value={form.username}
                onChange={onChange}
                style={errors.username ? errorInputStyle : baseInputStyle}
              />
              <FieldError msg={errors.username} />
            </div>
            <div>
              <label style={labelStyle}>
                Password <span style={{ color: 'var(--status-risk-text)' }}>*</span>
              </label>
              <input
                id="conn-password"
                type="password"
                name="password"
                placeholder="••••••••"
                value={form.password}
                onChange={onChange}
                style={errors.password ? errorInputStyle : baseInputStyle}
              />
              <FieldError msg={errors.password} />
            </div>
          </div>
        </>
      )}

      {/* Submit-level error banner */}
      {submitError && (
        <div
          style={{
            padding: '0.5rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--status-risk-bg)',
            border: '1px solid var(--status-risk-border)',
            color: 'var(--status-risk-text)',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '6px',
          }}
        >
          <AlertOctagon size={14} style={{ flexShrink: 0, marginTop: '1px' }} />
          <span>{submitError}</span>
        </div>
      )}
    </form>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function Integrations() {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [formErrors, setFormErrors] = useState(INITIAL_ERRORS);
  const [submitError, setSubmitError] = useState('');

  // Edit modal
  const [editConnector, setEditConnector] = useState(null); // connector object being edited
  const [editForm, setEditForm] = useState(INITIAL_FORM);
  const [editErrors, setEditErrors] = useState(INITIAL_ERRORS);
  const [editSubmitError, setEditSubmitError] = useState('');
  const [editSaving, setEditSaving] = useState(false);

  const [testingId, setTestingId] = useState(null);
  const [syncingId, setSyncingId] = useState(null);
  const [testResults, setTestResults] = useState({});

  // Sync modal state
  const [activeSyncConnector, setActiveSyncConnector] = useState(null);
  const [syncTable, setSyncTable] = useState('');
  const [syncLimit, setSyncLimit] = useState(1000);

  const [pageError, setPageError] = useState('');
  const { success, error: toastError, info } = useToast();

  // ── Data loading ──────────────────────────────────────────────────

  async function loadConnectors() {
    try {
      setLoading(true);
      setPageError('');
      const data = await fetchConnectors();
      setConnectors(data || []);
    } catch (err) {
      console.error('Failed to load connectors:', err);
      setPageError(err.response?.data?.detail || 'Failed to load external connectors.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConnectors();
  }, []);

  // ── Form helpers ──────────────────────────────────────────────────

  function handleFormChange(e) {
    const { name, value } = e.target;
    setForm((curr) => ({
      ...curr,
      [name]: name === 'port' ? (value === '' ? '' : Number(value)) : value,
    }));
    // Clear field error on change
    if (formErrors[name]) {
      setFormErrors((prev) => ({ ...prev, [name]: '' }));
    }
    setSubmitError('');
  }

  function handleDatabaseTypeChange(e) {
    const databaseType = e.target.value;
    setForm((curr) => ({
      ...curr,
      database_type: databaseType,
      port: getDatabasePort(databaseType),
    }));
    setFormErrors(INITIAL_ERRORS);
    setSubmitError('');
  }

  function handleEditFormChange(e) {
    const { name, value } = e.target;
    setEditForm((curr) => ({
      ...curr,
      [name]: name === 'port' ? (value === '' ? '' : Number(value)) : value,
    }));
    if (editErrors[name]) {
      setEditErrors((prev) => ({ ...prev, [name]: '' }));
    }
    setEditSubmitError('');
  }

  function handleEditDbTypeChange(e) {
    const databaseType = e.target.value;
    setEditForm((curr) => ({
      ...curr,
      database_type: databaseType,
      port: getDatabasePort(databaseType),
    }));
    setEditErrors(INITIAL_ERRORS);
    setEditSubmitError('');
  }

  // ── Validation ────────────────────────────────────────────────────

  function validateForm(f) {
    const errs = { ...INITIAL_ERRORS };
    let valid = true;

    if (!f.connection_name.trim()) {
      errs.connection_name = 'Connection name is required.';
      valid = false;
    }
    if (!f.database_name.trim()) {
      errs.database_name = 'Database name / file path is required.';
      valid = false;
    }

    if (f.database_type !== 'sqlite') {
      if (!f.host.trim()) {
        errs.host = 'Host is required.';
        valid = false;
      }
      if (!f.port || Number(f.port) < 1 || Number(f.port) > 65535) {
        errs.port = 'A valid port (1–65535) is required.';
        valid = false;
      }
      if (!f.username.trim()) {
        errs.username = 'Username is required.';
        valid = false;
      }
      if (!f.password.trim()) {
        errs.password = 'Password is required.';
        valid = false;
      }
    }

    return { errs, valid };
  }

  // ── Create connector ──────────────────────────────────────────────

  function openCreateModal() {
    setForm(INITIAL_FORM);
    setFormErrors(INITIAL_ERRORS);
    setSubmitError('');
    setShowCreateModal(true);
  }

  function closeCreateModal() {
    if (saving) return;
    setShowCreateModal(false);
    setSubmitError('');
    setFormErrors(INITIAL_ERRORS);
  }

  async function handleCreate() {
    const { errs, valid } = validateForm(form);
    if (!valid) {
      setFormErrors(errs);
      return;
    }

    try {
      setSaving(true);
      setSubmitError('');
      const payload = {
        connection_name: form.connection_name.trim(),
        database_type: form.database_type,
        host: isSqlite(form) ? null : form.host.trim() || null,
        port: isSqlite(form) ? null : Number(form.port),
        database_name: form.database_name.trim(),
        username: isSqlite(form) ? null : form.username.trim() || null,
        password: isSqlite(form) ? null : form.password || null,
        status: 'active',
      };

      await createConnector(payload);
      success(`Connected to "${form.connection_name}" — connection verified!`);
      setShowCreateModal(false);
      setForm(INITIAL_FORM);
      setFormErrors(INITIAL_ERRORS);
      await loadConnectors();
    } catch (err) {
      // Keep modal open — show specific error inline
      const detail = err.response?.data?.detail;
      let msg;
      if (detail && typeof detail === 'object' && detail.message) {
        msg = detail.message;
      } else if (typeof detail === 'string') {
        msg = detail;
      } else {
        msg = 'Failed to establish connection. Check credentials and try again.';
      }
      setSubmitError(msg);
    } finally {
      setSaving(false);
    }
  }

  // ── Edit connector ────────────────────────────────────────────────

  function openEditModal(connector) {
    setEditConnector(connector);
    setEditForm({
      connection_name: connector.connection_name,
      database_type: connector.database_type,
      host: connector.host || '',
      port: connector.port || getDatabasePort(connector.database_type),
      database_name: connector.database_name,
      username: connector.username || '',
      password: '', // never pre-fill password
      status: connector.status,
    });
    setEditErrors(INITIAL_ERRORS);
    setEditSubmitError('');
  }

  function closeEditModal() {
    if (editSaving) return;
    setEditConnector(null);
    setEditSubmitError('');
    setEditErrors(INITIAL_ERRORS);
  }

  async function handleEdit() {
    const { errs, valid } = validateForm(editForm);
    // For edit: password is optional (only validated if non-empty)
    const adjustedErrs = { ...errs };
    if (!editForm.password.trim()) {
      adjustedErrs.password = '';
    }
    const adjustedValid = Object.values(adjustedErrs).every((v) => !v);

    if (!adjustedValid) {
      setEditErrors(adjustedErrs);
      return;
    }

    try {
      setEditSaving(true);
      setEditSubmitError('');
      const payload = {
        connection_name: editForm.connection_name.trim(),
        host: isSqlite(editForm) ? null : editForm.host.trim() || null,
        port: isSqlite(editForm) ? null : Number(editForm.port),
        database_name: editForm.database_name.trim(),
        username: isSqlite(editForm) ? null : editForm.username.trim() || null,
        status: editForm.status,
      };
      // Only send password if user typed a new one
      if (editForm.password.trim()) {
        payload.password = editForm.password;
      }

      await updateConnector(editConnector.id, payload);
      success(`Connector "${editForm.connection_name}" updated.`);
      setEditConnector(null);
      await loadConnectors();
    } catch (err) {
      const detail = err.response?.data?.detail;
      let msg;
      if (detail && typeof detail === 'object' && detail.message) {
        msg = detail.message;
      } else if (typeof detail === 'string') {
        msg = detail;
      } else {
        msg = 'Failed to update connector.';
      }
      setEditSubmitError(msg);
    } finally {
      setEditSaving(false);
    }
  }

  // ── Test connection ───────────────────────────────────────────────

  async function handleTest(connectorId) {
    try {
      setTestingId(connectorId);
      const res = await testConnector(connectorId);

      // res.status is now "success" | "error" (string from backend)
      // res.success is the bool
      const resultStatus = res.status || (res.success ? 'success' : 'error');

      setTestResults((prev) => ({
        ...prev,
        [connectorId]: {
          status: resultStatus,
          latency: res.latency_ms != null ? `${res.latency_ms}ms` : null,
          message: res.message || (res.success ? 'Connection healthy & responsive' : 'Connection failed'),
          error_type: res.error_type,
        },
      }));

      if (res.success) {
        const latStr = res.latency_ms != null ? ` (${res.latency_ms}ms)` : '';
        success(`Connection test passed${latStr}`);
      } else {
        toastError(`Connection test failed: ${res.message}`);
      }

      // Refresh connectors so last_tested_at updates on card
      await loadConnectors();
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: {
          status: 'error',
          message: err.response?.data?.detail || 'Connection test request failed.',
          error_type: 'unknown',
        },
      }));
      toastError('Connection test failed.');
    } finally {
      setTestingId(null);
    }
  }

  // ── Sync ──────────────────────────────────────────────────────────

  async function handleSyncSubmit(e) {
    e.preventDefault();
    if (!activeSyncConnector) return;
    try {
      setSyncingId(activeSyncConnector.id);
      const payload = {
        project_id: 1,
        table_name: syncTable.trim() || undefined,
        limit: Number(syncLimit) || 1000,
      };
      const res = await syncConnector(activeSyncConnector.id, payload);
      const inserted = res.synced_rows ?? res.inserted_records ?? 0;
      success(`Synced ${inserted} annotations into Project #1!`);
      setActiveSyncConnector(null);
      setSyncTable('');
      await loadConnectors();
    } catch (err) {
      toastError(err.response?.data?.detail || 'Sync task failed.');
    } finally {
      setSyncingId(null);
    }
  }

  // ── Delete ────────────────────────────────────────────────────────

  async function handleDelete(connectorId) {
    if (!window.confirm('Disconnect and delete this database integration?')) return;
    try {
      await deleteConnector(connectorId);
      info('Database connector removed.');
      setTestResults((prev) => {
        const next = { ...prev };
        delete next[connectorId];
        return next;
      });
      await loadConnectors();
    } catch (err) {
      toastError('Failed to delete connector.');
    }
  }

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div>
      {/* ── Create Connector Modal ─────────────────────────────────── */}
      <Modal
        isOpen={showCreateModal}
        onClose={closeCreateModal}
        title="Connect External Database"
        subtitle="Link PostgreSQL, MySQL, or SQLite to ingest annotation batches."
        maxWidth="540px"
        footer={
          <>
            <button
              id="create-connector-cancel"
              type="button"
              className="secondary-btn"
              onClick={closeCreateModal}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              id="create-connector-submit"
              type="button"
              className="primary-btn"
              onClick={handleCreate}
              disabled={saving}
            >
              <Plus size={14} />
              <span>{saving ? 'Testing & Connecting…' : 'Establish Connection'}</span>
            </button>
          </>
        }
      >
        <ConnectorForm
          form={form}
          errors={formErrors}
          onChange={handleFormChange}
          onDbTypeChange={handleDatabaseTypeChange}
          submitError={submitError}
        />
      </Modal>

      {/* ── Edit Connector Modal ───────────────────────────────────── */}
      <Modal
        isOpen={!!editConnector}
        onClose={closeEditModal}
        title="Edit Database Connector"
        subtitle={`Update configuration for "${editConnector?.connection_name}".`}
        maxWidth="540px"
        footer={
          <>
            <button
              id="edit-connector-cancel"
              type="button"
              className="secondary-btn"
              onClick={closeEditModal}
              disabled={editSaving}
            >
              Cancel
            </button>
            <button
              id="edit-connector-submit"
              type="button"
              className="primary-btn"
              onClick={handleEdit}
              disabled={editSaving}
            >
              <Pencil size={14} />
              <span>{editSaving ? 'Saving…' : 'Save Changes'}</span>
            </button>
          </>
        }
      >
        <ConnectorForm
          form={editForm}
          errors={editErrors}
          onChange={handleEditFormChange}
          onDbTypeChange={handleEditDbTypeChange}
          submitError={editSubmitError}
        />
        {/* Note that password is optional on edit */}
        {editConnector && (
          <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Leave the password field blank to keep the existing stored credential.
          </p>
        )}
      </Modal>

      {/* ── Sync Modal ────────────────────────────────────────────────  */}
      <Modal
        isOpen={!!activeSyncConnector}
        onClose={() => setActiveSyncConnector(null)}
        title="Ingest Annotations from Database"
        subtitle={`Synchronize records from "${activeSyncConnector?.connection_name}" into Project #1.`}
        maxWidth="480px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setActiveSyncConnector(null)}
              disabled={syncingId != null}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleSyncSubmit}
              disabled={syncingId != null}
            >
              <RotateCw size={14} className={syncingId != null ? 'spin' : ''} />
              <span>{syncingId != null ? 'Synchronizing...' : 'Start Ingestion'}</span>
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={labelStyle}>Target Table Name (Optional)</label>
            <input
              type="text"
              placeholder="annotations_stream"
              value={syncTable}
              onChange={(e) => setSyncTable(e.target.value)}
              style={baseInputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Max Row Limit</label>
            <input
              type="number"
              value={syncLimit}
              onChange={(e) => setSyncLimit(e.target.value)}
              style={baseInputStyle}
            />
          </div>
        </div>
      </Modal>

      {/* ── Page Header ───────────────────────────────────────────────  */}
      <PageHeader
        eyebrow="Data Ingestion & Warehouses"
        title="Database Integrations"
        subtitle="Connect external SQL databases to ingest annotation streams and sync ground-truth sets."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <button
              type="button"
              className="secondary-btn"
              onClick={loadConnectors}
              disabled={loading}
            >
              <RotateCw size={14} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>

            <button
              id="add-connector-btn"
              type="button"
              className="primary-btn"
              onClick={openCreateModal}
            >
              <Plus size={14} />
              <span>Add Connector</span>
            </button>
          </div>
        }
      />

      {pageError && <ErrorState message={pageError} onRetry={loadConnectors} />}

      {/* ── Content ─────────────────────────────────────────────────── */}
      {loading ? (
        <div className="card">
          <LoadingState count={3} />
        </div>
      ) : connectors.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Database}
            eyebrow="External Datasources"
            title="No Database Connectors Registered"
            description="Link your Postgres, MySQL, or SQLite warehouse to automate annotation quality streaming."
            actionLabel="Connect First Database"
            onAction={openCreateModal}
          />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {connectors.map((conn) => {
            const testResult = testResults[conn.id];
            const isTesting = testingId === conn.id;

            return (
              <div
                key={conn.id}
                className="card"
                style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
              >
                <div>
                  {/* Card header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <div className="stat-card-icon-wrap" style={{ width: '36px', height: '36px' }}>
                        <Database size={18} />
                      </div>
                      <div>
                        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {conn.connection_name}
                        </h3>
                        <span className="mono-cell" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {conn.database_type.toUpperCase()} • {conn.database_name}
                        </span>
                      </div>
                    </div>

                    <StatusBadge connector={conn} testResult={testResult} />
                  </div>

                  {/* Telemetry rows */}
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.35rem',
                      background: 'var(--bg-subtle)',
                      padding: '0.65rem 0.85rem',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      marginBottom: '1rem',
                      fontSize: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Host Address:</span>
                      <span className="mono-cell" style={{ color: 'var(--text-primary)' }}>
                        {conn.host ? `${conn.host}${conn.port ? `:${conn.port}` : ''}` : 'Local File'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Last Tested:</span>
                      <span className="mono-cell" style={{ color: 'var(--text-primary)' }}>
                        {conn.last_tested_at
                          ? new Date(conn.last_tested_at).toLocaleString()
                          : 'Never tested'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Last Sync Time:</span>
                      <span className="mono-cell" style={{ color: 'var(--text-primary)' }}>
                        {conn.last_sync_at
                          ? new Date(conn.last_sync_at).toLocaleString()
                          : 'Never synced'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Total Records Ingested:</span>
                      <span className="mono-cell" style={{ color: 'var(--accent-brand)', fontWeight: 600 }}>
                        {(conn.synced_rows_count ?? 0).toLocaleString()} rows
                      </span>
                    </div>
                  </div>

                  {/* Inline test result banner */}
                  {testResult && (
                    <div
                      style={{
                        padding: '0.45rem 0.65rem',
                        borderRadius: 'var(--radius-xs)',
                        marginBottom: '0.85rem',
                        fontSize: '0.72rem',
                        background: testResult.status === 'success' ? 'var(--status-good-bg)' : 'var(--status-risk-bg)',
                        color: testResult.status === 'success' ? 'var(--status-good-text)' : 'var(--status-risk-text)',
                        border: `1px solid ${testResult.status === 'success' ? 'var(--status-good-border)' : 'var(--status-risk-border)'}`,
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '6px',
                      }}
                    >
                      {testResult.status === 'success' ? (
                        <CheckCircle2 size={13} style={{ flexShrink: 0, marginTop: '1px' }} />
                      ) : (
                        <AlertOctagon size={13} style={{ flexShrink: 0, marginTop: '1px' }} />
                      )}
                      <span>
                        {testResult.message}
                        {testResult.latency ? ` — ${testResult.latency}` : ''}
                      </span>
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '0.75rem',
                    borderTop: '1px solid var(--border-subtle)',
                  }}
                >
                  {/* Left: Test Connection */}
                  <button
                    id={`test-conn-${conn.id}`}
                    type="button"
                    className="secondary-btn"
                    onClick={() => handleTest(conn.id)}
                    disabled={isTesting}
                    style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}
                  >
                    <Activity size={12} className={isTesting ? 'spin' : ''} />
                    <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                  </button>

                  {/* Right: Sync + Edit + Delete */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <button
                      id={`sync-conn-${conn.id}`}
                      type="button"
                      className="primary-btn"
                      onClick={() => setActiveSyncConnector(conn)}
                      style={{ fontSize: '0.72rem', padding: '0.3rem 0.65rem' }}
                    >
                      <RotateCw size={12} />
                      <span>Sync Data</span>
                    </button>

                    <button
                      id={`edit-conn-${conn.id}`}
                      type="button"
                      className="icon-action-btn"
                      onClick={() => openEditModal(conn)}
                      title="Edit connector"
                      style={{ width: '28px', height: '28px' }}
                    >
                      <Pencil size={13} />
                    </button>

                    <button
                      id={`delete-conn-${conn.id}`}
                      type="button"
                      className="icon-action-btn"
                      onClick={() => handleDelete(conn.id)}
                      title="Disconnect database"
                      style={{ width: '28px', height: '28px', color: 'var(--status-risk-text)' }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}