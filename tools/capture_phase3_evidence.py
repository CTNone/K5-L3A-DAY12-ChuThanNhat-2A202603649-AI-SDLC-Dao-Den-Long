"""Regenerate Phase 3 evidence from real commands; never edits captured output."""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs" / "proof" / "phase-3"
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


def write_scenario(name, scenario):
    path = PROOF / f"{name}-scenario.json"
    path.write_text(json.dumps(scenario, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    failures = []
    checks = {}

    commands = [
        ("compile", [sys.executable, "-m", "py_compile", "game.py", "tools/verify_phase1.py",
                     "tools/verify_phase2.py", "tools/verify_phase3.py",
                     "tools/capture_phase1_evidence.py", "tools/capture_phase2_evidence.py",
                     "tools/capture_phase3_evidence.py"], "compile.log"),
        ("sync-check", [sys.executable, "tools/sync_shared.py", "--check"], "sync-check.log"),
        ("verify-phase1", [sys.executable, "tools/verify_phase1.py"], "verify-phase1.log"),
        ("verify-phase2", [sys.executable, "tools/verify_phase2.py"], "verify-phase2.log"),
        ("verify-phase3", [sys.executable, "tools/verify_phase3.py"], "verify-phase3.log"),
        ("web-check", [sys.executable, "game.py", "--check"], "web-check.log"),
        ("build-web", [sys.executable, "tools/build_web.py"], "build-web.log"),
    ]
    for name, cmd, log_name in commands:
        proc = run(name, cmd, log_name)
        checks[name] = {"cmd": cmd, "exit": proc.returncode, "log": f"docs/proof/phase-3/{log_name}"}
        if proc.returncode != 0:
            failures.append(name)

    empty = {"random_motes": False, "random_shades": False, "random_wisps": False,
             "random_charms": False, "motes": [], "wisps": [], "charms": []}
    scenarios = {
        "refuel": (empty | {"player": {"pos": [0, 0, 0], "carried": 5},
                            "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 50},
                                         {"id": "L2", "pos": [0.5, 0, 0], "lit": True, "fuel": 50}],
                            "shades": []},
                   {"frames": [{"tick": 0, "interact": True}]}, 5),
        "depletion": (empty | {"player": {"pos": [10, 0, 0]}, "time_left_s": 300,
                               "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 1}],
                               "shades": []},
                      None, 61),
        "drain": (empty | {"player": {"pos": [30, 0, 0]}, "time_left_s": 300,
                           "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
                           "shades": [{"id": "S1", "pos": [2, 0, 0]}]},
                  None, 30),
        "relight": (empty | {"player": {"pos": [0, 0, 0], "carried": 5},
                             "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": False, "fuel": 0, "ever_lit": True}],
                             "shades": []},
                    {"frames": [{"tick": 0, "interact": True}]}, 5),
        "pushback": (empty | {"player": {"pos": [0, 0, 0], "carried": 10},
                              "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 20}],
                              "shades": [{"id": "S1", "pos": [0.5, 0, 1]}]},
                     {"frames": [{"tick": 0, "interact": True}]}, 5),
        "dawn-threshold": (empty | {"player": {"flames": 2}, "time_left_s": 0.01,
                                    "lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 4)], "shades": []},
                           None, 1),
        "colorblind": (empty | {"color_mode": "colorblind", "shades": []}, None, 1),
    }
    for name, (scenario, inputs, ticks) in scenarios.items():
        scenario_path = write_scenario(name, scenario)
        inputs_path = PROOF / f"{name}-inputs.json"
        if inputs is not None:
            inputs_path.write_text(json.dumps(inputs) + "\n", encoding="utf-8")
        out = PROOF / f"{name}.jsonl"
        cmd = [sys.executable, "game.py", "--headless", "--seed", "7", "--night", "1",
               "--ticks", str(ticks), "--snapshot-every", "1", "--scenario", str(scenario_path),
               "--out", str(out)]
        if inputs is not None:
            cmd += ["--inputs", str(inputs_path)]
        proc = run(name, cmd, f"{name}.log")
        checks[name] = {"cmd": cmd, "exit": proc.returncode, "out": f"docs/proof/phase-3/{out.name}"}
        if proc.returncode != 0:
            failures.append(name)

    det_hashes = []
    drain_scenario = PROOF / "drain-scenario.json"
    for run_index in (1, 2):
        out = PROOF / f"drain-determinism-{run_index}.jsonl"
        proc = run(
            f"determinism-{run_index}",
            [sys.executable, "game.py", "--headless", "--seed", "7", "--night", "1",
             "--ticks", "120", "--snapshot-every", "10", "--scenario", str(drain_scenario),
             "--out", str(out)],
            f"drain-determinism-{run_index}.log",
        )
        if proc.returncode != 0:
            failures.append(f"determinism-{run_index}")
        det_hashes.append(sha256(out))
    deterministic = len(set(det_hashes)) == 1
    checks["determinism-drain"] = {"hashes": det_hashes, "equal": deterministic}
    if not deterministic:
        failures.append("determinism-drain")

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
        "phase": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract_version": json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))["contract_version"],
        "seed": 7,
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
