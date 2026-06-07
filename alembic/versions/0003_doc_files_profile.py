"""document file storage + user phone

Revision ID: 0003_doc_files_profile
Revises: 0002_domain_models
Create Date: 2026-06-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0003_doc_files_profile"
down_revision = "0002_domain_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Store uploaded document files directly in the DB (self-contained, no volume needed).
    op.add_column("documents", sa.Column("filename", sa.String(255), nullable=True))
    op.add_column(
        "documents", sa.Column("content_type", sa.String(128), nullable=True)
    )
    op.add_column("documents", sa.Column("size", sa.Integer, nullable=True))
    op.add_column("documents", sa.Column("content", sa.LargeBinary, nullable=True))
    op.add_column("documents", sa.Column("uploaded_by", sa.Integer, nullable=True))
    op.create_foreign_key(
        "fk_documents_uploaded_by",
        "documents",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Profile phone number.
    op.add_column("users", sa.Column("phone", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "phone")
    op.drop_constraint("fk_documents_uploaded_by", "documents", type_="foreignkey")
    op.drop_column("documents", "uploaded_by")
    op.drop_column("documents", "content")
    op.drop_column("documents", "size")
    op.drop_column("documents", "content_type")
    op.drop_column("documents", "filename")
