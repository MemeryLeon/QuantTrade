from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/export_openapi.py <output-json>", file=sys.stderr)
        return 2

    sys.path.insert(0, str(BACKEND))
    from app.main import app

    output_path = Path(sys.argv[1])
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
