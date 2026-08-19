import React, { useState } from 'react';

/**
 * DatasetExport component provides export menu with CSV and JSON options
 */
export function DatasetExport({ onExport, disabled = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [exporting, setExporting] = useState(false);

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
    <div className="export-menu">
      <button
        className="primary-btn"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exporting}
      >
        {exporting ? 'Exporting...' : 'Dataset Export'}
      </button>
      {isOpen && (
        <div className="export-dropdown">
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="export-option"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={exporting}
            className="export-option"
          >
            Export JSON
          </button>
        </div>
      )}
    </div>
  );
}
