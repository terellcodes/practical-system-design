"""create contacts table

Revision ID: 002_create_contacts
Revises: 001_create_invites
Create Date: 2025-12-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_create_contacts'
down_revision: Union[str, Sequence[str], None] = '001_create_invites'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create contacts table with unidirectional design."""
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contact_one_id', sa.Integer(), nullable=False),
        sa.Column('contact_two_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contact_one_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_two_id'], ['users.id'], ondelete='CASCADE'),
        # Unique constraint ensures one row per contact pair
        sa.UniqueConstraint('contact_one_id', 'contact_two_id', name='uq_contacts_pair'),
    )
    
    # Create indexes for efficient lookups in both directions
    op.create_index('ix_contacts_contact_one_id', 'contacts', ['contact_one_id'])
    op.create_index('ix_contacts_contact_two_id', 'contacts', ['contact_two_id'])


def downgrade() -> None:
    """Drop contacts table."""
    op.drop_index('ix_contacts_contact_two_id', table_name='contacts')
    op.drop_index('ix_contacts_contact_one_id', table_name='contacts')
    op.drop_table('contacts')



