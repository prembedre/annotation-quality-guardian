"""Add automation_rules table for persistent rule toggles.

Revision ID: 0008_add_automation_rules_table
Revises: 0007_add_project_archived
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0008_add_automation_rules_table"
down_revision: Union[str, None] = "0007_add_project_archived"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "automation_rules" not in inspector.get_table_names():
        op.create_table(
            "automation_rules",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "project_id",
                sa.Integer(),
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("rule_id", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("condition", sa.String(length=255), nullable=False),
            sa.Column("action", sa.String(length=255), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("project_id", "rule_id", name="uq_project_rule"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "automation_rules" in inspector.get_table_names():
        op.drop_table("automation_rules")
