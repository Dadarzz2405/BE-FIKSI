"""support comment upvotes

Revision ID: e4f5a6b7c8d9
Revises: d1e2f3g4h5i6
Create Date: 2026-02-26 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d1e2f3g4h5i6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("upvotes", sa.Column("comment_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_upvotes_comment_id_comments",
        "upvotes",
        "comments",
        ["comment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_upvotes_comment_id", "upvotes", ["comment_id"])

    op.alter_column("upvotes", "post_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    op.create_unique_constraint("uq_upvote_user_comment", "upvotes", ["user_id", "comment_id"])
    op.create_check_constraint(
        "ck_upvotes_exactly_one_target",
        "upvotes",
        "(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_upvotes_exactly_one_target", "upvotes", type_="check")
    op.drop_constraint("uq_upvote_user_comment", "upvotes", type_="unique")
    op.alter_column("upvotes", "post_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.drop_index("ix_upvotes_comment_id", table_name="upvotes")
    op.drop_constraint("fk_upvotes_comment_id_comments", "upvotes", type_="foreignkey")
    op.drop_column("upvotes", "comment_id")
