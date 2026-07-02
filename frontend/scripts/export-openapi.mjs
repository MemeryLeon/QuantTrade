import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";

const windowsPython = join("..", ".venv", "Scripts", "python.exe");
const unixPython = join("..", ".venv", "bin", "python");
const python = existsSync(windowsPython) ? windowsPython : existsSync(unixPython) ? unixPython : "python";

const result = spawnSync(
  python,
  ["../scripts/export_openapi.py", "frontend/src/api/generated/openapi.json"],
  { stdio: "inherit" },
);

process.exit(result.status ?? 1);
