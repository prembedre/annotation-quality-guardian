import React, { useState } from 'react';

export function ThresholdSlider({
  id,
  label,
  description,
  min = 0,
  max = 100,
  step = 1,
  value,
  displayValue,
  unit = '%',
  recommended,
  onChange,
  tooltipHelp,
}) {
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // percentage of value across range
  const pct = Math.min(Math.max(((value - min) / (max - min)) * 100, 0), 100);

  // percentage for recommended marker
  const recPct = recommended != null ? Math.min(Math.max(((recommended - min) / (max - min)) * 100, 0), 100) : null;

  return (
    <div style={{ marginBottom: '1.75rem' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.65rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <label htmlFor={id} style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {label}
            </label>
            {tooltipHelp && (
              <span
                style={{
                  fontSize: '0.65rem',
                  color: 'var(--text-muted)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '50%',
                  width: '14px',
                  height: '14px',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'help',
                }}
                title={tooltipHelp}
              >
                ?
              </span>
            )}
          </div>
          {description && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {description}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
          <span
            className="mono-cell"
            style={{
              fontSize: '1.15rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}
          >
            {displayValue != null ? displayValue : `${value}${unit}`}
          </span>
        </div>
      </div>

      <div
        className="threshold-slider-container"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Recommended marker */}
        {recPct != null && (
          <div
            className="threshold-rec-tick"
            style={{ left: `${recPct}%` }}
            title={`Recommended production baseline: ${recommended}${unit}`}
          >
            <span>Rec {recommended}{unit}</span>
          </div>
        )}

        {/* Multi-zone track */}
        <div className="threshold-track-zones">
          {/* Thumb marker */}
          <div
            className="threshold-thumb"
            style={{ left: `${pct}%` }}
          />
        </div>

        {/* Floating Tooltip during drag/hover */}
        {(isDragging || isHovered) && (
          <div
            style={{
              position: 'absolute',
              top: '-26px',
              left: `${pct}%`,
              transform: 'translateX(-50%)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-medium)',
              boxShadow: 'var(--shadow-md)',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              zIndex: 10,
            }}
          >
            {displayValue != null ? displayValue : `${value}${unit}`}
          </div>
        )}

        {/* Native Range Slider for full accessibility */}
        <input
          id={id}
          className="threshold-native-slider"
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={() => setIsDragging(false)}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={() => setIsDragging(false)}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
        <span>Min {min}{unit}</span>
        <span style={{ color: 'var(--accent-400)' }}>
          Current: {displayValue != null ? displayValue : `${value}${unit}`}
        </span>
        <span>Max {max}{unit}</span>
      </div>
    </div>
  );
}

export default ThresholdSlider;
