"""Regenerate Phase 2 evidence from real commands; never edits captured output."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs" / "proof" / "phase-2"
sys.path.insert(0, str(ROOT))
from game import find_godot  # noqa: E402


def run(name, cmd, log_name):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = PROOF / log_name
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    print(f"{name}: exit {proc.returncode} -> {log.relative_to(ROOT)}")
    return proc


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    failures = []
    checks = {}

    commands = [
        ("compile", [sys.executable, "-m", "py_compile", "game.py", "tools/verify_phase1.py", "tools/capture_phase1_evidence.py"], "compile.log"),
        ("sync-check", [sys.executable, "tools/sync_shared.py", "--check"], "sync-check.log"),
        ("verify-phase1", [sys.executable, "tools/verify_phase1.py"], "verify-phase1.log"),
        ("verify-phase2", [sys.executable, "tools/verify_phase2.py"], "verify-phase2.log"),
        ("web-check", [sys.executable, "game.py", "--check"], "web-check.log"),
        ("build-web", [sys.executable, "tools/build_web.py"], "build-web.log"),
    ]
    for name, cmd, log_name in commands:
        proc = run(name, cmd, log_name)
        checks[name] = {"cmd": cmd, "exit": proc.returncode, "log": f"docs/proof/phase-2/{log_name}"}
        if proc.returncode != 0:
            failures.append(name)

    headless = []
    for night in (1, 2, 3):
        out = PROOF / f"night{night}-headless.jsonl"
        proc = run(
            f"headless-night{night}",
            [sys.executable, "game.py", "--headless", "--seed", "7", "--night", str(night),
             "--ticks", "600", "--snapshot-every", "10", "--out", str(out)],
            f"night{night}-headless.log",
        )
        checks[f"headless-night{night}"] = {"cmd": "python game.py --headless --seed 7 --night %d --ticks 600" % night,
                                           "exit": proc.returncode, "out": f"docs/proof/phase-2/{out.name}"}
        if proc.returncode != 0:
            failures.append(f"headless-night{night}")
        headless.append(out)

    det_hashes = []
    for run_index in (1, 2):
        out = PROOF / f"night3-determinism-{run_index}.jsonl"
        proc = run(
            f"determinism-{run_index}",
            [sys.executable, "game.py", "--headless", "--seed", "7", "--night", "3",
             "--ticks", "600", "--snapshot-every", "10", "--out", str(out)],
            f"night3-determinism-{run_index}.log",
        )
        if proc.returncode != 0:
            failures.append(f"determinism-{run_index}")
        det_hashes.append(sha256(out))
    deterministic = len(set(det_hashes)) == 1
    checks["determinism-night3"] = {"hashes": det_hashes, "equal": deterministic}
    if not deterministic:
        failures.append("determinism-night3")

    godot = find_godot()
    if godot is None:
        failures.append("godot-not-found")
        checks["godot-capture"] = {"exit": 127, "error": "Godot 4.7.2 not found"}
    else:
        proc = run(
            "godot-capture",
            [str(godot), "--path", "godot", "--", "--capture", "--capture-dir", str(PROOF)],
            "godot-capture.log",
        )
        checks["godot-capture"] = {"cmd": "godot --path godot -- --capture", "exit": proc.returncode}
        if proc.returncode != 0:
            failures.append("godot-capture")

    manifest = {
        "phase": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_version": json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))["contract_version"],
        "seed": 7,
        "ticks": 600,
        "checks": checks,
        "failures": failures,
        "files": [],
    }
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if git.returncode == 0:
        manifest["git_head"] = git.stdout.strip()

    for path in sorted(PROOF.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["files"].append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    (PROOF / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"manifest: {PROOF / 'manifest.json'}")
    print(f"failures: {failures or 'none'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
