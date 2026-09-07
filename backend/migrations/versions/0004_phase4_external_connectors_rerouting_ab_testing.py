"""Add Phase 4 external database connectors, reroute histories, and A/B test experiments.

Revision ID: 0004_phase4_external_connectors_rerouting_ab_testing
Revises: 0003_phase3_thresholds_and_reviewer_workflow
Create Date: 2026-09-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "0004_phase4_external_connectors_rerouting_ab_testing"
down_revision: Union[str, None] = "0003_phase3_thresholds_and_reviewer_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ==========================================================
    # 1. External DB Connectors Table (Read-Only Integration)
    # ==========================================================

    op.create_table(
        "external_db_connectors",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "connection_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "database_type",
            sa.String(length=50),
            nullable=False,
            server_default="postgresql",
        ),
        sa.Column(
            "host",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "port",
            sa.Integer(),
            nullable=True,
            server_default="5432",
        ),
        sa.Column(
            "database_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "username",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "password_encrypted",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "read_only",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "query_config",
            sa.JSON(),
            nullable=False,
            server_default="{}",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("connection_name", name="uq_external_db_connectors_connection_name"),
    )

    op.create_index(
        "ix_external_db_connectors_id",
        "external_db_connectors",
        ["id"],
    )

    op.create_index(
        "ix_external_db_connectors_name",
        "external_db_connectors",
        ["connection_name"],
        unique=True,
    )

    op.create_index(
        "idx_external_db_connectors_status",
        "external_db_connectors",
        ["status"],
    )

    # ==========================================================
    # 2. Reroute Histories Table (Automatic Task Rerouting)
    # ==========================================================

    op.create_table(
        "reroute_histories",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "original_annotator_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "reassigned_annotator_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "reason",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "trust_score_snapshot",
            sa.Numeric(10, 6),
            nullable=True,
        ),
        sa.Column(
            "reroute_status",
            sa.String(length=50),
            nullable=False,
            server_default="PENDING",
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
            ["item_id"],
            ["items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["original_annotator_id"],
            ["annotators.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reassigned_annotator_id"],
            ["annotators.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_reroute_histories_id",
        "reroute_histories",
        ["id"],
    )

    op.create_index(
        "idx_reroute_histories_item",
        "reroute_histories",
        ["item_id"],
    )

    op.create_index(
        "idx_reroute_histories_project_status",
        "reroute_histories",
        ["project_id", "reroute_status"],
    )

    op.create_index(
        "idx_reroute_histories_original_annotator",
        "reroute_histories",
        ["original_annotator_id"],
    )

    op.create_index(
        "idx_reroute_histories_reassigned_annotator",
        "reroute_histories",
        ["reassigned_annotator_id"],
    )

    # ==========================================================
    # 3. A/B Testing Experiments Table
    # ==========================================================

    op.create_table(
        "ab_test_experiments",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "experiment_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "schema_version_a",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "schema_version_b",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "annotator_group",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "assigned_version",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ab_test_experiments_id",
        "ab_test_experiments",
        ["id"],
    )

    op.create_index(
        "idx_ab_test_experiments_project_status",
        "ab_test_experiments",
        ["project_id", "status"],
    )


def downgrade() -> None:

    op.drop_index("idx_ab_test_experiments_project_status", table_name="ab_test_experiments")
    op.drop_index("ix_ab_test_experiments_id", table_name="ab_test_experiments")
    op.drop_table("ab_test_experiments")

    op.drop_index("idx_reroute_histories_reassigned_annotator", table_name="reroute_histories")
    op.drop_index("idx_reroute_histories_original_annotator", table_name="reroute_histories")
    op.drop_index("idx_reroute_histories_project_status", table_name="reroute_histories")
    op.drop_index("idx_reroute_histories_item", table_name="reroute_histories")
    op.drop_index("ix_reroute_histories_id", table_name="reroute_histories")
    op.drop_table("reroute_histories")

    op.drop_index("idx_external_db_connectors_status", table_name="external_db_connectors")
    op.drop_index("ix_external_db_connectors_name", table_name="external_db_connectors")
    op.drop_index("ix_external_db_connectors_id", table_name="external_db_connectors")
    op.drop_table("external_db_connectors")
