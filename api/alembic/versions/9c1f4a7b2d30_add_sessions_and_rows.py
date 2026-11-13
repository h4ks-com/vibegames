"""Add sessions, login_states and rows

Revision ID: 9c1f4a7b2d30
Revises: 684f2e4cbdc5
Create Date: 2026-11-13 14:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1f4a7b2d30"
down_revision: str | None = "684f2e4cbdc5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("sub", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("picture", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.Column("last_seen", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_sessions_sub"), ["sub"], unique=False)
        batch_op.create_index(batch_op.f("ix_sessions_expires_at"), ["expires_at"], unique=False)

    op.create_table(
        "login_states",
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("verifier", sa.String(length=128), nullable=False),
        sa.Column("nonce", sa.String(length=64), nullable=False),
        sa.Column("next_path", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("state"),
    )

    op.create_table(
        "rows",
        sa.Column("app", sa.String(length=64), nullable=False),
        sa.Column("usr", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("public", sa.Boolean(), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("app", "usr", "key"),
    )
    with op.batch_alter_table("rows", schema=None) as batch_op:
        batch_op.create_index("rows_public", ["app", "public", "updated_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("rows", schema=None) as batch_op:
        batch_op.drop_index("rows_public")
    op.drop_table("rows")
    op.drop_table("login_states")
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_sessions_expires_at"))
        batch_op.drop_index(batch_op.f("ix_sessions_sub"))
    op.drop_table("sessions")
