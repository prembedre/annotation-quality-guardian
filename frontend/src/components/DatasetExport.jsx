import React, { useState } from 'react';
import { Download, FileText, FileCode, Check, Database } from 'lucide-react';
import { Modal } from './Modal';

export function DatasetExport({ onExport, disabled = false, totalCount = 0, flaggedCount = 0 }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [format, setFormat] = useState('csv');
  const [scope, setScope] = useState('all'); // 'all', 'flagged', 'filtered'
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    try {
      setExporting(true);
      await onExport(format, scope);
      setModalOpen(false);
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="primary-btn"
        onClick={() => setModalOpen(true)}
        disabled={disabled}
      >
        <Download size={14} />
        <span>Export Dataset</span>
      </button>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Export Dataset Scope & Format"
        subtitle="Download verified annotations and flag telemetry for offline evaluation."
        maxWidth="500px"
        footer={
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={() => setModalOpen(false)}
              disabled={exporting}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleExport}
              disabled={exporting}
            >
              <Download size={14} />
              <span>{exporting ? 'Generating Export...' : `Download ${format.toUpperCase()}`}</span>
            </button>
          </>
        }
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Format Selection */}
          <div>
            <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>Export File Format</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.65rem' }}>
              {[
                { id: 'csv', name: 'CSV', desc: 'Spreadsheet compatible', icon: FileText },
                { id: 'json', name: 'JSON', desc: 'Nested telemetry trees', icon: FileCode },
                { id: 'parquet', name: 'Parquet', desc: 'Optimized ML format', icon: Database },
              ].map((fmt) => {
                const Icon = fmt.icon;
                const isSel = format === fmt.id;
                return (
                  <button
                    key={fmt.id}
                    type="button"
                    onClick={() => setFormat(fmt.id)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      padding: '0.75rem',
                      background: isSel ? 'rgba(14, 165, 233, 0.1)' : 'var(--bg-subtle)',
                      border: `1px solid ${isSel ? 'var(--accent-brand)' : 'var(--border-subtle)'}`,
                      borderRadius: 'var(--radius-sm)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all var(--transition-fast)',
                    }}
                  >
                    <Icon size={16} style={{ color: isSel ? 'var(--accent-brand)' : 'var(--text-secondary)', marginBottom: '4px' }} />
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{fmt.name}</span>
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>{fmt.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Scope Selection */}
          <div>
            <div className="eyebrow" style={{ marginBottom: '0.5rem' }}>Export Filter Scope</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {[
                { id: 'all', label: 'All Items in Dataset', count: totalCount },
                { id: 'flagged', label: 'Flagged & Disputed Items Only', count: flaggedCount },
                { id: 'filtered', label: 'Current Filter Results', count: 'Active view' },
              ].map((sc) => (
                <label
                  key={sc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    background: scope === sc.id ? 'var(--bg-surface-elevated)' : 'var(--bg-subtle)',
                    border: `1px solid ${scope === sc.id ? 'var(--border-medium)' : 'var(--border-subtle)'}`,
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                    <input
                      type="radio"
                      name="exportScope"
                      checked={scope === sc.id}
                      onChange={() => setScope(sc.id)}
                    />
                    <span style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {sc.label}
                    </span>
                  </div>
                  <span className="mono-cell" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {sc.count}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </>
  );
}

export default DatasetExport;
