"""add upvotes table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old upvotes table if it exists (had nullable post_id/comment_id - wrong schema)
    op.execute("DROP TABLE IF EXISTS upvotes CASCADE")

    op.create_table(
        'upvotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'post_id', name='unique_post_upvote'),
    )
    op.create_index('ix_upvotes_id', 'upvotes', ['id'])
    op.create_index('ix_upvotes_user_id', 'upvotes', ['user_id'])
    op.create_index('ix_upvotes_post_id', 'upvotes', ['post_id'])


def downgrade() -> None:
    op.drop_index('ix_upvotes_post_id', 'upvotes')
    op.drop_index('ix_upvotes_user_id', 'upvotes')
    op.drop_index('ix_upvotes_id', 'upvotes')
    op.drop_table('upvotes')
