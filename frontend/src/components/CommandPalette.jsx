import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutDashboard,
  Award,
  CheckSquare,
  AlertTriangle,
  Sliders,
  Database,
  Bot,
  GitCompare,
  FolderGit2,
  Users,
  ShieldCheck,
  X,
  ArrowRight,
} from 'lucide-react';

const STATIC_COMMANDS = [
  { id: 'dash', title: 'Quality Dashboard', category: 'Navigation', icon: LayoutDashboard, path: '/' },
  { id: 'scores', title: 'Quality Scores', category: 'Navigation', icon: Award, path: '/scores' },
  { id: 'review', title: 'Review Queue', category: 'Navigation', icon: CheckSquare, path: '/review-queue' },
  { id: 'ambiguity', title: 'Ambiguous Classes', category: 'Navigation', icon: AlertTriangle, path: '/ambiguity' },
  { id: 'settings', title: 'Project Settings', category: 'Navigation', icon: Sliders, path: '/project-settings' },
  { id: 'integrations', title: 'Database Integrations', category: 'Navigation', icon: Database, path: '/integrations' },
  { id: 'automation', title: 'Rerouting & Automation', category: 'Navigation', icon: Bot, path: '/automation' },
  { id: 'ab', title: 'A/B Guidelines Experiment', category: 'Navigation', icon: GitCompare, path: '/ab-testing' },
  { id: 'projects', title: 'Data Projects', category: 'Navigation', icon: FolderGit2, path: '/projects' },
  { id: 'ann-1', title: 'Annotator #1 — Alice Chen', category: 'Annotators', icon: Users, path: '/?annotator=1' },
  { id: 'ann-2', title: 'Annotator #2 — Bob Miller', category: 'Annotators', icon: Users, path: '/?annotator=2' },
  { id: 'ann-3', title: 'Annotator #3 — Clara Garcia', category: 'Annotators', icon: Users, path: '/?annotator=3' },
  { id: 'flag-gold', title: 'View Gold Label Mismatches', category: 'Quick Filters', icon: ShieldCheck, path: '/review-queue?risk=risk' },
  { id: 'flag-outlier', title: 'View Embedding Outliers', category: 'Quick Filters', icon: AlertTriangle, path: '/review-queue?risk=medium' },
];

export function CommandPalette({ isOpen, onClose }) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const filtered = STATIC_COMMANDS.filter((cmd) =>
    cmd.title.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    function handleKeyDown(e) {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          navigate(filtered[selectedIndex].path);
          onClose();
        }
      } else if (e.key === 'Escape') {
        onClose();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filtered, selectedIndex, navigate, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-dialog"
        style={{ maxWidth: '580px', padding: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0.85rem 1.15rem',
            borderBottom: '1px solid var(--border-subtle)',
            gap: '0.65rem',
          }}
        >
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command, page name, annotator, or filter..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.88rem',
            }}
          />
          <span className="kbd-shortcut">ESC</span>
        </div>

        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '0.5rem' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '1.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              No matching commands or pages found.
            </div>
          ) : (
            filtered.map((item, index) => {
              const Icon = item.icon;
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => {
                    navigate(item.path);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.6rem 0.85rem',
                    borderRadius: 'var(--radius-sm)',
                    background: isSelected ? 'var(--bg-surface-hover)' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div
                      style={{
                        width: '26px',
                        height: '26px',
                        borderRadius: 'var(--radius-xs)',
                        background: isSelected ? 'var(--accent-brand)' : 'var(--bg-surface-elevated)',
                        color: isSelected ? '#FFFFFF' : 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'all var(--transition-fast)',
                      }}
                    >
                      <Icon size={14} />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                        {item.title}
                      </div>
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                        {item.category}
                      </div>
                    </div>
                  </div>

                  {isSelected && (
                    <ArrowRight size={14} style={{ color: 'var(--accent-brand)' }} />
                  )}
                </div>
              );
            })
          )}
        </div>

        <div
          style={{
            padding: '0.5rem 1rem',
            background: 'var(--bg-subtle)',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
          }}
        >
          <span>Use <kbd className="kbd-shortcut">↑</kbd> <kbd className="kbd-shortcut">↓</kbd> to navigate</span>
          <span>Press <kbd className="kbd-shortcut">↵</kbd> to select</span>
        </div>
      </div>
    </div>
  );
}

export default CommandPalette;
