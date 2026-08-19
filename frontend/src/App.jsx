import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Scores from './pages/Scores';
import ReviewQueue from './pages/ReviewQueue';

function App() {
  return (
    <Router>
      <div className="app">
        <nav className="sidebar">
          <h1 className="logo">🛡️ AQG</h1>
          <ul>
            <li><NavLink to="/" end>Dashboard</NavLink></li>
            <li><NavLink to="/projects">Projects</NavLink></li>
            <li><NavLink to="/scores">Scores</NavLink></li>
            <li><NavLink to="/review-queue">Review Queue</NavLink></li>
          </ul>
        </nav>
        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/scores" element={<Scores />} />
            <Route path="/review-queue" element={<ReviewQueue />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
