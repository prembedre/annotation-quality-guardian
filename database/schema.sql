-- ============================================================
-- Annotation Quality Guardian — Database Schema
-- PostgreSQL 15+
-- ============================================================

-- ── Projects ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id            SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL UNIQUE,
    description   TEXT,
    label_set     JSONB NOT NULL DEFAULT '[]',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ
);

-- ── Annotators ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS annotators (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    email         VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Items (data points to be annotated) ──────────────────────
CREATE TABLE IF NOT EXISTS items (
    id            SERIAL PRIMARY KEY,
    project_id    INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    external_id   VARCHAR(255) NOT NULL,
    content       JSONB NOT NULL DEFAULT '{}',
    is_gold       BOOLEAN NOT NULL DEFAULT FALSE,
    gold_label    VARCHAR(255),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, external_id)
);

-- ── Annotations ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS annotations (
    id            SERIAL PRIMARY KEY,
    project_id    INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_id       INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    annotator_id  INT NOT NULL REFERENCES annotators(id) ON DELETE CASCADE,
    label         VARCHAR(255) NOT NULL,
    confidence    NUMERIC(4,3) CHECK (confidence >= 0 AND confidence <= 1),
    duration_ms   INT,
    metadata      JSONB NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ,
    UNIQUE (item_id, annotator_id)
);

-- ── Quality Scores (computed results) ────────────────────────
CREATE TABLE IF NOT EXISTS quality_scores (
    id            SERIAL PRIMARY KEY,
    project_id    INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    annotator_id  INT REFERENCES annotators(id) ON DELETE SET NULL,
    metric        VARCHAR(100) NOT NULL,   -- e.g. 'gold_accuracy', 'cohens_kappa'
    value         NUMERIC(10,6),
    details       JSONB NOT NULL DEFAULT '{}',
    computed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────
CREATE INDEX idx_annotations_project   ON annotations (project_id);
CREATE INDEX idx_annotations_annotator ON annotations (annotator_id);
CREATE INDEX idx_annotations_item      ON annotations (item_id);
CREATE INDEX idx_items_project         ON items (project_id);
CREATE INDEX idx_items_gold            ON items (project_id, is_gold) WHERE is_gold = TRUE;
CREATE INDEX idx_quality_scores_project ON quality_scores (project_id);
