"""rename posts image column

Revision ID: 916746b69445
Revises: 
Create Date: 2026-02-15 17:28:46.026177

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '916746b69445'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("posts", "image", new_column_name="image_url")


def downgrade() -> None:
    op.alter_column("posts", "image_url", new_column_name="image")
