#!/usr/bin/env python3
"""Generate the Godot copy of tuning and maps from the headless sources."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "game.contract.json"
MAPS = ROOT / "shared" / "maps"
OUT = ROOT / "godot" / "shared"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_files():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if not isinstance(contract, dict) or not isinstance(contract.get("tuning"), dict):
        raise ValueError("game.contract.json must contain a tuning object")

    files = {}
    files[Path("tuning.json")] = canonical({
        "contract_version": contract["contract_version"],
        "tuning": contract["tuning"],
    })
    for path in sorted(MAPS.glob("night*.json")):
        files[Path("maps") / path.name] = canonical(json.loads(path.read_text(encoding="utf-8")))

    manifest = {
        "generated_by": "tools/sync_shared.py",
        "files": {rel.as_posix(): digest(text) for rel, text in files.items()},
    }
    files[Path("manifest.json")] = canonical(manifest)
    return files


def write_files(files):
    for rel, text in files.items():
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)


def check_files(files):
    stale = []
    for rel, expected in files.items():
        dest = OUT / rel
        if not dest.exists():
            stale.append(f"{rel.as_posix()} (missing)")
            continue
        actual = dest.read_text(encoding="utf-8")
        if actual != expected:
            stale.append(f"{rel.as_posix()} (stale)")
    if stale:
        print("shared data is out of sync: " + ", ".join(stale), file=sys.stderr)
        return 1
    print("shared data is in sync")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Sync shared tuning/maps into godot/shared")
    parser.add_argument("--check", action="store_true", help="verify generated files without writing")
    args = parser.parse_args()
    try:
        files = build_files()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        return check_files(files)
    write_files(files)
    print(f"wrote {len(files)} files to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
