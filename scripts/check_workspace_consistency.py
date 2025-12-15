#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".git", "docs", "frontend", "logs"
}

CORE_DIRS = [
    PROJECT_ROOT / "saasentialcore",
    PROJECT_ROOT / "api" / "core",
]

FORBIDDEN_PATTERNS = [
    # interdire le legacy
    re.compile(r"\bsaasentialcore\.products\b"),
    # interdire core -> products (imports python)
    re.compile(r"^\s*from\s+products\.", re.MULTILINE),
    re.compile(r"^\s*import\s+products\.", re.MULTILINE),
]

def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)

def iter_py_files(base: Path):
    if not base.exists():
        return
    for p in base.rglob("*.py"):
        if is_excluded(p):
            continue
        yield p

def scan_file(path: Path) -> list[str]:
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"[READ] {path}: {e}"]
    errors: list[str] = []
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(txt):
            errors.append(f"[IMPORT] Forbidden pattern '{pat.pattern}' in {path}")
    return errors

def main() -> int:
    print("=== Sparkmetriq Workspace Consistency Check ===")
    print(f"Racine du projet : {PROJECT_ROOT}")

    errors: list[str] = []

    for d in CORE_DIRS:
        for f in iter_py_files(d):
            errors.extend(scan_file(f))

    if errors:
        print("\nÉCHEC : incohérences détectées :\n")
        for e in errors:
            print(" -", e)
        return 1

    print("\nOK : workspace conforme (checks minimaux).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
