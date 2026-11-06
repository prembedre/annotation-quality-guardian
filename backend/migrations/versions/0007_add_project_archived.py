"""Add is_archived column to projects table

Revision ID: 0007_add_project_archived
Revises: 0006_add_users_table
Create Date: 2026-09-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0007_add_project_archived"
down_revision: Union[str, None] = "0006_add_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("projects")]
        if "is_archived" not in columns:
            with op.batch_alter_table("projects", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "is_archived",
                        sa.Boolean(),
                        nullable=False,
                        server_default=sa.text("0"),
                    )
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "projects" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("projects")]
        if "is_archived" in columns:
            with op.batch_alter_table("projects", schema=None) as batch_op:
                batch_op.drop_column("is_archived")
