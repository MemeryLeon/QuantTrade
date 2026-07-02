from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)
PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
NPM_REGISTRY = "https://registry.npmmirror.com"


class CommandError(RuntimeError):
    pass


def run(command: list[str], cwd: Path = ROOT) -> None:
    print(f"$ {' '.join(command)}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise CommandError(f"command failed with exit code {completed.returncode}")


def capture(command: list[str], cwd: Path = ROOT) -> str:
    completed = subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=True)
    if completed.returncode != 0:
        raise CommandError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def find_executable(*names: str) -> str:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    raise CommandError(f"missing executable: {' or '.join(names)}")


def docker_compose_base() -> list[str]:
    docker = find_executable("docker")
    return [docker, "compose", "-f", str(ROOT / "docker-compose.dev.yml")]


def npm_base() -> list[str]:
    return [find_executable("npm.cmd", "npm")]


def python_base() -> list[str]:
    return [str(PYTHON)]


def bootstrap() -> None:
    if not VENV_PYTHON.exists():
        run([sys.executable, "-m", "venv", str(ROOT / ".venv")])
    run(python_base() + ["-m", "pip", "install", "-e", ".[dev]", "-i", PIP_INDEX_URL], BACKEND)
    run(npm_base() + ["install", f"--registry={NPM_REGISTRY}"], FRONTEND)


def dev() -> None:
    run(docker_compose_base() + ["up", "-d", "postgres", "redis", "minio"])


def check_docker_services() -> None:
    expected = {
        "quanttrade-postgres": "healthy",
        "quanttrade-redis": "healthy",
        "quanttrade-minio": "healthy",
    }
    docker = find_executable("docker")
    deadline = time.monotonic() + 60
    pending = dict(expected)
    while pending:
        for container, health in list(pending.items()):
            actual = capture(
                [
                    docker,
                    "inspect",
                    "--format",
                    "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                    container,
                ],
            )
            if actual == health:
                pending.pop(container)
            elif time.monotonic() >= deadline:
                raise CommandError(f"{container} expected {health}, got {actual}")
        if pending:
            time.sleep(2)


def doctor() -> None:
    checks: list[tuple[str, str]] = []
    checks.append(("python", capture(python_base() + ["--version"])))
    checks.append(("pyarrow", capture(python_base() + ["-c", "import pyarrow; print(pyarrow.__version__)"])))
    checks.append(("node", capture([find_executable("node"), "--version"])))
    checks.append(("npm", capture(npm_base() + ["--version"])))
    checks.append(("docker", capture([find_executable("docker"), "--version"])))
    run(docker_compose_base() + ["config"])
    check_docker_services()
    for name, value in checks:
        print(f"PASS {name}: {value}")
    print("PASS docker compose config")
    print("PASS postgres/redis/minio health")


def test() -> None:
    run(python_base() + ["-m", "ruff", "check", "app", "tests", "--no-cache"], BACKEND)
    run(python_base() + ["-m", "mypy", "--cache-dir", str(ROOT / ".tmp" / "mypy_cache")], BACKEND)
    run(python_base() + ["-m", "pytest"], BACKEND)
    migration_smoke()


def frontend_openapi() -> None:
    run(npm_base() + ["run", "generate:openapi"], FRONTEND)
    git = find_executable("git")
    run(
        [
            git,
            "diff",
            "--exit-code",
            "--",
            "frontend/src/api/generated/openapi.json",
            "frontend/src/api/generated/schema.d.ts",
        ],
        ROOT,
    )


def frontend_build() -> None:
    frontend_openapi()
    run(npm_base() + ["run", "build"], FRONTEND)


def frontend_test() -> None:
    run(npm_base() + ["test"], FRONTEND)


def test_integration() -> None:
    run(docker_compose_base() + ["config"])
    check_docker_services()
    storage_integration_smoke()
    print("PASS integration smoke: postgres/redis/minio health checks are healthy")


def migration_smoke() -> None:
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect

    with tempfile.TemporaryDirectory() as tmpdir:
        database_path = Path(tmpdir) / "migration-smoke.db"
        config = Config(str(BACKEND / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND / "alembic"))
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{database_path.as_posix()}")
        try:
            if "job_runs" not in inspect(engine).get_table_names():
                raise CommandError("migration smoke did not create job_runs")
            command.downgrade(config, "base")
            if "job_runs" in inspect(engine).get_table_names():
                raise CommandError("migration smoke did not drop job_runs")
        finally:
            engine.dispose()
    print("PASS alembic migration upgrade/downgrade")


def storage_integration_smoke() -> None:
    from io import BytesIO

    from minio import Minio
    from redis import Redis

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = Redis.from_url(redis_url)
    redis_key = "quanttrade:integration:smoke"
    redis_client.set(redis_key, b"ok", ex=60)
    if redis_client.get(redis_key) != b"ok":
        raise CommandError("redis integration smoke failed")
    redis_client.delete(redis_key)

    minio_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    parsed = urlparse(minio_url)
    endpoint = parsed.netloc if parsed.scheme else minio_url
    bucket = os.getenv("MINIO_BUCKET_LEAN_ARTIFACTS", "quanttrade-lean-artifacts")
    minio_client = Minio(
        endpoint,
        access_key=os.getenv("MINIO_ROOT_USER", "quanttrade_minio"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "quanttrade_minio_dev_password"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)
    object_name = "integration/smoke.txt"
    payload = b"ok"
    minio_client.put_object(bucket, object_name, BytesIO(payload), len(payload))
    stat = minio_client.stat_object(bucket, object_name)
    if stat.size != len(payload):
        raise CommandError("minio integration smoke failed")
    minio_client.remove_object(bucket, object_name)
    print("PASS redis/minio adapter smoke")


def check() -> None:
    doctor()
    test()
    frontend_build()
    frontend_test()
    test_integration()


def e2e() -> None:
    run(npm_base() + ["run", "e2e"], FRONTEND)


def down() -> None:
    run(docker_compose_base() + ["down"])


TASKS = {
    "doctor": doctor,
    "bootstrap": bootstrap,
    "dev": dev,
    "check": check,
    "test": test,
    "test-integration": test_integration,
    "e2e": e2e,
    "down": down,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="QuantTrade development command runner")
    parser.add_argument("task", choices=sorted(TASKS))
    args = parser.parse_args()
    try:
        TASKS[args.task]()
    except CommandError as exc:
        print(f"FAIL {args.task}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
