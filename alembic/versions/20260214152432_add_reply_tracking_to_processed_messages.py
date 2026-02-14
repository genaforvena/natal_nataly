"""Add reply tracking to processed_messages table

Revision ID: 20260214152432
Revises: dcae006eca50
Create Date: 2026-02-14 15:24:32.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260214152432'
down_revision: Union[str, Sequence[str], None] = 'dcae006eca50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add reply_sent and reply_sent_at columns to processed_messages table."""
    # Add reply_sent column (default False for existing rows)
    op.add_column(
        'processed_messages',
        sa.Column('reply_sent', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    
    # Add reply_sent_at column (nullable, as not all messages have replies yet)
    op.add_column(
        'processed_messages',
        sa.Column('reply_sent_at', sa.DateTime(), nullable=True)
    )
    
    # Create index on reply_sent for efficient queries
    op.create_index(
        'ix_processed_messages_reply_sent',
        'processed_messages',
        ['reply_sent']
    )


def downgrade() -> None:
    """Downgrade schema: Remove reply_sent and reply_sent_at columns."""
    op.drop_index('ix_processed_messages_reply_sent', table_name='processed_messages')
    op.drop_column('processed_messages', 'reply_sent_at')
    op.drop_column('processed_messages', 'reply_sent')
