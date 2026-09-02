-- ============================================================
-- Annotation Quality Guardian — Sample Data
-- Run after schema.sql
-- ============================================================

-- ── Projects ─────────────────────────────────────────────────
INSERT INTO projects (name, description, label_set) VALUES
    ('Sentiment Analysis', 'Classify customer reviews as positive, negative, or neutral.', '["positive", "negative", "neutral"]'),
    ('Named Entity Recognition', 'Tag named entities in news articles.', '["PER", "ORG", "LOC", "MISC"]');

-- ── Annotators ───────────────────────────────────────────────
INSERT INTO annotators (username, email) VALUES
    ('alice',   'alice@example.com'),
    ('bob',     'bob@example.com'),
    ('charlie', 'charlie@example.com'),
    ('david',   'david@example.com'),
    ('eva',     'eva@example.com');


-- ── Items (including gold-standard items) ────────────────────
INSERT INTO items (project_id, external_id, content, is_gold, gold_label) VALUES
    (1, 'rev-001', '{"text": "Absolutely love this product!"}',            TRUE,  'positive'),
    (1, 'rev-002', '{"text": "Terrible experience, would not recommend."}', TRUE,  'negative'),
    (1, 'rev-003', '{"text": "It was okay, nothing special."}',            TRUE,  'neutral'),
    (1, 'rev-004', '{"text": "Best purchase I have ever made."}',          FALSE, NULL),
    (1, 'rev-005', '{"text": "Not worth the money."}',                     FALSE, NULL),
    (1, 'rev-006', '{"text": "Decent quality for the price."}',            FALSE, NULL);

-- ── Annotations ──────────────────────────────────────────────
-- Alice annotations
INSERT INTO annotations (project_id, item_id, annotator_id, label, confidence, duration_ms) VALUES
    (1, 1, 1, 'positive', 0.95, 3200),
    (1, 2, 1, 'negative', 0.90, 2800),
    (1, 3, 1, 'neutral',  0.85, 4100),
    (1, 4, 1, 'positive', 0.92, 3500),
    (1, 5, 1, 'negative', 0.88, 3000),
    (1, 6, 1, 'neutral',  0.70, 4500);

-- Bob annotations
INSERT INTO annotations (project_id, item_id, annotator_id, label, confidence, duration_ms) VALUES
    (1, 1, 2, 'positive', 0.90, 3800),
    (1, 2, 2, 'negative', 0.85, 3200),
    (1, 3, 2, 'positive', 0.60, 5200),   -- disagreement with gold
    (1, 4, 2, 'positive', 0.88, 3600),
    (1, 5, 2, 'neutral',  0.55, 4800),   -- disagreement with Alice
    (1, 6, 2, 'neutral',  0.75, 4000);

-- Charlie annotations
INSERT INTO annotations (project_id, item_id, annotator_id, label, confidence, duration_ms) VALUES
    (1, 1, 3, 'positive', 0.92, 3100),
    (1, 2, 3, 'negative', 0.88, 2900),
    (1, 3, 3, 'neutral',  0.80, 4300),
    (1, 4, 3, 'positive', 0.91, 3300),
    (1, 5, 3, 'negative', 0.82, 3400),
    (1, 6, 3, 'positive', 0.65, 5100);   -- disagreement with Alice & Bob

-- ============================================================
-- Phase 2 Sample Data
-- ============================================================

-- Behavioral scores
INSERT INTO behavioral_scores (
    project_id,
    annotator_id,
    item_id,
    time_score,
    streak_score,
    anomaly_score,
    details
) VALUES
    (
        1, 1, 4,
        0.90,
        0.85,
        0.10,
        '{"reason": "Normal annotation behavior"}'
    ),
    (
        1, 2, 5,
        0.45,
        0.35,
        0.72,
        '{"reason": "Unusual timing and disagreement streak"}'
    );

-- Embedding results
INSERT INTO embedding_results (
    project_id,
    item_id,
    model_name,
    embedding,
    outlier_score,
    is_outlier,
    nearest_item_id,
    details
) VALUES
    (
        1,
        4,
        'sentence-transformers',
        '[0.12, 0.45, 0.78]',
        0.18,
        FALSE,
        1,
        '{"method": "cosine_similarity"}'
    ),
    (
        1,
        5,
        'sentence-transformers',
        '[0.91, 0.05, 0.12]',
        0.87,
        TRUE,
        2,
        '{"method": "cosine_similarity"}'
    );

-- Final trust scores
INSERT INTO trust_scores (
    project_id,
    item_id,
    gold_score,
    agreement_score,
    behavioral_score,
    embedding_score,
    final_score,
    flagged,
    breakdown
) VALUES
    (
        1,
        4,
        0.95,
        0.90,
        0.90,
        0.82,
        0.89,
        FALSE,
        '{
            "gold": 0.95,
            "agreement": 0.90,
            "behavioral": 0.90,
            "embedding": 0.82
        }'
    ),
    (
        1,
        5,
        0.60,
        0.45,
        0.45,
        0.13,
        0.41,
        TRUE,
        '{
            "gold": 0.60,
            "agreement": 0.45,
            "behavioral": 0.45,
            "embedding": 0.13
        }'
    );

-- ============================================================
-- Phase 3 Sample Data
-- ============================================================

-- Additional annotations for David (annotator 4) and Eva (annotator 5)
INSERT INTO annotations (project_id, item_id, annotator_id, label, confidence, duration_ms) VALUES
    (1, 1, 4, 'positive', 0.94, 3000),
    (1, 2, 4, 'negative', 0.89, 2700),
    (1, 3, 4, 'neutral',  0.82, 4000),
    (1, 4, 4, 'positive', 0.90, 3200),
    (1, 5, 4, 'negative', 0.86, 3100),
    (1, 6, 4, 'neutral',  0.72, 4200),
    (1, 1, 5, 'positive', 0.91, 3300),
    (1, 2, 5, 'negative', 0.87, 2950),
    (1, 3, 5, 'negative', 0.50, 6000),  -- disagreement
    (1, 4, 5, 'positive', 0.89, 3400),
    (1, 5, 5, 'positive', 0.40, 5800),  -- disagreement
    (1, 6, 5, 'neutral',  0.78, 3900);

-- Project Scoring Threshold Configurations
INSERT INTO project_thresholds (
    project_id,
    gold_threshold,
    kappa_threshold,
    behavioral_threshold,
    embedding_threshold,
    trust_threshold
) VALUES
    (1, 0.90, 0.70, 0.75, 0.80, 0.60),
    (2, 0.85, 0.65, 0.70, 0.75, 0.55);

-- Reviewer Decisions
INSERT INTO reviewer_decisions (
    project_id,
    item_id,
    annotation_id,
    review_status,
    reviewed_by,
    corrected_label,
    review_notes
) VALUES
    (
        1, 4, NULL,
        'CONFIRM',
        1,
        'positive',
        'Confirmed majority label as gold label.'
    ),
    (
        1, 5, NULL,
        'CORRECT',
        1,
        'negative',
        'Corrected ambiguous label to negative based on reviewer inspection.'
    ),
    (
        1, 6, NULL,
        'ESCALATE',
        3,
        NULL,
        'Escalated to lead annotator due to split vote across annotators.'
    );

