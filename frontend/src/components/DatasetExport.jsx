import React, { useState, useRef, useEffect } from 'react';
import { Download, ChevronDown, FileText, FileCode } from 'lucide-react';

/**
 * DatasetExport component provides export menu with CSV and JSON options
 */
export function DatasetExport({ onExport, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format) => {
    try {
      setExporting(true);
      await onExport(format);
      setIsOpen(false);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-menu" ref={menuRef}>
      <button
        type="button"
        className="primary-btn"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exporting}
      >
        <Download size={14} />
        <span>{exporting ? 'Exporting...' : 'Export Dataset'}</span>
        <ChevronDown size={14} style={{ opacity: 0.8 }} />
      </button>

      {isOpen && (
        <div className="export-dropdown">
          <button
            type="button"
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="export-option"
          >
            <FileText size={14} style={{ color: 'var(--status-info-text)' }} />
            <span>Export CSV</span>
          </button>
          <button
            type="button"
            onClick={() => handleExport('json')}
            disabled={exporting}
            className="export-option"
          >
            <FileCode size={14} style={{ color: 'var(--accent-400)' }} />
            <span>Export JSON</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default DatasetExport;
