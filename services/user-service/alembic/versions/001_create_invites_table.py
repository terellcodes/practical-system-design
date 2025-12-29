"""create invites table

Revision ID: 001_create_invites
Revises: 99f5f278dd9c
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_create_invites'
down_revision: Union[str, Sequence[str], None] = '99f5f278dd9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create invites table."""
    op.create_table(
        'invites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invitor_id', sa.Integer(), nullable=False),
        sa.Column('invitee_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invitor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invitee_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for efficient lookups
    op.create_index('ix_invites_invitor_id', 'invites', ['invitor_id'])
    op.create_index('ix_invites_invitee_id', 'invites', ['invitee_id'])
    op.create_index('ix_invites_status', 'invites', ['status'])


def downgrade() -> None:
    """Drop invites table."""
    op.drop_index('ix_invites_status', table_name='invites')
    op.drop_index('ix_invites_invitee_id', table_name='invites')
    op.drop_index('ix_invites_invitor_id', table_name='invites')
    op.drop_table('invites')

