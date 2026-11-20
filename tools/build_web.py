"""Build the Godot web export with the locally installed Godot 4.7.2 editor."""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot"
OUTPUT = ROOT / "build" / "web" / "index.html"


def template_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Godot"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Godot"
    else:
        base = Path.home() / ".local" / "share" / "godot"
    return base / "export_templates" / "4.7.2.stable"


def find_godot():
    for candidate in (
        Path("C:/Tools/Godot/Godot_v4.7.2-stable_win64_console.exe"),
        Path("C:/Tools/Godot/Godot_v4.7.2-stable_win64.exe"),
    ):
        if candidate.exists():
            return candidate
    for name in ("godot4", "godot"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="export the debug template")
    parser.add_argument("--skip-import", action="store_true")
    args = parser.parse_args()

    godot = find_godot()
    if godot is None:
        print("Godot 4.7.2 was not found. Set it on PATH or install it at C:/Tools/Godot.", file=sys.stderr)
        return 1
    templates = template_dir()
    if not (templates / "web_release.zip").exists():
        print(f"Godot export templates are missing from {templates}", file=sys.stderr)
        print("Install Godot_v4.7.2-stable_export_templates.tpz from the official release, then rerun.", file=sys.stderr)
        return 1
    if not (PROJECT / "project.godot").exists():
        print(f"Godot project not found at {PROJECT}", file=sys.stderr)
        return 1

    sync = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], cwd=ROOT)
    if sync.returncode != 0:
        print("godot/shared is out of sync; run python tools/sync_shared.py", file=sys.stderr)
        return sync.returncode

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if not args.skip_import:
        imported = subprocess.run([str(godot), "--headless", "--path", str(PROJECT), "--import"], cwd=ROOT)
        if imported.returncode != 0:
            return imported.returncode

    mode = "--export-debug" if args.debug else "--export-release"
    exported = subprocess.run([str(godot), "--headless", "--path", str(PROJECT), mode, "Web", str(OUTPUT)], cwd=ROOT)
    if exported.returncode != 0:
        return exported.returncode
    if not OUTPUT.exists():
        print(f"Export finished without {OUTPUT}", file=sys.stderr)
        return 1
    print(f"Web build: {OUTPUT.parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
