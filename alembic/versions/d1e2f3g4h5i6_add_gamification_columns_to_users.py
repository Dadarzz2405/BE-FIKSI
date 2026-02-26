"""add gamification columns to users

Revision ID: d1e2f3g4h5i6
Revises: c3d4e5f6a7b8
Create Date: 2026-02-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd1e2f3g4h5i6'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add gamification columns to users table
    op.add_column('users', sa.Column('xp_total', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('xp_current', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('reputation', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('cp_total', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove gamification columns from users table
    op.drop_column('users', 'cp_total')
    op.drop_column('users', 'reputation')
    op.drop_column('users', 'level')
    op.drop_column('users', 'xp_current')
    op.drop_column('users', 'xp_total')
