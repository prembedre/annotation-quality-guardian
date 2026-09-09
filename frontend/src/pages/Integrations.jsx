import React, { useEffect, useState } from 'react';
import {
  createConnector,
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
  X,
  Server,
  Activity,
  Layers,
} from 'lucide-react';

const PROJECT_ID = 1;

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

function getDatabasePort(databaseType) {
  if (databaseType === 'mysql') return 3306;
  if (databaseType === 'sqlite') return '';
  return 5432;
}

function formatDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString();
}

export default function Integrations() {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);

  const [testingId, setTestingId] = useState(null);
  const [syncingId, setSyncingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const [testResults, setTestResults] = useState({});
  const [syncResults, setSyncResults] = useState({});

  const [syncConnectorId, setSyncConnectorId] = useState(null);
  const [syncTable, setSyncTable] = useState('');
  const [syncQuery, setSyncQuery] = useState('');
  const [syncLimit, setSyncLimit] = useState(1000);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function loadConnectors() {
    try {
      setLoading(true);
      setError('');
      const data = await fetchConnectors();
      setConnectors(data || []);
    } catch (err) {
      console.error('Failed to load connectors:', err);
      setError(
        err.response?.data?.detail || 'Failed to load external connectors.'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConnectors();
  }, []);

  function handleFormChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]:
        name === 'port' ? (value === '' ? '' : Number(value)) : value,
    }));
    setMessage('');
    setError('');
  }

  function handleDatabaseTypeChange(event) {
    const databaseType = event.target.value;
    setForm((current) => ({
      ...current,
      database_type: databaseType,
      port: getDatabasePort(databaseType),
    }));
  }

  function resetForm() {
    setForm({ ...INITIAL_FORM });
    setShowForm(false);
  }

  async function handleCreate(event) {
    event.preventDefault();
    try {
      setSaving(true);
      setMessage('');
      setError('');

      const payload = {
        connection_name: form.connection_name,
        database_type: form.database_type,
        host: form.database_type === 'sqlite' ? null : form.host || null,
        port: form.database_type === 'sqlite' ? null : Number(form.port),
        database_name: form.database_name,
        username: form.database_type === 'sqlite' ? null : form.username || null,
        password: form.database_type === 'sqlite' ? null : form.password || null,
        status: form.status,
        query_config: {},
      };

      await createConnector(payload);
      setMessage('External database connector registered successfully.');
      resetForm();
      await loadConnectors();
    } catch (err) {
      console.error('Failed to create connector:', err);
      setError(
        err.response?.data?.detail || 'Failed to create external connector.'
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleTest(connectorId) {
    try {
      setTestingId(connectorId);
      setMessage('');
      setError('');

      const result = await testConnector(connectorId);
      setTestResults((current) => ({
        ...current,
        [connectorId]: result,
      }));
    } catch (err) {
      console.error('Failed to test connector:', err);
      setError(err.response?.data?.detail || 'Failed to test connector.');
    } finally {
      setTestingId(null);
    }
  }

  async function handleDelete(connectorId) {
    const confirmed = window.confirm(
      'Are you sure you want to disconnect this external connector?'
    );
    if (!confirmed) return;

    try {
      setDeletingId(connectorId);
      setMessage('');
      setError('');

      await deleteConnector(connectorId);
      setMessage('Connector disconnected successfully.');
      await loadConnectors();
    } catch (err) {
      console.error('Failed to delete connector:', err);
      setError(err.response?.data?.detail || 'Failed to delete connector.');
    } finally {
      setDeletingId(null);
    }
  }

  function openSync(connectorId) {
    setSyncConnectorId(connectorId);
    setSyncTable('');
    setSyncQuery('');
    setSyncLimit(1000);
    setMessage('');
    setError('');
  }

  function closeSync() {
    setSyncConnectorId(null);
    setSyncTable('');
    setSyncQuery('');
    setSyncLimit(1000);
  }

  async function handleSync(event) {
    event.preventDefault();
    if (!syncConnectorId) return;

    try {
      setSyncingId(syncConnectorId);
      setMessage('');
      setError('');

      const payload = {
        project_id: PROJECT_ID,
        table_name: syncTable || null,
        custom_query: syncQuery || null,
        limit: Number(syncLimit),
      };

      const result = await syncConnector(syncConnectorId, payload);
      setSyncResults((current) => ({
        ...current,
        [syncConnectorId]: result,
      }));

      setMessage('External annotation data synced successfully into Project 1.');
      closeSync();
    } catch (err) {
      console.error('Failed to sync connector:', err);
      setError(
        err.response?.data?.detail || 'Failed to sync external annotations.'
      );
    } finally {
      setSyncingId(null);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">External Integrations</h1>
          <p className="page-subtitle">
            Manage read-only connections to external labeling databases (PostgreSQL, MySQL, SQLite) and sync annotations.
          </p>
        </div>

        <button
          type="button"
          className="primary-btn"
          onClick={() => {
            setShowForm(true);
            setMessage('');
            setError('');
          }}
        >
          <Plus size={16} />
          <span>Add Connector</span>
        </button>
      </div>

      {message && (
        <div className="alert-success">
          <CheckCircle2 size={16} />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="alert">
          <AlertOctagon size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Add Connector Modal Dialog */}
      {showForm && (
        <div className="modal-backdrop" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Connect External Database</h2>
                <p>Configure read-only credentials for your labeling source.</p>
              </div>
              <button
                type="button"
                className="modal-close"
                onClick={resetForm}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="modal-body">
              <div className="integration-form-grid">
                <div>
                  <label htmlFor="connection_name">Connection Name *</label>
                  <input
                    id="connection_name"
                    name="connection_name"
                    value={form.connection_name}
                    onChange={handleFormChange}
                    placeholder="e.g. Label Studio Production"
                    required
                    autoFocus
                  />
                </div>

                <div>
                  <label htmlFor="database_type">Engine Type</label>
                  <select
                    id="database_type"
                    name="database_type"
                    value={form.database_type}
                    onChange={handleDatabaseTypeChange}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="sqlite">SQLite</option>
                  </select>
                </div>

                {form.database_type !== 'sqlite' && (
                  <>
                    <div>
                      <label htmlFor="host">Host Server *</label>
                      <input
                        id="host"
                        name="host"
                        value={form.host}
                        onChange={handleFormChange}
                        placeholder="e.g. db.internal.example.com"
                        required
                      />
                    </div>

                    <div>
                      <label htmlFor="port">Port *</label>
                      <input
                        id="port"
                        name="port"
                        type="number"
                        min="1"
                        max="65535"
                        value={form.port}
                        onChange={handleFormChange}
                        required
                      />
                    </div>
                  </>
                )}

                <div>
                  <label htmlFor="database_name">
                    {form.database_type === 'sqlite' ? 'File Path *' : 'Database Name *'}
                  </label>
                  <input
                    id="database_name"
                    name="database_name"
                    value={form.database_name}
                    onChange={handleFormChange}
                    placeholder={
                      form.database_type === 'sqlite'
                        ? '/var/data/annotations.db'
                        : 'annotations_prod'
                    }
                    required
                  />
                </div>

                {form.database_type !== 'sqlite' && (
                  <>
                    <div>
                      <label htmlFor="username">Username</label>
                      <input
                        id="username"
                        name="username"
                        value={form.username}
                        onChange={handleFormChange}
                        placeholder="readonly_user"
                      />
                    </div>

                    <div>
                      <label htmlFor="password">Password</label>
                      <input
                        id="password"
                        name="password"
                        type="password"
                        value={form.password}
                        onChange={handleFormChange}
                        placeholder="••••••••"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label htmlFor="status">Initial Status</label>
                  <select
                    id="status"
                    name="status"
                    value={form.status}
                    onChange={handleFormChange}
                  >
                    <option value="active">Active</option>
                    <option value="disabled">Disabled</option>
                  </select>
                </div>
              </div>

              <div className="integration-readonly-note">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--status-info-text)', fontWeight: 600 }}>
                  <ShieldCheck size={14} />
                  <span>Enforced Read-Only Protocol</span>
                </div>
                <span style={{ color: 'var(--text-muted)' }}>
                  AQG never executes DDL or write transactions on your production labeling databases.
                </span>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={resetForm}
                  disabled={saving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={saving}
                >
                  {saving ? 'Registering...' : 'Register Connector'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Connected Platforms Card */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
          <div className="card-header" style={{ marginBottom: 0 }}>
            <div>
              <h2>Connected Labeling Databases</h2>
              <p>Registered database connections with synchronized schema ingest.</p>
            </div>
            <span className="badge badge-info">
              {connectors.length} connector{connectors.length === 1 ? '' : 's'}
            </span>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '1.5rem' }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        ) : connectors.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <Database size={26} />
            </div>
            <h3>No External Connectors Configured</h3>
            <p>
              Connect AQG with an external labeling tool database (PostgreSQL, MySQL, SQLite) to sync item annotations into the guardian system.
            </p>
            <button
              type="button"
              className="primary-btn"
              onClick={() => setShowForm(true)}
            >
              <Plus size={16} />
              <span>Add Your First Connector</span>
            </button>
          </div>
        ) : (
          <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Connection Name</th>
                  <th>Database Engine</th>
                  <th>Host / Endpoint</th>
                  <th>Status</th>
                  <th>Access Mode</th>
                  <th>Last Updated</th>
                  <th style={{ textAlign: 'right', paddingRight: '1.5rem' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {connectors.map((connector) => {
                  const testResult = testResults[connector.id];
                  const syncResult = syncResults[connector.id];

                  return (
                    <tr key={connector.id}>
                      <td>
                        <strong>{connector.connection_name}</strong>
                        <div
                          className="mono-cell"
                          style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}
                        >
                          ID #{connector.id}
                        </div>
                      </td>

                      <td>
                        <span className="badge badge-info" style={{ textTransform: 'uppercase' }}>
                          {connector.database_type}
                        </span>
                      </td>

                      <td className="mono-cell">
                        {connector.host || 'Local file'}
                        {connector.port ? `:${connector.port}` : ''}
                      </td>

                      <td>
                        <span
                          className={`badge ${
                            connector.status === 'active' ? 'badge-good' : 'badge-risk'
                          }`}
                        >
                          {connector.status}
                        </span>
                      </td>

                      <td>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            fontSize: '0.75rem',
                            color: 'var(--status-info-text)',
                          }}
                        >
                          <ShieldCheck size={13} />
                          <span>Read-only</span>
                        </span>
                      </td>

                      <td
                        className="mono-cell"
                        style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}
                      >
                        {formatDate(connector.updated_at || connector.created_at)}
                      </td>

                      <td style={{ textAlign: 'right', paddingRight: '1.5rem' }}>
                        <div
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.4rem',
                          }}
                        >
                          <button
                            type="button"
                            className="secondary-btn"
                            onClick={() => handleTest(connector.id)}
                            disabled={testingId === connector.id}
                            title="Test Connection Latency"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          >
                            <Activity size={12} />
                            <span>{testingId === connector.id ? 'Testing...' : 'Test'}</span>
                          </button>

                          <button
                            type="button"
                            className="secondary-btn"
                            onClick={() => openSync(connector.id)}
                            disabled={connector.status !== 'active'}
                            title="Sync Annotations"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          >
                            <RotateCw size={12} />
                            <span>Sync</span>
                          </button>

                          <button
                            type="button"
                            className="btn-danger"
                            onClick={() => handleDelete(connector.id)}
                            disabled={deletingId === connector.id}
                            title="Delete Connector"
                            style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>

                        {/* Inline Test Feedback */}
                        {testResult && (
                          <div
                            style={{
                              marginTop: '6px',
                              padding: '6px 8px',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.72rem',
                              textAlign: 'left',
                              background: testResult.success
                                ? 'var(--status-good-bg)'
                                : 'var(--status-risk-bg)',
                              border: `1px solid ${
                                testResult.success
                                  ? 'var(--status-good-border)'
                                  : 'var(--status-risk-border)'
                              }`,
                              color: testResult.success
                                ? 'var(--status-good-text)'
                                : 'var(--status-risk-text)',
                            }}
                          >
                            <strong>
                              {testResult.success ? '✓ Connected' : '✕ Error'}
                            </strong>
                            {' • '}
                            <span>{testResult.message}</span>
                            {testResult.latency_ms != null && (
                              <span className="mono-cell">
                                {' '}({Number(testResult.latency_ms).toFixed(1)}ms)
                              </span>
                            )}
                          </div>
                        )}

                        {/* Inline Sync Feedback */}
                        {syncResult && (
                          <div
                            style={{
                              marginTop: '6px',
                              padding: '6px 8px',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.72rem',
                              textAlign: 'left',
                              background: 'var(--bg-subtle)',
                              border: '1px solid var(--border-subtle)',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            <strong style={{ color: 'var(--status-good-text)' }}>
                              Sync Complete:
                            </strong>{' '}
                            <span>Fetched: {syncResult.total_fetched}</span> |{' '}
                            <span>Inserted: {syncResult.inserted_records}</span> |{' '}
                            <span>Duplicates: {syncResult.duplicate_records}</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Sync Modal */}
      {syncConnectorId && (
        <div className="modal-backdrop" onClick={closeSync}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h2>Sync Annotations</h2>
                <p>Import annotations from connector #{syncConnectorId} into Project {PROJECT_ID}.</p>
              </div>
              <button
                type="button"
                className="modal-close"
                onClick={closeSync}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSync} className="modal-body">
              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="sync-table">Source Table Name</label>
                <input
                  id="sync-table"
                  value={syncTable}
                  onChange={(e) => setSyncTable(e.target.value)}
                  placeholder="e.g. task_annotations"
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label htmlFor="sync-query">Custom SELECT Query (Optional)</label>
                <textarea
                  id="sync-query"
                  value={syncQuery}
                  onChange={(e) => setSyncQuery(e.target.value)}
                  placeholder="SELECT * FROM task_annotations WHERE validated = true"
                  rows={4}
                />
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Leave blank to perform a full scan on the table.
                </span>
              </div>

              <div style={{ marginBottom: '1.25rem' }}>
                <label htmlFor="sync-limit">Maximum Batch Size</label>
                <input
                  id="sync-limit"
                  type="number"
                  min="1"
                  max="50000"
                  value={syncLimit}
                  onChange={(e) => setSyncLimit(e.target.value)}
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={closeSync}
                  disabled={syncingId === syncConnectorId}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-btn"
                  disabled={syncingId === syncConnectorId}
                >
                  <RotateCw
                    size={14}
                    className={syncingId === syncConnectorId ? 'spin' : ''}
                  />
                  <span>
                    {syncingId === syncConnectorId ? 'Syncing...' : 'Start Sync'}
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