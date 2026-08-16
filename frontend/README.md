# 🖥️ Frontend — Annotation Quality Guardian

## Overview

React-based dashboard for visualizing annotation quality metrics, managing projects, and monitoring annotator performance.

## Tech Stack

- **React 18** — UI framework
- **Vite 5** — Build tool & dev server
- **React Router 6** — Client-side routing
- **Axios** — HTTP client

## Setup

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` and proxies `/api` requests to the FastAPI backend at `http://localhost:8000`.

## Directory Structure

```
src/
├── main.jsx          # Entry point
├── App.jsx           # Root component with routing
├── index.css         # Global styles & design tokens
├── pages/            # Page-level components
│   ├── Dashboard.jsx
│   ├── Projects.jsx
│   └── Scores.jsx
├── components/       # Reusable UI components
└── services/
    └── api.js        # Centralized API calls
```

## Available Scripts

| Command           | Description                    |
|-------------------|--------------------------------|
| `npm run dev`     | Start development server       |
| `npm run build`   | Build for production            |
| `npm run preview` | Preview production build        |
| `npm run lint`    | Run ESLint                      |
