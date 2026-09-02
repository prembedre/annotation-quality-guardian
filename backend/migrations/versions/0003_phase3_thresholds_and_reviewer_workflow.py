"""Add Phase 3 project thresholds, reviewer decisions tables, and performance indexes.

Revision ID: 0003_phase3_thresholds_and_reviewer_workflow
Revises: 0002_phase2_scoring
Create Date: 2026-09-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "0003_phase3_thresholds_and_reviewer_workflow"
down_revision: Union[str, None] = "0002_phase2_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ==========================================================
    # 1. Project Scoring Thresholds Table
    # ==========================================================

    op.create_table(
        "project_thresholds",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "gold_threshold",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.900000",
        ),
        sa.Column(
            "kappa_threshold",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.700000",
        ),
        sa.Column(
            "behavioral_threshold",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.750000",
        ),
        sa.Column(
            "embedding_threshold",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.800000",
        ),
        sa.Column(
            "trust_threshold",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.600000",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_project_thresholds_project_id"),
    )

    op.create_index(
        "ix_project_thresholds_id",
        "project_thresholds",
        ["id"],
    )

    op.create_index(
        "ix_project_thresholds_project_id",
        "project_thresholds",
        ["project_id"],
        unique=True,
    )

    # ==========================================================
    # 2. Reviewer Decisions Table
    # ==========================================================

    op.create_table(
        "reviewer_decisions",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "annotation_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "review_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "corrected_label",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "review_notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["annotation_id"],
            ["annotations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["annotators.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_reviewer_decisions_id",
        "reviewer_decisions",
        ["id"],
    )

    op.create_index(
        "idx_reviewer_decisions_project",
        "reviewer_decisions",
        ["project_id"],
    )

    op.create_index(
        "idx_reviewer_decisions_item",
        "reviewer_decisions",
        ["item_id"],
    )

    op.create_index(
        "idx_reviewer_decisions_reviewer",
        "reviewer_decisions",
        ["reviewed_by"],
    )

    op.create_index(
        "idx_reviewer_decisions_status",
        "reviewer_decisions",
        ["review_status"],
    )

    # ==========================================================
    # 3. Leaderboard & Heatmap Performance Indexes
    # ==========================================================

    # Leaderboard rolling accuracy queries by project, annotator, and created timestamp
    op.create_index(
        "idx_annotations_proj_annot_created",
        "annotations",
        ["project_id", "annotator_id", "created_at"],
    )

    # Heatmap queries by class/label per project
    op.create_index(
        "idx_annotations_proj_label",
        "annotations",
        ["project_id", "label"],
    )

    # Agreement heatmaps across annotators by item label
    op.create_index(
        "idx_annotations_item_label",
        "annotations",
        ["item_id", "label"],
    )

    # Fast filtering and sorting of trust scores per project
    op.create_index(
        "idx_trust_scores_proj_score",
        "trust_scores",
        ["project_id", "final_score"],
    )

    # Fast annotator quality score lookup for leaderboards (if quality_scores table exists)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "quality_scores" in inspector.get_table_names():
        op.create_index(
            "idx_quality_scores_annotator",
            "quality_scores",
            ["annotator_id", "metric"],
        )


def downgrade() -> None:

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "quality_scores" in inspector.get_table_names():
        try:
            op.drop_index("idx_quality_scores_annotator", table_name="quality_scores")
        except Exception:
            pass

    op.drop_index("idx_trust_scores_proj_score", table_name="trust_scores")
    op.drop_index("idx_annotations_item_label", table_name="annotations")
    op.drop_index("idx_annotations_proj_label", table_name="annotations")
    op.drop_index("idx_annotations_proj_annot_created", table_name="annotations")

    op.drop_index("idx_reviewer_decisions_status", table_name="reviewer_decisions")
    op.drop_index("idx_reviewer_decisions_reviewer", table_name="reviewer_decisions")
    op.drop_index("idx_reviewer_decisions_item", table_name="reviewer_decisions")
    op.drop_index("idx_reviewer_decisions_project", table_name="reviewer_decisions")
    op.drop_index("ix_reviewer_decisions_id", table_name="reviewer_decisions")
    op.drop_table("reviewer_decisions")

    op.drop_index("ix_project_thresholds_project_id", table_name="project_thresholds")
    op.drop_index("ix_project_thresholds_id", table_name="project_thresholds")
    op.drop_table("project_thresholds")
