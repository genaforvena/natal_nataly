"""add_analytics_events_table

Revision ID: 577f32ae469d
Revises: 0e8cfa50b49c
Create Date: 2026-02-13 09:58:26.384331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '577f32ae469d'
down_revision: Union[str, Sequence[str], None] = '0e8cfa50b49c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('telegram_id', sa.String(), nullable=False),
        sa.Column('event_name', sa.String(), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_events_telegram_id'), 'analytics_events', ['telegram_id'], unique=False)
    op.create_index(op.f('ix_analytics_events_event_name'), 'analytics_events', ['event_name'], unique=False)
    op.create_index(op.f('ix_analytics_events_created_at'), 'analytics_events', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_analytics_events_created_at'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_event_name'), table_name='analytics_events')
    op.drop_index(op.f('ix_analytics_events_telegram_id'), table_name='analytics_events')
    op.drop_table('analytics_events')
