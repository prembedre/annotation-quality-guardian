import React, { useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  NavLink,
  useLocation,
} from 'react-router-dom';
import {
  Shield,
  LayoutDashboard,
  Award,
  CheckSquare,
  AlertTriangle,
  Sliders,
  Database,
  Bot,
  GitCompare,
  FolderGit2,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';

import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Scores from './pages/Scores';
import ReviewQueue from './pages/ReviewQueue';
import ProjectSettings from './pages/ProjectSettings';
import Integrations from './pages/Integrations';
import AutomationDashboard from './pages/AutomationDashboard';
import ABTesting from './pages/ABTesting';
import AmbiguityInsights from './pages/AmbiguityInsights';

const NAV_GROUPS = [
  {
    title: 'Monitor',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
      { to: '/scores', label: 'Scores', icon: Award },
      { to: '/review-queue', label: 'Review Queue', icon: CheckSquare },
      { to: '/ambiguity', label: 'Ambiguous Classes', icon: AlertTriangle },
    ],
  },
  {
    title: 'Configure',
    items: [
      { to: '/project-settings', label: 'Project Settings', icon: Sliders },
      { to: '/integrations', label: 'Integrations', icon: Database },
      { to: '/automation', label: 'Automation', icon: Bot },
      { to: '/ab-testing', label: 'A/B Testing', icon: GitCompare },
    ],
  },
  {
    title: 'Data',
    items: [
      { to: '/projects', label: 'Projects', icon: FolderGit2 },
    ],
  },
];

function getBreadcrumb(pathname) {
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (item.end ? pathname === item.to : pathname.startsWith(item.to)) {
        return { group: group.title, page: item.label };
      }
    }
  }
  return { group: 'Overview', page: 'Dashboard' };
}

function NavigationShell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const breadcrumb = getBreadcrumb(location.pathname);

  const closeMobile = () => setMobileOpen(false);

  return (
    <div className="app">
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-header">
          <div className="brand-icon-shield">
            <Shield size={20} />
          </div>
          <div className="brand-details">
            <div className="brand-title-row">
              <span className="brand-name">AQG</span>
              <span className="brand-pill">v1.2</span>
            </div>
            <span className="brand-tagline">Quality Guardian</span>
          </div>
        </div>

        {/* Persistent Project Anchor */}
        <div className="sidebar-project-select" title="Active Project">
          <div className="project-info">
            <span className="project-meta-label">Active Project</span>
            <div className="project-name-value">
              <span className="project-status-dot" />
              <span>Project 1</span>
            </div>
          </div>
          <span
            style={{
              fontSize: '0.68rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            PROD
          </span>
        </div>

        {/* Grouped Navigation */}
        <nav className="sidebar-content">
          {NAV_GROUPS.map((group) => (
            <div key={group.title}>
              <div className="nav-section-title">{group.title}</div>
              <ul className="sidebar-nav-list">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <li key={item.to}>
                      <NavLink
                        to={item.to}
                        end={item.end}
                        className={({ isActive }) =>
                          `sidebar-nav-item ${isActive ? 'active' : ''}`
                        }
                        onClick={closeMobile}
                      >
                        <Icon size={16} />
                        <span>{item.label}</span>
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="sidebar-footer">
          <span>Guardian Engine</span>
          <span className="sidebar-version-badge">ONLINE</span>
        </div>
      </aside>

      {/* Content Wrapper */}
      <div className="content-wrapper">
        {/* Slim Sticky Top Navigation Bar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="mobile-nav-toggle"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>

            <div className="breadcrumbs">
              <span className="crumb-group">{breadcrumb.group}</span>
              <ChevronRight size={13} style={{ color: 'var(--text-disabled)' }} />
              <span className="crumb-active">{breadcrumb.page}</span>
            </div>
          </div>

          <div className="topbar-right">
            <div className="topbar-badge-project">
              <span className="dot" />
              <span>Project 1 • Production</span>
            </div>
          </div>
        </header>

        {/* Main Page Area */}
        <main className="main-container">{children}</main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <NavigationShell>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/scores" element={<Scores />} />
          <Route path="/review-queue" element={<ReviewQueue />} />
          <Route path="/project-settings" element={<ProjectSettings />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/automation" element={<AutomationDashboard />} />
          <Route path="/ab-testing" element={<ABTesting />} />
          <Route path="/ambiguity" element={<AmbiguityInsights />} />
        </Routes>
      </NavigationShell>
    </Router>
  );
}

export default App;