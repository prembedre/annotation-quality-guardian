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

-- ============================================================
-- Phase 2 Tables
-- ============================================================

-- Behavioral scoring results
CREATE TABLE IF NOT EXISTS behavioral_scores (
    id              SERIAL PRIMARY KEY,
    project_id      INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    annotator_id    INT NOT NULL REFERENCES annotators(id) ON DELETE CASCADE,
    item_id         INT REFERENCES items(id) ON DELETE CASCADE,

    time_score      NUMERIC(10,6),
    streak_score    NUMERIC(10,6),
    anomaly_score   NUMERIC(10,6),

    details         JSONB NOT NULL DEFAULT '{}',
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Embedding results
CREATE TABLE IF NOT EXISTS embedding_results (
    id                SERIAL PRIMARY KEY,
    project_id        INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_id           INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,

    model_name        VARCHAR(255) NOT NULL,
    embedding         JSONB,
    outlier_score     NUMERIC(10,6),
    is_outlier        BOOLEAN NOT NULL DEFAULT FALSE,
    nearest_item_id   INT REFERENCES items(id) ON DELETE SET NULL,

    details           JSONB NOT NULL DEFAULT '{}',
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Final trust scores
CREATE TABLE IF NOT EXISTS trust_scores (
    id                SERIAL PRIMARY KEY,
    project_id        INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_id           INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,

    gold_score        NUMERIC(10,6),
    agreement_score   NUMERIC(10,6),
    behavioral_score  NUMERIC(10,6),
    embedding_score   NUMERIC(10,6),

    final_score       NUMERIC(10,6) NOT NULL,
    flagged           BOOLEAN NOT NULL DEFAULT FALSE,

    breakdown         JSONB NOT NULL DEFAULT '{}',

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ
);

-- Phase 2 indexes
CREATE INDEX idx_behavioral_scores_project
    ON behavioral_scores (project_id);

CREATE INDEX idx_behavioral_scores_annotator
    ON behavioral_scores (annotator_id);

CREATE INDEX idx_behavioral_scores_item
    ON behavioral_scores (item_id);

CREATE INDEX idx_embedding_results_project
    ON embedding_results (project_id);

CREATE INDEX idx_embedding_results_item
    ON embedding_results (item_id);

CREATE INDEX idx_embedding_results_outlier
    ON embedding_results (project_id, is_outlier)
    WHERE is_outlier = TRUE;

CREATE INDEX idx_trust_scores_project
    ON trust_scores (project_id);

CREATE INDEX idx_trust_scores_item
    ON trust_scores (item_id);

CREATE INDEX idx_trust_scores_flagged
    ON trust_scores (project_id, flagged)
    WHERE flagged = TRUE;

-- ============================================================
-- Phase 3 Tables
-- ============================================================

-- Project-wise configurable scoring thresholds
CREATE TABLE IF NOT EXISTS project_thresholds (
    id                   SERIAL PRIMARY KEY,
    project_id           INT NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    gold_threshold       NUMERIC(10,6) NOT NULL DEFAULT 0.900000,
    kappa_threshold      NUMERIC(10,6) NOT NULL DEFAULT 0.700000,
    behavioral_threshold NUMERIC(10,6) NOT NULL DEFAULT 0.750000,
    embedding_threshold  NUMERIC(10,6) NOT NULL DEFAULT 0.800000,
    trust_threshold      NUMERIC(10,6) NOT NULL DEFAULT 0.600000,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Reviewer resolve workflow decisions
CREATE TABLE IF NOT EXISTS reviewer_decisions (
    id               SERIAL PRIMARY KEY,
    project_id       INT REFERENCES projects(id) ON DELETE CASCADE,
    item_id          INT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    annotation_id    INT REFERENCES annotations(id) ON DELETE SET NULL,
    review_status    VARCHAR(50) NOT NULL, -- 'CONFIRM', 'CORRECT', 'ESCALATE'
    reviewed_by      INT REFERENCES annotators(id) ON DELETE SET NULL,
    reviewed_at      TIMESTAMPTZ DEFAULT NOW(),
    corrected_label  VARCHAR(255),
    review_notes     TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Phase 3 performance indexes for leaderboards, agreement heatmaps, and dashboard analytics
CREATE INDEX idx_annotations_proj_annot_created
    ON annotations (project_id, annotator_id, created_at);

CREATE INDEX idx_annotations_proj_label
    ON annotations (project_id, label);

CREATE INDEX idx_annotations_item_label
    ON annotations (item_id, label);

CREATE INDEX idx_trust_scores_proj_score
    ON trust_scores (project_id, final_score);

CREATE INDEX idx_quality_scores_annotator
    ON quality_scores (annotator_id, metric);

CREATE INDEX idx_reviewer_decisions_project
    ON reviewer_decisions (project_id);

CREATE INDEX idx_reviewer_decisions_item
    ON reviewer_decisions (item_id);

CREATE INDEX idx_reviewer_decisions_reviewer
    ON reviewer_decisions (reviewed_by);

CREATE INDEX idx_reviewer_decisions_status
    ON reviewer_decisions (review_status);

