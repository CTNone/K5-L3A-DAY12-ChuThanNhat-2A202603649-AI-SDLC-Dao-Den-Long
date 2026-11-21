#!/usr/bin/env python3
"""Regenerate Phase 4 evidence from real runs (never edit captured output)."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "proof" / "phase-4"


def run(args: list[str]) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "py_compile", "game.py", "leaderboard.py",
         "tools/verify_phase1.py", "tools/verify_phase2.py",
         "tools/verify_phase3.py", "tools/verify_phase4.py"])
    log_parts: list[str] = []
    for script in ("verify_phase1.py", "verify_phase2.py", "verify_phase3.py"):
        proc = subprocess.run([sys.executable, f"tools/{script}"], cwd=ROOT, text=True,
                              capture_output=True)
        log_parts.append(proc.stdout + proc.stderr)
        if proc.returncode:
            print(proc.stdout + proc.stderr)
            return proc.returncode
    run([sys.executable, "game.py", "--bench", "--bench-out", "bench.json"])
    run([sys.executable, "game.py", "--soak", "--soak-out", "soak.json"])
    for script in ("verify_phase1.py", "verify_phase2.py", "verify_phase3.py",
                   "verify_phase4.py"):
        proc = subprocess.run([sys.executable, f"tools/{script}"], cwd=ROOT, text=True,
                              capture_output=True)
        log_parts.append(proc.stdout + proc.stderr)
        if proc.returncode:
            print(proc.stdout + proc.stderr)
            return proc.returncode
    (OUT / "verify.log").write_text("\n".join(log_parts), encoding="utf-8")
    for name in ("bench.json", "soak.json"):
        shutil.copy2(ROOT / name, OUT / name)
    print(f"Phase 4 evidence written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
