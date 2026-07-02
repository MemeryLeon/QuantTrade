from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_and_downgrade_core_tables(tmp_path: Path) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "migration.db"
    url = f"sqlite:///{database_path.as_posix()}"
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", url)

    command.upgrade(config, "head")

    engine = create_engine(url)
    try:
        inspector = inspect(engine)
        assert "job_runs" in inspector.get_table_names()
        assert "data_snapshots" in inspector.get_table_names()

        command.downgrade(config, "base")

        inspector = inspect(engine)
        assert "job_runs" not in inspector.get_table_names()
        assert "data_snapshots" not in inspector.get_table_names()
    finally:
        engine.dispose()
