import React, { useState, useRef, useCallback } from 'react';
import {
  UploadCloud,
  FileText,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  X,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { Modal } from './Modal';
import { uploadDataset } from '../services/api';

export function DatasetUploadModal({
  isOpen,
  onClose,
  projects = [],
  activeProjectId = null,
  initialFile = null,
  onSuccess = null,
}) {
  const [selectedFile, setSelectedFile] = useState(initialFile);
  const [targetProjectId, setTargetProjectId] = useState(activeProjectId || '');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Sync initial file if passed
  React.useEffect(() => {
    if (initialFile) {
      setSelectedFile(initialFile);
    }
  }, [initialFile]);

  // Sync active project if changed
  React.useEffect(() => {
    if (activeProjectId && !targetProjectId) {
      setTargetProjectId(activeProjectId);
    }
  }, [activeProjectId, targetProjectId]);

  const handleReset = () => {
    setSelectedFile(null);
    setProgress(0);
    setResult(null);
    setError('');
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    setError('');
    setResult(null);
    const validExtensions = ['.csv', '.json'];
    const hasValidExt = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );

    if (!hasValidExt) {
      setError('Unsupported file type. Please upload a .csv or .json file.');
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      validateAndSetFile(file);
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      setError('');
      setProgress(10);

      const pid = targetProjectId ? parseInt(targetProjectId, 10) : null;
      const data = await uploadDataset(selectedFile, pid, (pct) => {
        setProgress(pct);
      });

      setResult(data);
      if (onSuccess) {
        onSuccess(data);
      }
    } catch (err) {
      console.error('Dataset upload failed:', err);
      const detail =
        err.response?.data?.detail ||
        err.message ||
        'Failed to upload dataset. Please check the file format.';
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setUploading(false);
    }
  };

  const handleModalClose = () => {
    if (uploading) return;
    handleReset();
    onClose();
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleModalClose}
      title="Upload Annotation Dataset"
      subtitle="Import raw annotations and labels via CSV or JSON file format."
      maxWidth="620px"
      footer={
        result ? (
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleReset}
            >
              <RefreshCw size={14} />
              <span>Upload Another</span>
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleModalClose}
            >
              <span>Done</span>
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              className="secondary-btn"
              onClick={handleModalClose}
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
            >
              {uploading ? (
                <>
                  <RefreshCw size={14} className="spin-slow" />
                  <span>Ingesting ({progress}%)…</span>
                </>
              ) : (
                <>
                  <UploadCloud size={14} />
                  <span>Upload & Ingest</span>
                </>
              )}
            </button>
          </>
        )
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {error && (
          <div
            style={{
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#dc2626',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
            }}
          >
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>{error}</div>
          </div>
        )}

        {/* Success / Result Summary View */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <CheckCircle2 size={24} style={{ color: '#059669', flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                  Ingestion Complete
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {result.message || 'Dataset records successfully processed.'}
                </div>
              </div>
            </div>

            {/* Ingestion Metric Badges */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '0.5rem',
                padding: '0.75rem',
                background: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                textAlign: 'center',
              }}
            >
              <div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Total
                </div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                  {result.total_records ?? 0}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: '#059669', textTransform: 'uppercase' }}>
                  Ingested
                </div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#059669' }}>
                  {result.inserted_records ?? 0}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: '#d97706', textTransform: 'uppercase' }}>
                  Skipped / Dup
                </div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#d97706' }}>
                  {result.duplicate_records ?? 0}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '0.65rem', color: '#dc2626', textTransform: 'uppercase' }}>
                  Failed
                </div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#dc2626' }}>
                  {result.failed_records ?? 0}
                </div>
              </div>
            </div>

            {/* Validation Errors Table (if any) */}
            {result.errors && result.errors.length > 0 && (
              <div>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#dc2626', marginBottom: '0.4rem' }}>
                  Validation Issues ({result.errors.length})
                </div>
                <div
                  style={{
                    maxHeight: '150px',
                    overflowY: 'auto',
                    border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.78rem',
                  }}
                >
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-subtle)', borderBottom: '1px solid var(--border-medium)' }}>
                        <th style={{ padding: '6px 10px', textAlign: 'left', width: '60px' }}>Row</th>
                        <th style={{ padding: '6px 10px', textAlign: 'left' }}>Error Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.errors.map((errItem, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '6px 10px', fontWeight: 600 }}>
                            {errItem.row || idx + 1}
                          </td>
                          <td style={{ padding: '6px 10px', color: 'var(--text-muted)' }}>
                            {errItem.error || (Array.isArray(errItem.errors) ? errItem.errors.join('; ') : JSON.stringify(errItem))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Upload Form View */}
        {!result && (
          <>
            {/* Target Project Selection */}
            <div>
              <label
                htmlFor="target-project-select"
                style={{ fontSize: '0.78rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}
              >
                Target Project
              </label>
              <select
                id="target-project-select"
                className="select"
                value={targetProjectId}
                onChange={(e) => setTargetProjectId(e.target.value)}
                disabled={uploading}
                style={{ width: '100%' }}
              >
                <option value="">Auto-detect / Use Project ID from dataset</option>
                {projects.map((proj) => (
                  <option key={proj.id} value={proj.id}>
                    Project #{proj.id}: {proj.name}
                  </option>
                ))}
              </select>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '3px' }}>
                If your file contains a &quot;project_id&quot; column, it will be mapped automatically.
              </span>
            </div>

            {/* Drag & Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: isDragging
                  ? '2px dashed var(--accent-brand)'
                  : '2px dashed var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                padding: '2rem 1.5rem',
                textAlign: 'center',
                cursor: uploading ? 'default' : 'pointer',
                background: isDragging
                  ? 'rgba(14, 165, 233, 0.05)'
                  : 'var(--bg-subtle)',
                transition: 'all var(--transition-fast)',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json,text/csv,application/json"
                style={{ display: 'none' }}
                onChange={handleFileChange}
                disabled={uploading}
              />

              <div
                style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '50%',
                  background: 'var(--bg-surface-elevated)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-brand)',
                  margin: '0 auto 0.75rem auto',
                }}
              >
                <UploadCloud size={24} />
              </div>

              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {isDragging ? 'Drop file here…' : 'Click to select or drag & drop dataset'}
              </div>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Supports standard CSV with headers (project_id, external_id, annotator_id, label) or structured JSON.
              </p>
            </div>

            {/* Selected File Card */}
            {selectedFile && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border-medium)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {selectedFile.name.endsWith('.json') ? (
                    <FileCode size={20} style={{ color: '#8b5cf6' }} />
                  ) : (
                    <FileText size={20} style={{ color: '#0ea5e9' }} />
                  )}
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {selectedFile.name}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {formatFileSize(selectedFile.size)}
                    </div>
                  </div>
                </div>

                {!uploading && (
                  <button
                    type="button"
                    className="icon-action-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    title="Remove file"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>
            )}

            {/* Progress Bar during upload */}
            {uploading && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '4px' }}>
                  <span>Uploading & Validating…</span>
                  <span>{progress}%</span>
                </div>
                <div
                  style={{
                    height: '6px',
                    width: '100%',
                    background: 'var(--border-subtle)',
                    borderRadius: '3px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      height: '100%',
                      width: `${progress}%`,
                      background: 'var(--accent-brand)',
                      transition: 'width 0.3s ease',
                    }}
                  />
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}
