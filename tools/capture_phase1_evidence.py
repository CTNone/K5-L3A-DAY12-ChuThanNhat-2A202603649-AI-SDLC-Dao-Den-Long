"""Capture reproducible Phase 1 contract evidence under docs/proof/phase-1."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs" / "proof" / "phase-1"
GAME = ROOT / "game.py"


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(name, scenario, inputs, ticks, interval, seed=17):
    sc = PROOF / f"{name}-scenario.json"
    inp = PROOF / f"{name}-inputs.json"
    out = PROOF / f"{name}.jsonl"
    write_json(sc, scenario)
    write_json(inp, inputs)
    cmd = [sys.executable, str(GAME), "--headless", "--seed", str(seed), "--night", "1",
           "--scenario", str(sc), "--inputs", str(inp), "--ticks", str(ticks),
           "--snapshot-every", str(interval), "--out", str(out)]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (PROOF / f"{name}-stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise SystemExit(f"{name} failed ({proc.returncode}): {proc.stderr}")
    return cmd, out.read_bytes()


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    empty = {"random_motes": False, "random_shades": False, "motes": [], "shades": []}
    # Five pickups in sequence, then deposit next to L1 at x=20.
    pickup = dict(empty, player={"pos": [0, 0, 0]}, motes=[[0, 0, 0]] * 5,
                  lanterns=[{"id": "L1", "pos": [20, 0, 0]}])
    frames = []
    for tick in (0, 2, 4, 6, 8):
        frames.extend([{"tick": tick, "interact": True}, {"tick": tick + 1, "interact": False}])
    frames.extend([{"tick": 10, "move": [1, 0]}, {"tick": 226, "move": [0, 0]},
                   {"tick": 227, "interact": True}, {"tick": 228, "interact": False}])
    _, pickup_bytes = run("pickup-deposit", pickup, {"frames": frames}, 229, 10)
    pickup_rows = [json.loads(line) for line in pickup_bytes.splitlines()]
    pickup_events = [row["name"] for row in pickup_rows if row.get("type") == "event"]
    assert pickup_events.count("mote_picked") == 5 and "lantern_lit" in pickup_events, pickup_events

    pulse = dict(empty, player={"pos": [0, 0, 0], "carried": 2},
                 shades=[{"id": "Sx", "pos": [4, 0, 0]}])
    _, pulse_bytes = run("pulse", pulse, {"frames": [{"tick": 0, "pulse": True}]}, 1, 1)
    assert any(json.loads(line).get("name") == "pulse" for line in pulse_bytes.splitlines())

    hit = dict(empty, player={"pos": [0, 0, 0], "carried": 4},
               shades=[{"id": "Sx", "pos": [0.5, 0, 0]}])
    _, hit_bytes = run("hit-loss", hit, {"frames": []}, 1, 1)
    assert any(json.loads(line).get("name") == "player_hit" for line in hit_bytes.splitlines())

    lethal = dict(empty, player={"pos": [0, 0, 0], "flames": 1},
                  shades=[{"id": "Sx", "pos": [0.5, 0, 0]}])
    _, loss_bytes = run("loss", lethal, {"frames": []}, 2, 1)
    loss_rows = [json.loads(line) for line in loss_bytes.splitlines()]
    loss_event = next(row for row in loss_rows if row.get("type") == "event" and row.get("name") == "game_over")
    assert loss_rows[-1].get("state") == "lost" and loss_event["data"] == {"result": "lost", "reason": "no_flames"}

    win = dict(empty, lanterns=[{"id": f"L{i}", "lit": True} for i in range(1, 6)])
    _, win_bytes = run("win", win, {"frames": []}, 1, 1)
    win_event = next(json.loads(line) for line in win_bytes.splitlines()
                     if json.loads(line).get("type") == "event" and json.loads(line).get("name") == "game_over")
    assert win_event["data"] == {"result": "won", "reason": "all_lit"}

    # Tick 0 exists before input; ticks are capped at 5; interval emits 2 and 4.
    boundary_cmd = [sys.executable, str(GAME), "--headless", "--seed", "17", "--ticks", "5",
                    "--snapshot-every", "2", "--out", str(PROOF / "boundary.jsonl")]
    proc = subprocess.run(boundary_cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode:
        raise SystemExit(proc.stderr)
    boundary = (PROOF / "boundary.jsonl").read_bytes()
    (PROOF / "boundary-stderr.txt").write_text(proc.stderr, encoding="utf-8")
    # Preserve the exact same-seed comparison as files, not a hand-copied claim.
    command, output = run("determinism-a", empty, {"frames": []}, 60, 10, 909)
    run("determinism-b", empty, {"frames": []}, 60, 10, 909)
    same = (PROOF / "determinism-b.jsonl").read_bytes() == output
    (PROOF / "determinism-compare.txt").write_text(
        f"seed=909 scenario=determinism-a/b ticks=60\nbyte_identical={str(same).lower()}\nbytes={len(output)}\n", encoding="utf-8")
    if not same:
        raise SystemExit("same seed outputs differ")

    rows = [json.loads(line) for line in boundary.splitlines()]
    snaps = [r["tick"] for r in rows if r.get("type") == "snapshot"]
    assert snaps == [0, 2, 4], snaps
    assert rows[-1] == {"type": "end", "ticks": 5, "state": "playing", "score": 0}
    zero_cmd = [sys.executable, str(GAME), "--headless", "--ticks", "0", "--out", str(PROOF / "zero-ticks.jsonl")]
    zero_proc = subprocess.run(zero_cmd, cwd=ROOT, capture_output=True, text=True)
    if zero_proc.returncode:
        raise SystemExit(zero_proc.stderr)
    zero_rows = [json.loads(line) for line in (PROOF / "zero-ticks.jsonl").read_text(encoding="utf-8").splitlines()]
    zero_snapshot = next(row for row in zero_rows if row.get("type") == "snapshot")
    assert zero_snapshot.get("tick") == 0
    assert zero_rows[-1].get("type") == "end" and zero_rows[-1].get("ticks") == 0

    bad = PROOF / "bad-input.json"
    write_json(bad, {"frames": [{"tick": 0, "move": [1.1, 0]}]})
    bad_out = PROOF / "bad-input.jsonl"
    bad_cmd = [sys.executable, str(GAME), "--headless", "--inputs", str(bad), "--out", str(bad_out)]
    bad_proc = subprocess.run(bad_cmd, cwd=ROOT, capture_output=True, text=True)
    (PROOF / "bad-input-stderr.txt").write_text(bad_proc.stderr, encoding="utf-8")
    assert bad_proc.returncode == 2 and "error:" in bad_proc.stderr
    # Save exact commands and observed statuses for the capture set.
    (PROOF / "commands-and-status.txt").write_text(
        "Build: python -m py_compile game.py tools/verify_phase1.py tools/capture_phase1_evidence.py\n"
        "Harness: python tools/verify_phase1.py\n"
        f"Boundary: {' '.join(boundary_cmd)}\nExit: {proc.returncode}; snapshots={snaps}; end={rows[-1]}\n"
        f"Zero ticks: {' '.join(zero_cmd)}\nExit: {zero_proc.returncode}; first_snapshot={zero_snapshot['type']}@{zero_snapshot['tick']}; end_ticks={zero_rows[-1]['ticks']}\n"
        f"Invalid input: {' '.join(bad_cmd)}\nExit: {bad_proc.returncode}; stderr saved to bad-input-stderr.txt\n"
        f"Determinism command template: {' '.join(command)}\nExit: 0; byte-identical: {str(same).lower()}\n",
        encoding="utf-8")
    print(f"Evidence captured in {PROOF}")
    print(f"Boundary snapshots: {snaps}; end ticks: {rows[-1]['ticks']}; deterministic: {same}")


if __name__ == "__main__":
    main()
