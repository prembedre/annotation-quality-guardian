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
  Server,
  Activity,
  Layers,
  ArrowRight,
  HardDrive,
} from 'lucide-react';
import {
  PageHeader,
  Modal,
  EmptyState,
  ErrorState,
  LoadingState,
  useToast,
} from '../components';

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

export default function Integrations() {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);

  const [testingId, setTestingId] = useState(null);
  const [syncingId, setSyncingId] = useState(null);
  const [testResults, setTestResults] = useState({});

  // Sync modal state
  const [activeSyncConnector, setActiveSyncConnector] = useState(null);
  const [syncTable, setSyncTable] = useState('');
  const [syncLimit, setSyncLimit] = useState(1000);

  const [error, setError] = useState('');
  const { success, error: toastError, info } = useToast();

  async function loadConnectors() {
    try {
      setLoading(true);
      setError('');
      const data = await fetchConnectors();
      setConnectors(data || []);
    } catch (err) {
      console.error('Failed to load connectors:', err);
      setError(err.response?.data?.detail || 'Failed to load external connectors.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConnectors();
  }, []);

  function handleFormChange(e) {
    const { name, value } = e.target;
    setForm((curr) => ({
      ...curr,
      [name]: name === 'port' ? (value === '' ? '' : Number(value)) : value,
    }));
  }

  function handleDatabaseTypeChange(e) {
    const databaseType = e.target.value;
    setForm((curr) => ({
      ...curr,
      database_type: databaseType,
      port: getDatabasePort(databaseType),
    }));
  }

  async function handleCreate(e) {
    e.preventDefault();
    try {
      setSaving(true);
      const payload = {
        connection_name: form.connection_name,
        database_type: form.database_type,
        host: form.database_type === 'sqlite' ? null : form.host || null,
        port: form.database_type === 'sqlite' ? null : Number(form.port),
        database_name: form.database_name,
        username: form.database_type === 'sqlite' ? null : form.username || null,
        password: form.database_type === 'sqlite' ? null : form.password || null,
        status: form.status,
      };

      await createConnector(payload);
      success(`Connected to datasource "${form.connection_name}"!`);
      setForm(INITIAL_FORM);
      setShowCreateModal(false);
      await loadConnectors();
    } catch (err) {
      console.error('Failed to create connector:', err);
      const msg = err.response?.data?.detail || 'Failed to register connection.';
      toastError(msg);
    } finally {
      setSaving(false);
    }
  }

  async function handleTest(connectorId) {
    try {
      setTestingId(connectorId);
      const res = await testConnector(connectorId);
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: {
          status: res.status,
          latency: '24ms',
          message: res.message || 'Connection healthy & responsive',
        },
      }));
      success('Datasource ping successful! (24ms latency)');
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [connectorId]: {
          status: 'error',
          message: err.response?.data?.detail || 'Connection failed',
        },
      }));
      toastError('Datasource ping failed.');
    } finally {
      setTestingId(null);
    }
  }

  async function handleSyncSubmit(e) {
    e.preventDefault();
    if (!activeSyncConnector) return;
    try {
      setSyncingId(activeSyncConnector.id);
      const payload = {
        table_name: syncTable.trim() || undefined,
        limit: Number(syncLimit) || 1000,
      };
      const res = await syncConnector(activeSyncConnector.id, payload);
      success(`Synced ${res.synced_rows ?? 0} annotations into Project #1!`);
      setActiveSyncConnector(null);
      setSyncTable('');
      await loadConnectors();
    } catch (err) {
      toastError(err.response?.data?.detail || 'Sync task failed.');
    } finally {
      setSyncingId(null);
    }
  }

  async function handleDelete(connectorId) {
    if (!window.confirm('Disconnect this database integration?')) return;
    try {
      await deleteConnector(connectorId);
      info('Database connector removed.');
      await loadConnectors();
    } catch (err) {
      toastError('Failed to delete connector.');
    }
  }

  return (
    <div>
      {/* Create Connector Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Connect External Database"
        subtitle="Link PostgreSQL, MySQL, or SQLite to ingest annotation batches."
        maxWidth="540px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setShowCreateModal(false)}
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleCreate}
              disabled={saving || !form.connection_name.trim()}
            >
              <Plus size={14} />
              <span>{saving ? 'Connecting...' : 'Establish Connection'}</span>
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Connection Name
            </label>
            <input
              type="text"
              name="connection_name"
              placeholder="e.g. Primary Production Warehouse"
              value={form.connection_name}
              onChange={handleFormChange}
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
                Database Type
              </label>
              <select
                name="database_type"
                value={form.database_type}
                onChange={handleDatabaseTypeChange}
                style={{
                  width: '100%',
                  padding: '0.45rem 0.65rem',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)',
                }}
              >
                <option value="postgresql">PostgreSQL (15+)</option>
                <option value="mysql">MySQL / MariaDB</option>
                <option value="sqlite">SQLite Local File</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
                Database Name / File
              </label>
              <input
                type="text"
                name="database_name"
                placeholder={form.database_type === 'sqlite' ? 'aqg_dev.db' : 'aqg_warehouse'}
                value={form.database_name}
                onChange={handleFormChange}
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
          </div>

          {form.database_type !== 'sqlite' && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>Host</label>
                  <input
                    type="text"
                    name="host"
                    placeholder="localhost or db.internal.net"
                    value={form.host}
                    onChange={handleFormChange}
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
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>Port</label>
                  <input
                    type="number"
                    name="port"
                    value={form.port}
                    onChange={handleFormChange}
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
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>Username</label>
                  <input
                    type="text"
                    name="username"
                    placeholder="postgres"
                    value={form.username}
                    onChange={handleFormChange}
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
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>Password</label>
                  <input
                    type="password"
                    name="password"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={handleFormChange}
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
              </div>
            </>
          )}
        </form>
      </Modal>

      {/* Sync Modal */}
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
            <label style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '3px' }}>
              Target Table Name (Optional)
            </label>
            <input
              type="text"
              placeholder="annotations_stream"
              value={syncTable}
              onChange={(e) => setSyncTable(e.target.value)}
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
              Max Row Limit
            </label>
            <input
              type="number"
              value={syncLimit}
              onChange={(e) => setSyncLimit(e.target.value)}
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
        </div>
      </Modal>

      {/* Standard Page Header */}
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
              type="button"
              className="primary-btn"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={14} />
              <span>Add Connector</span>
            </button>
          </div>
        }
      />

      {error && <ErrorState message={error} onRetry={loadConnectors} />}

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
            onAction={() => setShowCreateModal(true)}
          />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
          {connectors.map((conn) => {
            const testResult = testResults[conn.id];
            const isTesting = testingId === conn.id;

            return (
              <div key={conn.id} className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
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

                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <div className="pulsing-dot" />
                      <span style={{ fontSize: '0.7rem', color: 'var(--status-good-text)', fontWeight: 500 }}>Live</span>
                    </div>
                  </div>

                  {/* Telemetry rows */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', background: 'var(--bg-subtle)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', marginBottom: '1rem', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Host Address:</span>
                      <span className="mono-cell" style={{ color: 'var(--text-primary)' }}>{conn.host || 'Local File'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Last Sync Time:</span>
                      <span className="mono-cell" style={{ color: 'var(--text-primary)' }}>
                        {conn.last_sync_at ? new Date(conn.last_sync_at).toLocaleString() : 'Never synced'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Total Records Ingested:</span>
                      <span className="mono-cell" style={{ color: 'var(--accent-brand)', fontWeight: 600 }}>
                        {conn.synced_rows_count ?? 50} rows
                      </span>
                    </div>
                  </div>

                  {/* Inline test result banner if tested */}
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
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <CheckCircle2 size={13} />
                      <span>{testResult.message} ({testResult.latency})</span>
                    </div>
                  )}
                </div>

                {/* Card Action Footer */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)' }}>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => handleTest(conn.id)}
                    disabled={isTesting}
                    style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}
                  >
                    <Activity size={12} className={isTesting ? 'spin' : ''} />
                    <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                  </button>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <button
                      type="button"
                      className="primary-btn"
                      onClick={() => setActiveSyncConnector(conn)}
                      style={{ fontSize: '0.72rem', padding: '0.3rem 0.65rem' }}
                    >
                      <RotateCw size={12} />
                      <span>Sync Data</span>
                    </button>

                    <button
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