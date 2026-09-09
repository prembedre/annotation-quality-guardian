"""Add persistent Phase 4 automation setting to projects.

Revision ID: 0005_project_automation_enabled
Revises: 0004_phase4_external_connectors_rerouting_ab_testing
Create Date: 2026-09-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "0005_project_automation_enabled"
down_revision: Union[str, None] = (
    "0004_phase4_external_connectors_rerouting_ab_testing"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the persistent automation_enabled setting."""

    op.add_column(
        "projects",
        sa.Column(
            "automation_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
    )


def downgrade() -> None:
    """Remove the persistent automation_enabled setting."""

    op.drop_column(
        "projects",
        "automation_enabled",
    )