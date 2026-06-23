"""yookassa payment provider fields

Revision ID: 0004_payment_provider
Revises: 0003_doc_files_profile
Create Date: 2026-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0004_payment_provider"
down_revision = "0003_doc_files_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Поля для интеграции платежей с внешним провайдером (ЮKassa).
    op.add_column("payments", sa.Column("provider", sa.String(20), nullable=True))
    op.add_column(
        "payments", sa.Column("external_id", sa.String(64), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("confirmation_url", sa.String(512), nullable=True)
    )
    op.add_column(
        "payments", sa.Column("description", sa.String(255), nullable=True)
    )
    op.create_index(
        "ix_payments_external_id", "payments", ["external_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_payments_external_id", table_name="payments")
    op.drop_column("payments", "description")
    op.drop_column("payments", "confirmation_url")
    op.drop_column("payments", "external_id")
    op.drop_column("payments", "provider")
