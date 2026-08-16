import React from 'react';

function Dashboard() {
  return (
    <div>
      <h1 className="page-title">Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
        <div className="card">
          <h2>Total Annotations</h2>
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>—</p>
        </div>
        <div className="card">
          <h2>Active Projects</h2>
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>—</p>
        </div>
        <div className="card">
          <h2>Avg. Quality Score</h2>
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>—</p>
        </div>
      </div>

      <div className="card">
        <h2>Recent Activity</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>
          No recent activity to display. Connect the backend to see live data.
        </p>
      </div>
    </div>
  );
}

export default Dashboard;
