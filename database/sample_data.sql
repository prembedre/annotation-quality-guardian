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
    ('charlie', 'charlie@example.com');

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
