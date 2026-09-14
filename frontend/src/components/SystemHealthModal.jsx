import React from 'react';
import { Modal } from './Modal';
import { CheckCircle2, Server, Activity, Database, Cpu, HardDrive } from 'lucide-react';

export function SystemHealthModal({ isOpen, onClose }) {
  const healthMetrics = [
    { name: 'Guardian Scoring Core', status: 'Operational', latency: '18ms', icon: Cpu },
    { name: 'Primary Database (SQLite)', status: 'Connected', latency: '2ms', icon: Database },
    { name: 'Embedding Outlier Engine', status: 'Idle / Ready', latency: '42ms', icon: Activity },
    { name: 'Automated Rerouting Worker', status: 'Running', latency: '12ms', icon: Server },
    { name: 'Telemetry Storage', status: 'Healthy (94% free)', latency: '0.8ms', icon: HardDrive },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Guardian Engine Status & Diagnostics"
      subtitle="Real-time telemetry, service latency, and inference queue status."
      maxWidth="560px"
      footer={
        <button type="button" className="secondary-btn" onClick={onClose}>
          Close
        </button>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0.85rem 1rem',
            background: 'var(--status-good-bg)',
            border: '1px solid var(--status-good-border)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div className="pulsing-dot" />
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--status-good-text)' }}>
                All Quality Guardian Systems Operational
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Uptime 99.98% over last 30 days • Engine v1.2.4
              </div>
            </div>
          </div>
          <span className="badge badge-good">100% ONLINE</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div className="eyebrow" style={{ marginBottom: '0.2rem' }}>Subsystems Telemetry</div>
          {healthMetrics.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <Icon size={16} style={{ color: 'var(--accent-brand)' }} />
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-primary)' }}>
                      {item.name}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      Response latency: <span className="mono-cell">{item.latency}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--status-good-text)', fontSize: '0.75rem', fontWeight: 500 }}>
                  <CheckCircle2 size={13} />
                  <span>{item.status}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}

export default SystemHealthModal;
