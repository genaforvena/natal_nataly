"""Add user_profile column to users table

Revision ID: 0e8cfa50b49c
Revises: 
Create Date: 2026-02-12 17:49:57.782777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e8cfa50b49c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add user_profile column to users table."""
    # Add user_profile column as nullable Text
    op.add_column('users', sa.Column('user_profile', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema: Remove user_profile column from users table."""
    # Remove user_profile column
    op.drop_column('users', 'user_profile')
