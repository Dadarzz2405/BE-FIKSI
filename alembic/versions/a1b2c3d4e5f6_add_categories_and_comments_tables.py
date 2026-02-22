"""add categories and comments tables

Revision ID: a1b2c3d4e5f6
Revises: 916746b69445
Create Date: 2026-02-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '916746b69445'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_name', 'categories', ['name'])
    op.create_index('ix_categories_slug', 'categories', ['slug'])

    # add category_id to posts
    op.add_column('posts', sa.Column(
        'category_id',
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey('categories.id', ondelete='SET NULL'),
        nullable=True,
    ))
    op.create_index('ix_posts_category_id', 'posts', ['category_id'])

    # comments table
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comments_id', 'comments', ['id'])
    op.create_index('ix_comments_post_id', 'comments', ['post_id'])
    op.create_index('ix_comments_author_id', 'comments', ['author_id'])


def downgrade() -> None:
    op.drop_index('ix_comments_author_id', 'comments')
    op.drop_index('ix_comments_post_id', 'comments')
    op.drop_index('ix_comments_id', 'comments')
    op.drop_table('comments')
    op.drop_index('ix_posts_category_id', 'posts')
    op.drop_column('posts', 'category_id')
    op.drop_index('ix_categories_slug', 'categories')
    op.drop_index('ix_categories_name', 'categories')
    op.drop_index('ix_categories_id', 'categories')
    op.drop_table('categories')
