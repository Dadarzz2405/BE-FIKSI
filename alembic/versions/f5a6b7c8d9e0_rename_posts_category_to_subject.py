"""rename posts category_id to subject_id

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-02-28 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    insp = inspect(conn)
    return any(col["name"] == column for col in insp.get_columns(table))


def _index_exists(conn, table: str, index_name: str) -> bool:
    insp = inspect(conn)
    return any(idx["name"] == index_name for idx in insp.get_indexes(table))


def _drop_foreign_keys_for_column(conn, table: str, column: str) -> None:
    insp = inspect(conn)
    for fk in insp.get_foreign_keys(table):
        constrained = fk.get("constrained_columns") or []
        name = fk.get("name")
        if name and column in constrained:
            op.drop_constraint(name, table, type_="foreignkey")


def upgrade() -> None:
    conn = op.get_bind()

    has_category_id = _column_exists(conn, "posts", "category_id")
    has_subject_id = _column_exists(conn, "posts", "subject_id")

    if has_category_id and not has_subject_id:
        # Remove old FK first, then rename in-place to preserve existing values.
        _drop_foreign_keys_for_column(conn, "posts", "category_id")
        op.alter_column("posts", "category_id", new_column_name="subject_id")
        has_subject_id = True

    if not has_subject_id:
        op.add_column(
            "posts",
            sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        )

    _drop_foreign_keys_for_column(conn, "posts", "subject_id")
    op.execute(
        """
        UPDATE posts p
        SET subject_id = NULL
        WHERE subject_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM subjects s WHERE s.id = p.subject_id
          )
        """
    )
    op.create_foreign_key(
        "fk_posts_subject_id_subjects",
        "posts",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="SET NULL",
    )

    if _index_exists(conn, "posts", "ix_posts_category_id"):
        op.drop_index("ix_posts_category_id", table_name="posts")
    if not _index_exists(conn, "posts", "ix_posts_subject_id"):
        op.create_index("ix_posts_subject_id", "posts", ["subject_id"])


def downgrade() -> None:
    conn = op.get_bind()

    if _index_exists(conn, "posts", "ix_posts_subject_id"):
        op.drop_index("ix_posts_subject_id", table_name="posts")

    _drop_foreign_keys_for_column(conn, "posts", "subject_id")

    has_subject_id = _column_exists(conn, "posts", "subject_id")
    has_category_id = _column_exists(conn, "posts", "category_id")

    if has_subject_id and not has_category_id:
        op.alter_column("posts", "subject_id", new_column_name="category_id")
        has_category_id = True

    if has_category_id:
        op.execute(
            """
            UPDATE posts p
            SET category_id = NULL
            WHERE category_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM categories c WHERE c.id = p.category_id
              )
            """
        )
        op.create_foreign_key(
            "fk_posts_category_id_categories",
            "posts",
            "categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )
        if not _index_exists(conn, "posts", "ix_posts_category_id"):
            op.create_index("ix_posts_category_id", "posts", ["category_id"])
