"""auth and rbac tables

Revision ID: 0001_auth_rbac
Revises:
Create Date: 2026-06-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth_rbac"
down_revision = None
branch_labels = None
depends_on = None

PERMISSIONS = [
    "orders.read",
    "orders.write",
    "requests.read",
    "requests.write",
    "tasks.read",
    "tasks.write",
    "documents.read",
    "documents.write",
    "payments.read",
    "payments.write",
    "partners.read",
    "partners.write",
    "catalog.read",
    "catalog.write",
    "users.manage",
    "analytics.read",
]


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            sa.Integer,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "partners",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("org_name", sa.String(255), nullable=False),
        sa.Column("inn", sa.String(12), unique=True, nullable=True),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("contract_no", sa.String(64), nullable=True),
        sa.Column(
            "status", sa.String(32), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "is_active", sa.Boolean, nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "is_partner_admin",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("roles.id"),
            nullable=False,
        ),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("partners.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        roles_table,
        [
            {"id": 1, "code": "admin", "name": "Administrator"},
            {"id": 2, "code": "manager", "name": "Manager"},
            {"id": 3, "code": "executor", "name": "Executor"},
            {"id": 4, "code": "partner", "name": "Partner"},
        ],
    )

    permissions_table = sa.table(
        "permissions",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        permissions_table,
        [
            {"id": index + 1, "code": code, "description": None}
            for index, code in enumerate(PERMISSIONS)
        ],
    )

    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", sa.Integer),
        sa.column("permission_id", sa.Integer),
    )
    op.bulk_insert(
        role_permissions_table,
        [
            {"role_id": 1, "permission_id": index + 1}
            for index in range(len(PERMISSIONS))
        ],
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("partners")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
