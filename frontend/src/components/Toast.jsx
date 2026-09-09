import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';

/**
 * Toast component for displaying feedback notifications
 */
export function Toast({ message, type = 'success', onClose, duration = 4000 }) {
  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  if (!message) return null;

  return (
    <div className={`toast toast-${type}`}>
      {type === 'success' ? (
        <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
      ) : (
        <AlertCircle size={18} style={{ flexShrink: 0 }} />
      )}
      <span style={{ flex: 1 }}>{message}</span>
      <button
        type="button"
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: 'inherit',
          padding: '2px',
          cursor: 'pointer',
          opacity: 0.8,
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}

export default Toast;
