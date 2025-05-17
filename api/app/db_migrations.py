from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations():
    # assume this file lives next to alembic.ini
    base_dir = Path(__file__).resolve().parent.parent
    cfg = Config(base_dir / "alembic.ini")
    # Apply all pending migrations
    command.upgrade(cfg, "head")
