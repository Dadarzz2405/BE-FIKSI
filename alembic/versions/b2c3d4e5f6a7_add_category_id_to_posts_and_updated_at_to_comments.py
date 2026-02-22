"""add category_id to posts and updated_at to comments

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    insp = inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()

    # Add category_id to posts only if missing (a1b2c3d4e5f6 may have already added it)
    if not _column_exists(conn, "posts", "category_id"):
        op.add_column('posts', sa.Column(
            'category_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ))
        op.create_foreign_key(
            'fk_posts_category_id',
            'posts', 'categories',
            ['category_id'], ['id'],
            ondelete='SET NULL',
        )
        op.create_index('ix_posts_category_id', 'posts', ['category_id'])

    # Add updated_at to comments only if missing (comments table may have been created with it)
    if not _column_exists(conn, "comments", "updated_at"):
        op.add_column('comments', sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=True,
        ))
        op.execute("UPDATE comments SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "posts", "category_id"):
        op.drop_index('ix_posts_category_id', 'posts')
        op.drop_constraint('fk_posts_category_id', 'posts', type_='foreignkey')
        op.drop_column('posts', 'category_id')
    if _column_exists(conn, "comments", "updated_at"):
        op.drop_column('comments', 'updated_at')
