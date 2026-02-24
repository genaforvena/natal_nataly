"""Add refactored architecture columns

Revision ID: 20260224000001
Revises: 20260214155358
Create Date: 2026-02-24 00:00:01.000000

Adds columns required by the simplified runtime architecture:
- users.last_update_id        – last processed Telegram update_id (dedup)
- users.conversation_session_json – conversation context (replaces ConversationThread rows)
- processed_messages.role     – "user" or "assistant" for analytics
- processed_messages.latency_ms – processing latency in ms for analytics
- astro_profiles.chart_hash   – chart hash for quick comparison
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260224000001'
down_revision: Union[str, Sequence[str], None] = '20260214155358'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns for simplified architecture."""

    # users table
    op.add_column('users', sa.Column('last_update_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('conversation_session_json', sa.Text(), nullable=True))

    # processed_messages table – analytics fields
    op.add_column('processed_messages', sa.Column('role', sa.String(), nullable=True))
    op.add_column('processed_messages', sa.Column('latency_ms', sa.Integer(), nullable=True))

    # astro_profiles table
    op.add_column('astro_profiles', sa.Column('chart_hash', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove new columns."""

    op.drop_column('astro_profiles', 'chart_hash')
    op.drop_column('processed_messages', 'latency_ms')
    op.drop_column('processed_messages', 'role')
    op.drop_column('users', 'conversation_session_json')
    op.drop_column('users', 'last_update_id')
