from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

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
    for container, health in expected.items():
        actual = capture(
            [
                docker,
                "inspect",
                "--format",
                "{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}",
                container,
            ],
        )
        if actual != health:
            raise CommandError(f"{container} expected {health}, got {actual}")


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
    run(python_base() + ["-m", "ruff", "check", "app", "tests"], BACKEND)
    run(python_base() + ["-m", "mypy"], BACKEND)
    run(python_base() + ["-m", "pytest"], BACKEND)


def frontend_build() -> None:
    run(npm_base() + ["run", "build"], FRONTEND)


def test_integration() -> None:
    run(docker_compose_base() + ["config"])
    check_docker_services()
    print("PASS integration smoke: postgres/redis/minio health checks are healthy")


def check() -> None:
    doctor()
    test()
    frontend_build()
    test_integration()


def e2e() -> None:
    frontend_build()
    print("PASS e2e baseline smoke: frontend production build completed")


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
