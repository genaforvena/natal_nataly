"""Add message_text to processed_messages table

Revision ID: 20260214155358
Revises: 20260214152432
Create Date: 2026-02-14 15:53:58.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260214155358'
down_revision: Union[str, Sequence[str], None] = '20260214152432'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add message_text column to processed_messages table."""
    # Add message_text column (nullable, for storing message content)
    op.add_column(
        'processed_messages',
        sa.Column('message_text', sa.Text(), nullable=True)
    )
    
    # Data migration: Mark all existing pending messages (without text) as replied
    # This prevents old messages from blocking new messages after the migration
    # Old messages can't be combined since they have no text stored
    op.execute("""
        UPDATE processed_messages 
        SET reply_sent = TRUE, 
            reply_sent_at = CURRENT_TIMESTAMP 
        WHERE reply_sent = FALSE 
        AND message_text IS NULL
    """)


def downgrade() -> None:
    """Downgrade schema: Remove message_text column."""
    op.drop_column('processed_messages', 'message_text')
