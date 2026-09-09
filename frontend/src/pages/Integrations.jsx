import { useEffect, useState } from 'react';
import {
  createConnector,
  deleteConnector,
  fetchConnectors,
  syncConnector,
  testConnector,
} from '../services/integrationService';

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
  if (databaseType === 'mysql') {
    return 3306;
  }

  if (databaseType === 'sqlite') {
    return '';
  }

  return 5432;
}

function formatDate(value) {
  if (!value) {
    return 'N/A';
  }

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
        err.response?.data?.detail ||
          'Failed to load external connectors.'
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
        name === 'port'
          ? value === ''
            ? ''
            : Number(value)
          : value,
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
        host:
          form.database_type === 'sqlite'
            ? null
            : form.host || null,
        port:
          form.database_type === 'sqlite'
            ? null
            : Number(form.port),
        database_name: form.database_name,
        username:
          form.database_type === 'sqlite'
            ? null
            : form.username || null,
        password:
          form.database_type === 'sqlite'
            ? null
            : form.password || null,
        status: form.status,
        query_config: {},
      };

      await createConnector(payload);

      setMessage(
        'External connector created successfully.'
      );

      resetForm();

      await loadConnectors();
    } catch (err) {
      console.error('Failed to create connector:', err);

      setError(
        err.response?.data?.detail ||
          'Failed to create external connector.'
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

      setError(
        err.response?.data?.detail ||
          'Failed to test connector.'
      );
    } finally {
      setTestingId(null);
    }
  }

  async function handleDelete(connectorId) {
    const confirmed = window.confirm(
      'Are you sure you want to delete this connector?'
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(connectorId);
      setMessage('');
      setError('');

      await deleteConnector(connectorId);

      setMessage('Connector deleted successfully.');

      await loadConnectors();
    } catch (err) {
      console.error('Failed to delete connector:', err);

      setError(
        err.response?.data?.detail ||
          'Failed to delete connector.'
      );
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

    if (!syncConnectorId) {
      return;
    }

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

      const result = await syncConnector(
        syncConnectorId,
        payload
      );

      setSyncResults((current) => ({
        ...current,
        [syncConnectorId]: result,
      }));

      setMessage(
        'External annotations synced successfully.'
      );

      closeSync();
    } catch (err) {
      console.error('Failed to sync connector:', err);

      setError(
        err.response?.data?.detail ||
          'Failed to sync external annotations.'
      );
    } finally {
      setSyncingId(null);
    }
  }

  return (
    <div className="integration-page">
      <div className="integration-header">
        <div>
          <h1>External Integrations</h1>

          <p>
            Manage read-only connections to external labeling
            databases and sync annotation data into AQG.
          </p>
        </div>

        <button
          type="button"
          className="integration-primary-button"
          onClick={() => {
            setShowForm((current) => !current);
            setMessage('');
            setError('');
          }}
        >
          {showForm ? 'Close Form' : '+ Add Connector'}
        </button>
      </div>

      {message && (
        <div className="integration-success">
          {message}
        </div>
      )}

      {error && (
        <div className="integration-error">
          {error}
        </div>
      )}

      {showForm && (
        <section className="integration-card">
          <div className="integration-card-header">
            <div>
              <h2>Add External Connector</h2>

              <p>
                Configure a read-only connection to an external
                labeling database.
              </p>
            </div>
          </div>

          <form
            className="integration-form"
            onSubmit={handleCreate}
          >
            <div className="integration-form-grid">
              <div className="integration-field">
                <label htmlFor="connection_name">
                  Connection Name
                </label>

                <input
                  id="connection_name"
                  name="connection_name"
                  value={form.connection_name}
                  onChange={handleFormChange}
                  placeholder="Label Studio Production"
                  required
                />
              </div>

              <div className="integration-field">
                <label htmlFor="database_type">
                  Database Type
                </label>

                <select
                  id="database_type"
                  name="database_type"
                  value={form.database_type}
                  onChange={handleDatabaseTypeChange}
                >
                  <option value="postgresql">
                    PostgreSQL
                  </option>

                  <option value="mysql">
                    MySQL
                  </option>

                  <option value="sqlite">
                    SQLite
                  </option>
                </select>
              </div>

              {form.database_type !== 'sqlite' && (
                <>
                  <div className="integration-field">
                    <label htmlFor="host">
                      Host
                    </label>

                    <input
                      id="host"
                      name="host"
                      value={form.host}
                      onChange={handleFormChange}
                      placeholder="localhost"
                      required
                    />
                  </div>

                  <div className="integration-field">
                    <label htmlFor="port">
                      Port
                    </label>

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

              <div className="integration-field">
                <label htmlFor="database_name">
                  Database Name / Path
                </label>

                <input
                  id="database_name"
                  name="database_name"
                  value={form.database_name}
                  onChange={handleFormChange}
                  placeholder={
                    form.database_type === 'sqlite'
                      ? '/path/to/labels.db'
                      : 'labeling_database'
                  }
                  required
                />
              </div>

              {form.database_type !== 'sqlite' && (
                <>
                  <div className="integration-field">
                    <label htmlFor="username">
                      Username
                    </label>

                    <input
                      id="username"
                      name="username"
                      value={form.username}
                      onChange={handleFormChange}
                      placeholder="readonly_user"
                    />
                  </div>

                  <div className="integration-field">
                    <label htmlFor="password">
                      Password
                    </label>

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

              <div className="integration-field">
                <label htmlFor="status">
                  Status
                </label>

                <select
                  id="status"
                  name="status"
                  value={form.status}
                  onChange={handleFormChange}
                >
                  <option value="active">
                    Active
                  </option>

                  <option value="disabled">
                    Disabled
                  </option>
                </select>
              </div>
            </div>

            <div className="integration-readonly-note">
              <strong>Read-only integration</strong>

              <span>
                AQG uses this connection to read annotation data.
                Write operations to the external database are not
                performed.
              </span>
            </div>

            <div className="integration-form-actions">
              <button
                type="button"
                className="integration-secondary-button"
                onClick={resetForm}
                disabled={saving}
              >
                Cancel
              </button>

              <button
                type="submit"
                className="integration-primary-button"
                disabled={saving}
              >
                {saving ? 'Creating...' : 'Create Connector'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="integration-card">
        <div className="integration-card-header">
          <div>
            <h2>Connected Platforms</h2>

            <p>
              External database connections registered with AQG.
            </p>
          </div>

          <span className="integration-count">
            {connectors.length} connector
            {connectors.length === 1 ? '' : 's'}
          </span>
        </div>

        {loading && (
          <div className="integration-loading">
            Loading connectors...
          </div>
        )}

        {!loading && connectors.length === 0 && (
          <div className="integration-empty">
            <strong>
              No external connectors configured.
            </strong>

            <span>
              Add a connector to connect AQG with an external
              labeling database.
            </span>
          </div>
        )}

        {!loading && connectors.length > 0 && (
          <div className="integration-table-wrapper">
            <table className="integration-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Database</th>
                  <th>Host</th>
                  <th>Status</th>
                  <th>Access</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {connectors.map((connector) => {
                  const testResult =
                    testResults[connector.id];

                  const syncResult =
                    syncResults[connector.id];

                  return (
                    <tr key={connector.id}>
                      <td>
                        <strong>
                          {connector.connection_name}
                        </strong>

                        <small>
                          ID #{connector.id}
                        </small>
                      </td>

                      <td>
                        {connector.database_type}
                      </td>

                      <td>
                        {connector.host || 'Local / file'}
                        {connector.port
                          ? `:${connector.port}`
                          : ''}
                      </td>

                      <td>
                        <span
                          className={`integration-status ${
                            connector.status === 'active'
                              ? 'integration-status-active'
                              : 'integration-status-disabled'
                          }`}
                        >
                          {connector.status}
                        </span>
                      </td>

                      <td>
                        <span className="integration-readonly-badge">
                          Read-only
                        </span>
                      </td>

                      <td>
                        {formatDate(
                          connector.updated_at ||
                            connector.created_at
                        )}
                      </td>

                      <td>
                        <div className="integration-actions">
                          <button
                            type="button"
                            className="integration-action-button"
                            onClick={() =>
                              handleTest(connector.id)
                            }
                            disabled={
                              testingId === connector.id
                            }
                          >
                            {testingId === connector.id
                              ? 'Testing...'
                              : 'Test'}
                          </button>

                          <button
                            type="button"
                            className="integration-action-button"
                            onClick={() =>
                              openSync(connector.id)
                            }
                            disabled={
                              connector.status !== 'active'
                            }
                          >
                            Sync
                          </button>

                          <button
                            type="button"
                            className="integration-delete-button"
                            onClick={() =>
                              handleDelete(connector.id)
                            }
                            disabled={
                              deletingId === connector.id
                            }
                          >
                            {deletingId === connector.id
                              ? 'Deleting...'
                              : 'Delete'}
                          </button>
                        </div>

                        {testResult && (
                          <div
                            className={`integration-result ${
                              testResult.success
                                ? 'integration-result-success'
                                : 'integration-result-error'
                            }`}
                          >
                            <strong>
                              {testResult.success
                                ? 'Connection successful'
                                : 'Connection failed'}
                            </strong>

                            <span>
                              {testResult.message}
                            </span>

                            {testResult.latency_ms !=
                              null && (
                              <span>
                                Latency:{' '}
                                {Number(
                                  testResult.latency_ms
                                ).toFixed(1)}{' '}
                                ms
                              </span>
                            )}
                          </div>
                        )}

                        {syncResult && (
                          <div className="integration-sync-result">
                            <strong>
                              Last sync
                            </strong>

                            <span>
                              Fetched:{' '}
                              {syncResult.total_fetched}
                            </span>

                            <span>
                              Inserted:{' '}
                              {syncResult.inserted_records}
                            </span>

                            <span>
                              Duplicates:{' '}
                              {syncResult.duplicate_records}
                            </span>

                            <span>
                              Failed:{' '}
                              {syncResult.failed_records}
                            </span>
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
      </section>

      {syncConnectorId && (
        <div className="integration-modal-backdrop">
          <div className="integration-modal">
            <div className="integration-modal-header">
              <div>
                <h2>Sync External Annotations</h2>

                <p>
                  Import read-only annotation data into Project{' '}
                  {PROJECT_ID}.
                </p>
              </div>

              <button
                type="button"
                className="integration-modal-close"
                onClick={closeSync}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSync}>
              <div className="integration-field">
                <label htmlFor="sync-table">
                  Table Name
                </label>

                <input
                  id="sync-table"
                  value={syncTable}
                  onChange={(event) =>
                    setSyncTable(event.target.value)
                  }
                  placeholder="annotations"
                />
              </div>

              <div className="integration-field">
                <label htmlFor="sync-query">
                  Custom SELECT Query
                </label>

                <textarea
                  id="sync-query"
                  value={syncQuery}
                  onChange={(event) =>
                    setSyncQuery(event.target.value)
                  }
                  placeholder="SELECT * FROM annotations"
                  rows="5"
                />

                <small>
                  Leave blank to use the table name.
                </small>
              </div>

              <div className="integration-field">
                <label htmlFor="sync-limit">
                  Maximum Rows
                </label>

                <input
                  id="sync-limit"
                  type="number"
                  min="1"
                  max="50000"
                  value={syncLimit}
                  onChange={(event) =>
                    setSyncLimit(event.target.value)
                  }
                />
              </div>

              <div className="integration-form-actions">
                <button
                  type="button"
                  className="integration-secondary-button"
                  onClick={closeSync}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="integration-primary-button"
                  disabled={
                    syncingId === syncConnectorId
                  }
                >
                  {syncingId === syncConnectorId
                    ? 'Syncing...'
                    : 'Start Sync'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}