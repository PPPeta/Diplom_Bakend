"""domain models: catalog, pricing, requests, orders, tasks, documents, payments, messages

Revision ID: 0002_domain_models
Revises: 0001_auth_rbac
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0002_domain_models"
down_revision = "0001_auth_rbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_catalog",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column(
            "base_price",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.true()
        ),
    )

    op.create_table(
        "price_lists",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("partners.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_to", sa.Date, nullable=True),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.true()
        ),
    )

    op.create_table(
        "price_list_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "price_list_id",
            sa.Integer,
            sa.ForeignKey("price_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            sa.Integer,
            sa.ForeignKey("service_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
    )

    op.create_table(
        "partner_terms",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("partners.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "discount_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "commission_pct",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "priority", sa.Integer, nullable=False, server_default=sa.text("100")
        ),
        sa.Column("notes", sa.String(255), nullable=True),
    )

    op.add_column(
        "partners",
        sa.Column("price_list_id", sa.Integer, nullable=True),
    )
    op.create_foreign_key(
        "fk_partners_price_list_id",
        "partners",
        "price_lists",
        ["price_list_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column(
            "source", sa.String(32), nullable=False, server_default="site"
        ),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="new"
        ),
        sa.Column(
            "pdn_consent", sa.Boolean, nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("number", sa.String(32), nullable=False, unique=True),
        sa.Column("client_ref", sa.String(255), nullable=True),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("partners.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "manager_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="new"
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            sa.Integer,
            sa.ForeignKey("service_catalog.id"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "sum",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "executor_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="open"
        ),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("number", sa.String(64), nullable=True),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="draft"
        ),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("partners.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("payments")
    op.drop_table("documents")
    op.drop_table("tasks")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("requests")
    op.drop_constraint("fk_partners_price_list_id", "partners", type_="foreignkey")
    op.drop_column("partners", "price_list_id")
    op.drop_table("partner_terms")
    op.drop_table("price_list_items")
    op.drop_table("price_lists")
    op.drop_table("service_catalog")
