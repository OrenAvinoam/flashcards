"""initial deck schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS deck")
    op.create_table(
        "decks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="deck",
    )
    op.create_index("ix_deck_decks_user_id", "decks", ["user_id"], schema="deck")

    op.create_table(
        "cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "deck_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("deck.decks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("front", sa.String(2000), nullable=False),
        sa.Column("back", sa.String(2000), nullable=False),
        sa.Column("fsrs_state", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="deck",
    )
    op.create_index("ix_deck_cards_deck_id", "cards", ["deck_id"], schema="deck")


def downgrade() -> None:
    op.drop_index("ix_deck_cards_deck_id", table_name="cards", schema="deck")
    op.drop_table("cards", schema="deck")
    op.drop_index("ix_deck_decks_user_id", table_name="decks", schema="deck")
    op.drop_table("decks", schema="deck")
