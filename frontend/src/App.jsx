import React, { useState, useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  NavLink,
  useLocation,
  useNavigate,
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
  ChevronDown,
  Search,
  Bell,
  Sun,
  Moon,
  LogOut,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  Check,
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

import {
  ThemeProvider,
  useTheme,
  ToastProvider,
  useToast,
  CommandPalette,
  SystemHealthModal,
} from './components';

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

const PROJECTS_LIST = [
  { id: 1, name: 'Project 1 (Sentiment NLP)', env: 'Production', active: true },
  { id: 2, name: 'Project 2 (NER Clinical)', env: 'Staging', active: false },
  { id: 3, name: 'Project 3 (Vision Bounding)', env: 'Development', active: false },
];

function getBreadcrumb(pathname) {
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (item.end ? pathname === item.to : pathname.startsWith(item.to)) {
        return { group: group.title, page: item.label, path: item.to };
      }
    }
  }
  return { group: 'Overview', page: 'Dashboard', path: '/' };
}

function NavigationShell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);
  const [projectSearch, setProjectSearch] = useState('');
  const [activeProject, setActiveProject] = useState(PROJECTS_LIST[0]);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [healthModalOpen, setHealthModalOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { info } = useToast();
  const breadcrumb = getBreadcrumb(location.pathname);

  const closeMobile = () => setMobileOpen(false);

  // Global Keyboard Shortcuts (⌘K, etc.)
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const filteredProjects = PROJECTS_LIST.filter((p) =>
    p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
    p.env.toLowerCase().includes(projectSearch.toLowerCase())
  );

  return (
    <div className="app">
      {/* Command Palette ⌘K Dialog */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />

      {/* Guardian Engine System Health Diagnostics Modal */}
      <SystemHealthModal
        isOpen={healthModalOpen}
        onClose={() => setHealthModalOpen(false)}
      />

      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-backdrop"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-header">
          <NavLink to="/" className="brand-wrapper" onClick={closeMobile}>
            <div className="brand-icon-shield">
              <Shield size={18} />
            </div>
            {!collapsed && (
              <div className="brand-details">
                <div className="brand-title-row">
                  <span className="brand-name">AQG</span>
                  <span className="brand-pill">v1.2</span>
                </div>
                <span className="brand-tagline">Quality Guardian</span>
              </div>
            )}
          </NavLink>

          <button
            type="button"
            className="icon-action-btn"
            style={{ width: '26px', height: '26px', border: 'none' }}
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen size={15} /> : <PanelLeftClose size={15} />}
          </button>
        </div>

        {/* Project & Environment Switcher */}
        {!collapsed ? (
          <div className="sidebar-project-container">
            <button
              type="button"
              className="project-switcher-btn"
              onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
              aria-expanded={projectDropdownOpen}
            >
              <div className="project-switcher-active">
                <div className="project-avatar-badge">
                  {activeProject.id}
                </div>
                <div className="project-names-block">
                  <span className="project-title">{activeProject.name}</span>
                  <span className="project-env-tag">
                    <span className="pulsing-dot" style={{ width: '5px', height: '5px' }} />
                    {activeProject.env}
                  </span>
                </div>
              </div>
              <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
            </button>

            {projectDropdownOpen && (
              <div className="project-switcher-dropdown">
                <input
                  type="text"
                  placeholder="Filter projects..."
                  value={projectSearch}
                  onChange={(e) => setProjectSearch(e.target.value)}
                  className="project-search-input"
                  autoFocus
                />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {filteredProjects.map((proj) => (
                    <button
                      key={proj.id}
                      type="button"
                      className={`project-menu-item ${proj.id === activeProject.id ? 'active' : ''}`}
                      onClick={() => {
                        setActiveProject(proj);
                        setProjectDropdownOpen(false);
                        info(`Switched active context to ${proj.name}`);
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>{proj.name}</span>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                          ({proj.env})
                        </span>
                      </div>
                      {proj.id === activeProject.id && (
                        <Check size={13} style={{ color: 'var(--accent-brand)' }} />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ padding: '0.75rem 0', display: 'flex', justifyContent: 'center' }}>
            <div
              className="project-avatar-badge"
              title={`${activeProject.name} (${activeProject.env})`}
              style={{ cursor: 'pointer' }}
              onClick={() => setCollapsed(false)}
            >
              {activeProject.id}
            </div>
          </div>
        )}

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
                        title={collapsed ? item.label : undefined}
                      >
                        <Icon size={16} style={{ flexShrink: 0 }} />
                        <span>{item.label}</span>
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Guardian Engine Live Status Pill */}
        {!collapsed && (
          <div
            className="sidebar-engine-status"
            onClick={() => setHealthModalOpen(true)}
            title="Click to view engine health & telemetry"
          >
            <div className="engine-status-left">
              <div className="pulsing-dot" />
              <span className="engine-status-text">Guardian Engine</span>
            </div>
            <span className="engine-status-badge">ONLINE</span>
          </div>
        )}

        {/* User Avatar & Account Footer */}
        <div className="sidebar-footer">
          <button
            type="button"
            className="user-profile-btn"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
          >
            <div className="user-avatar">AG</div>
            {!collapsed && (
              <div className="user-info-text">
                <span className="user-name">Alex Guardian</span>
                <span className="user-role">Lead QA Engineer</span>
              </div>
            )}
          </button>

          {userMenuOpen && (
            <div className="user-dropdown-menu">
              <button
                type="button"
                className="user-menu-item"
                onClick={() => {
                  toggleTheme();
                  setUserMenuOpen(false);
                }}
              >
                {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                <span>{theme === 'dark' ? 'Light Theme' : 'Dark Theme'}</span>
              </button>
              <button
                type="button"
                className="user-menu-item"
                onClick={() => {
                  navigate('/project-settings');
                  setUserMenuOpen(false);
                }}
              >
                <Settings size={14} />
                <span>Account Settings</span>
              </button>
              <div style={{ height: '1px', background: 'var(--border-subtle)', margin: '3px 0' }} />
              <button
                type="button"
                className="user-menu-item"
                onClick={() => {
                  info('Session demo logged out');
                  setUserMenuOpen(false);
                }}
              >
                <LogOut size={14} />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Content Wrapper */}
      <div className={`content-wrapper ${collapsed ? 'collapsed' : ''}`}>
        {/* Sticky Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="icon-action-btn mobile-nav-toggle"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle navigation menu"
              style={{ display: 'none' }}
            >
              {mobileOpen ? <X size={18} /> : <Menu size={18} />}
            </button>

            {/* Breadcrumb Navigation with Hover State */}
            <nav className="breadcrumbs" aria-label="Breadcrumb">
              <span
                className="crumb-group"
                onClick={() => navigate(breadcrumb.path)}
              >
                {breadcrumb.group}
              </span>
              <ChevronRight size={13} className="crumb-separator" />
              <span className="crumb-active">{breadcrumb.page}</span>
            </nav>
          </div>

          <div className="topbar-right">
            {/* Global Command Palette Trigger Button (⌘K) */}
            <button
              type="button"
              className="command-palette-trigger"
              onClick={() => setCommandPaletteOpen(true)}
            >
              <Search size={14} />
              <span>Search or jump to...</span>
              <kbd className="kbd-shortcut">⌘K</kbd>
            </button>

            {/* Notifications Bell */}
            <div style={{ position: 'relative' }}>
              <button
                type="button"
                className="icon-action-btn"
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                aria-label="Notifications"
                title="Notifications"
              >
                <Bell size={16} />
                <span className="notification-badge-dot" />
              </button>

              {notificationsOpen && (
                <div className="notifications-popover">
                  <div className="notifications-header">
                    <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Notifications</span>
                    <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>3 New</span>
                  </div>
                  <div className="notifications-list">
                    <div className="notification-row">
                      <div className="pulsing-dot" style={{ marginTop: '4px' }} />
                      <div>
                        <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Rerouting Rule Triggered</div>
                        <div style={{ color: 'var(--text-muted)' }}>Low-trust batch #1042 reassigned to senior tier.</div>
                      </div>
                    </div>
                    <div className="notification-row">
                      <div className="pulsing-dot" style={{ background: 'var(--status-risk-solid)', marginTop: '4px' }} />
                      <div>
                        <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Ambiguity Spike Detected</div>
                        <div style={{ color: 'var(--text-muted)' }}>Neutral vs Positive overlap rate reached 23.4%.</div>
                      </div>
                    </div>
                    <div className="notification-row">
                      <div className="pulsing-dot" style={{ background: 'var(--status-good-solid)', marginTop: '4px' }} />
                      <div>
                        <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Scores Synchronized</div>
                        <div style={{ color: 'var(--text-muted)' }}>Latest Cohen's Kappa computed for 50 items.</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Direct Theme Toggle */}
            <button
              type="button"
              className="icon-action-btn"
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
              aria-label="Toggle dark/light theme"
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>

            {/* Active Project Environment Status Chip */}
            <div className="topbar-status-chip">
              <div className="pulsing-dot" style={{ width: '6px', height: '6px' }} />
              <span className="font-mono">{activeProject.name} • {activeProject.env}</span>
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
    <ThemeProvider>
      <ToastProvider>
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
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;