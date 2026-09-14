import React, { useState } from 'react';
import { Check, Copy, Terminal } from 'lucide-react';

export function CodeBlock({ snippets, defaultTab = 'curl' }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [copied, setCopied] = useState(false);

  // snippets = { curl: '...', python: '...', js: '...' }
  const currentCode = snippets[activeTab] || '';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy', e);
    }
  };

  const tabs = Object.keys(snippets);

  return (
    <div className="codeblock-card">
      <div className="codeblock-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
            <Terminal size={13} />
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>API Command</span>
          </div>

          {tabs.length > 1 && (
            <div className="codeblock-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`codeblock-tab ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          type="button"
          className="codeblock-copy-btn"
          onClick={handleCopy}
          title="Copy to clipboard"
        >
          {copied ? (
            <>
              <Check size={12} style={{ color: 'var(--status-good-text)' }} />
              <span style={{ color: 'var(--status-good-text)' }}>Copied</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      <pre className="codeblock-content">
        <code>{currentCode}</code>
      </pre>
    </div>
  );
}

export default CodeBlock;
