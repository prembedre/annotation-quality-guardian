"""Add Phase 2 scoring tables and indexes.

Revision ID: 0002_phase2_scoring
Revises: 0001_initial_schema
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_phase2_scoring"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 0. Ensure projects table exists ───────────────────────
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "projects" not in inspector.get_table_names():
        op.create_table(
            "projects",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("label_set", sa.JSON(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_projects_id",
            "projects",
            ["id"],
            unique=False,
        )

    # ── 1. Behavioral scoring results ─────────────────────────
    op.create_table(
        "behavioral_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("annotator_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("time_score", sa.Numeric(10, 6), nullable=True),
        sa.Column("streak_score", sa.Numeric(10, 6), nullable=True),
        sa.Column("anomaly_score", sa.Numeric(10, 6), nullable=True),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["annotator_id"],
            ["annotators.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_behavioral_scores_project",
        "behavioral_scores",
        ["project_id"],
    )
    op.create_index(
        "idx_behavioral_scores_annotator",
        "behavioral_scores",
        ["annotator_id"],
    )
    op.create_index(
        "idx_behavioral_scores_item",
        "behavioral_scores",
        ["item_id"],
    )

    # ── 2. Embedding results ──────────────────────────────────
    op.create_table(
        "embedding_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.Column("outlier_score", sa.Numeric(10, 6), nullable=True),
        sa.Column(
            "is_outlier",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("nearest_item_id", sa.Integer(), nullable=True),
        sa.Column(
            "details",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(),
            nullable=False,
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
            ["nearest_item_id"],
            ["items.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_embedding_results_project",
        "embedding_results",
        ["project_id"],
    )
    op.create_index(
        "idx_embedding_results_item",
        "embedding_results",
        ["item_id"],
    )

    # ── 3. Extend existing Phase 1 trust_scores table ─────────
    op.add_column(
        "trust_scores",
        sa.Column("project_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "trust_scores",
        sa.Column("gold_score", sa.Numeric(10, 6), nullable=True),
    )
    op.add_column(
        "trust_scores",
        sa.Column("agreement_score", sa.Numeric(10, 6), nullable=True),
    )
    op.add_column(
        "trust_scores",
        sa.Column("behavioral_score", sa.Numeric(10, 6), nullable=True),
    )
    op.add_column(
        "trust_scores",
        sa.Column("embedding_score", sa.Numeric(10, 6), nullable=True),
    )

    op.create_index(
        "idx_trust_scores_project",
        "trust_scores",
        ["project_id"],
    )

    # ── 4. Phase 2 trust-score indexes ─────────────────────────
    op.create_index(
        "idx_trust_scores_flagged_project",
        "trust_scores",
        ["project_id", "flagged"],
    )


def downgrade() -> None:
    # Remove Phase 2 trust-score additions.
    op.drop_index(
        "idx_trust_scores_flagged_project",
        table_name="trust_scores",
    )
    op.drop_index(
        "idx_trust_scores_project",
        table_name="trust_scores",
    )

    op.drop_column("trust_scores", "embedding_score")
    op.drop_column("trust_scores", "behavioral_score")
    op.drop_column("trust_scores", "agreement_score")
    op.drop_column("trust_scores", "gold_score")
    op.drop_column("trust_scores", "project_id")

    # Remove Phase 2 tables.
    op.drop_index(
        "idx_embedding_results_item",
        table_name="embedding_results",
    )
    op.drop_index(
        "idx_embedding_results_project",
        table_name="embedding_results",
    )
    op.drop_table("embedding_results")

    op.drop_index(
        "idx_behavioral_scores_item",
        table_name="behavioral_scores",
    )
    op.drop_index(
        "idx_behavioral_scores_annotator",
        table_name="behavioral_scores",
    )
    op.drop_index(
        "idx_behavioral_scores_project",
        table_name="behavioral_scores",
    )
    op.drop_table("behavioral_scores")
