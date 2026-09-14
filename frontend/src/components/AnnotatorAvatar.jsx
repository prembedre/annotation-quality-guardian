import React from 'react';

/**
 * Curated tonal gradient palette (6-8 pairs)
 * Subtle diagonal gradients using two tonal shades of the same hue
 */
const AVATAR_PALETTES = [
  { gradient: 'linear-gradient(135deg, #7C6AE8 0%, #4B3FA0 100%)', border: 'rgba(216, 208, 255, 0.3)' }, // Violet / Indigo
  { gradient: 'linear-gradient(135deg, #FF9F5B 0%, #E8722C 100%)', border: 'rgba(255, 222, 200, 0.3)' }, // Warm Sunset / Orange
  { gradient: 'linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)', border: 'rgba(186, 230, 253, 0.3)' }, // Sky / Azure
  { gradient: 'linear-gradient(135deg, #34D399 0%, #059669 100%)', border: 'rgba(167, 243, 208, 0.3)' }, // Emerald / Teal
  { gradient: 'linear-gradient(135deg, #F472B6 0%, #DB2777 100%)', border: 'rgba(251, 207, 232, 0.3)' }, // Rose / Berry
  { gradient: 'linear-gradient(135deg, #FBBF24 0%, #D97706 100%)', border: 'rgba(254, 240, 138, 0.3)' }, // Amber / Honey
  { gradient: 'linear-gradient(135deg, #60A5FA 0%, #2563EB 100%)', border: 'rgba(191, 219, 254, 0.3)' }, // Royal Blue
  { gradient: 'linear-gradient(135deg, #C084FC 0%, #7E22CE 100%)', border: 'rgba(233, 213, 255, 0.3)' }, // Purple / Orchid
];

/**
 * Deterministically hash an identifier (name or id) to an index
 */
export function getAvatarPalette(identifier) {
  const str = String(identifier || '??').trim();
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0; // Convert to 32bit integer
  }
  const index = Math.abs(hash) % AVATAR_PALETTES.length;
  return AVATAR_PALETTES[index];
}

/**
 * Extract 2-letter initials from full name or identifier
 */
export function getInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

/**
 * Annotator Avatar Component with tonal gradient, soft depth shadow,
 * subtle ring, and refined initials typography.
 */
export default function AnnotatorAvatar({
  name,
  id,
  size = 28,
  showStatus = false,
  isOnline = false,
  className = '',
  style = {},
}) {
  const identifier = name || (id ? `User-${id}` : '??');
  const palette = getAvatarPalette(identifier);
  const initials = getInitials(name || identifier);

  const fontSize = Math.max(9, Math.round(size * 0.38));

  return (
    <div
      className={`annotator-avatar-wrapper ${className}`}
      style={{
        position: 'relative',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: `${size}px`,
        height: `${size}px`,
        flexShrink: 0,
        ...style,
      }}
      title={name || `Annotator #${id || ''}`}
    >
      <div
        className="annotator-avatar-circle"
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          background: palette.gradient,
          border: '1.5px solid rgba(255, 255, 255, 0.18)',
          boxShadow: '0 2px 6px rgba(0, 0, 0, 0.3), inset 0 1px 1px rgba(255, 255, 255, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FFFFFF',
          fontWeight: 600,
          fontSize: `${fontSize}px`,
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          userSelect: 'none',
          boxSizing: 'border-box',
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.25)',
        }}
      >
        {initials}
      </div>

      {showStatus && (
        <span
          className="annotator-status-dot"
          style={{
            position: 'absolute',
            bottom: '0px',
            right: '0px',
            width: `${Math.max(6, Math.round(size * 0.26))}px`,
            height: `${Math.max(6, Math.round(size * 0.26))}px`,
            borderRadius: '50%',
            backgroundColor: isOnline ? 'var(--status-good-solid, #10B981)' : 'var(--text-muted, #94A3B8)',
            border: '1.5px solid var(--bg-surface, #1E293B)',
            boxShadow: '0 0 4px rgba(0,0,0,0.4)',
          }}
        />
      )}
    </div>
  );
}
