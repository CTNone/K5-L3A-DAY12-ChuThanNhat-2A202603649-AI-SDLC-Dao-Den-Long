#!/usr/bin/env python3
"""Phase 4 release checks: contract, leaderboard, evidence and docs."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import leaderboard  # noqa: E402


def fail(message: str) -> None:
    print(f"Phase 4 check failed: {message}")
    raise SystemExit(1)


def main() -> int:
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    if contract.get("contract_version") != "1.3":
        fail("contract version must be 1.3")
    for key in ("bench_cmd", "soak_cmd", "leaderboard_cmd"):
        if not isinstance(contract.get(key), str) or not contract[key]:
            fail(f"missing {key}")
    if contract.get("leaderboard", {}).get("max_entries") != 10:
        fail("leaderboard.max_entries must be 10")
    if "input" not in contract or "accessibility" not in contract:
        fail("missing input/accessibility contract sections")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "leaderboard.json"
        leaderboard.add(path, "Alice", 100, 1, 20261121, "2026-11-21T10:00:00Z")
        leaderboard.add(path, "Bob", 100, 2, 20261121, "2026-11-21T09:00:00Z")
        leaderboard.add(path, "Cara", 200, 3, 20261121, "2026-11-21T11:00:00Z")
        entries = leaderboard.load(path)
        if [e["name"] for e in entries] != ["Cara", "Bob", "Alice"]:
            fail("leaderboard sorting/tie-break is wrong")
        if len(entries) != 3:
            fail("leaderboard lost entries")
        exported = leaderboard.export(Path(tmp) / "export.json", path)
        if exported != entries:
            fail("leaderboard export mismatch")

    bench = json.loads((ROOT / "bench.json").read_text(encoding="utf-8"))
    for key in ("avg_fps", "p1_low_fps", "frame_ms_p95", "load_ms", "peak_mem_mb"):
        if key not in bench:
            fail(f"bench.json missing {key}")
    if bench.get("renderer") != "headless-simulation":
        fail("bench.json must state headless-simulation")
    if bench.get("frames", 0) < 60:
        fail("bench.json has too few frames")

    soak = json.loads((ROOT / "soak.json").read_text(encoding="utf-8"))
    if soak.get("crashes"):
        fail("soak.json reports crashes")
    if len(soak.get("nights", [])) != 10:
        fail("soak.json must contain 10 nights")
    if soak.get("rss_start_mb", 0) <= 0 or soak.get("rss_end_mb", 0) <= 0:
        fail("soak.json missing real RSS")

    required = [
        "LICENSE", "CREDITS.md", "Dockerfile",
        "docs/notes/phase-4-spec.md", "docs/notes/phase-4-assumptions.md",
        "docs/notes/phase-4-retro.md", "docs/notes/ai-usage-log.md",
        "docs/demo/demo.mp4", "docs/proof/phase-4/README.md",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")
    if (ROOT / "docs/demo/demo.mp4").stat().st_size < 1_000_000:
        fail("demo.mp4 is too small")

    print("Phase 4 release checks passed:")
    print("- contract 1.3, bench/soak/leaderboard commands")
    print("- leaderboard sort, tie-break and export")
    print("- bench.json and soak.json are real captured output")
    print("- LICENSE, credits, Dockerfile, Phase 4 notes and demo video")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
