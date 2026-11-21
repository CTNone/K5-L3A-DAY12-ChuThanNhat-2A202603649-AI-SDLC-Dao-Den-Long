"""Package the web build into a self-contained release zip with its own server."""
import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build" / "web"
DIST = ROOT / "dist"
DEMO = ROOT / "docs" / "demo" / "demo.mp4"

RUN_MD = """# Dao Den Long - web build

1. Extract this zip to any folder.
2. Run `python serve_web.py` (Python 3.10+).
3. Open the URL printed by the server, usually http://127.0.0.1:8060/.

The server sets the COOP/COEP headers that the Godot web build needs.
Use `--port` or `--no-browser` if needed.
"""


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_zip(version):
    index = SOURCE / "index.html"
    if not index.exists():
        print(f"Missing {index}; run python tools/build_web.py first.", file=sys.stderr)
        return None
    DIST.mkdir(parents=True, exist_ok=True)
    target = DIST / f"dao-den-long-web-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SOURCE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(SOURCE).as_posix())
        archive.write(ROOT / "tools" / "serve_web.py", "serve_web.py")
        archive.write(DIST / "RUN.md", "RUN.md")
    return target


def write_sums(version, target):
    (DIST / "RUN.md").unlink(missing_ok=True)
    lines = []
    for path in sorted(DIST.glob("*.zip")):
        lines.append(f"{sha256(path)}  {path.name}")
    if DEMO.exists():
        lines.append(f"{sha256(DEMO)}  {DEMO.name}")
    (DIST / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    proof = ROOT / "docs" / "proof" / "phase-4" / f"web-sha256-{version}.txt"
    proof.write_text(sha256(target) + "\n", encoding="utf-8")
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1.0.1")
    args = parser.parse_args()
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "RUN.md").write_text(RUN_MD, encoding="utf-8")
    target = build_zip(args.version)
    if target is None:
        return 1
    lines = write_sums(args.version, target)
    print(f"Release zip: {target}")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
