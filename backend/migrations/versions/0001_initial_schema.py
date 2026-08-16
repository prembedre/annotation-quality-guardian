"""Initial schema creation for AQG core entities

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-16 20:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create items table ──
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False, server_default="default"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_items_id"), "items", ["id"], unique=False)
    op.create_index(op.f("ix_items_source"), "items", ["source"], unique=False)

    # ── 2. Create annotators table ──
    op.create_table(
        "annotators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_annotators_id"), "annotators", ["id"], unique=False)
    op.create_index(op.f("ix_annotators_name"), "annotators", ["name"], unique=False)
    op.create_index(op.f("ix_annotators_email"), "annotators", ["email"], unique=True)

    # ── 3. Create annotations table ──
    op.create_table(
        "annotations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("annotator_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["annotator_id"], ["annotators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_annotations_id"), "annotations", ["id"], unique=False)
    op.create_index(op.f("ix_annotations_item_id"), "annotations", ["item_id"], unique=False)
    op.create_index(op.f("ix_annotations_annotator_id"), "annotations", ["annotator_id"], unique=False)
    op.create_index(op.f("ix_annotations_label"), "annotations", ["label"], unique=False)
    op.create_index(op.f("ix_annotations_timestamp"), "annotations", ["timestamp"], unique=False)
    op.create_index("ix_item_annotator", "annotations", ["item_id", "annotator_id"], unique=True)

    # ── 4. Create trust_scores table ──
    op.create_table(
        "trust_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trust_scores_id"), "trust_scores", ["id"], unique=False)
    op.create_index(op.f("ix_trust_scores_item_id"), "trust_scores", ["item_id"], unique=False)
    op.create_index(op.f("ix_trust_scores_flagged"), "trust_scores", ["flagged"], unique=False)


def downgrade() -> None:
    op.drop_table("trust_scores")
    op.drop_table("annotations")
    op.drop_table("annotators")
    op.drop_table("items")
