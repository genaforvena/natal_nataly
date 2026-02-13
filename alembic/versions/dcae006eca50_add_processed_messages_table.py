"""Add processed_messages table for persistent duplicate detection

Revision ID: dcae006eca50
Revises: 0e8cfa50b49c
Create Date: 2026-02-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcae006eca50'
down_revision: Union[str, Sequence[str], None] = '0e8cfa50b49c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add processed_messages table for persistent duplicate detection."""
    op.create_table(
        'processed_messages',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('telegram_id', sa.String(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for fast lookups
    op.create_index(
        'ix_processed_messages_telegram_id',
        'processed_messages',
        ['telegram_id']
    )
    op.create_index(
        'ix_processed_messages_message_id',
        'processed_messages',
        ['message_id']
    )
    op.create_index(
        'ix_processed_messages_processed_at',
        'processed_messages',
        ['processed_at']
    )
    
    # Create composite index for duplicate detection query
    op.create_index(
        'ix_processed_messages_telegram_message',
        'processed_messages',
        ['telegram_id', 'message_id'],
        unique=False  # Not unique because we track history, but practically will be unique for recent messages
    )


def downgrade() -> None:
    """Downgrade schema: Remove processed_messages table."""
    op.drop_index('ix_processed_messages_telegram_message', table_name='processed_messages')
    op.drop_index('ix_processed_messages_processed_at', table_name='processed_messages')
    op.drop_index('ix_processed_messages_message_id', table_name='processed_messages')
    op.drop_index('ix_processed_messages_telegram_id', table_name='processed_messages')
    op.drop_table('processed_messages')
