"""Reproducible Phase 2 acceptance checks; Python standard library only."""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game.py"
sys.path.insert(0, str(ROOT))
from game import T  # noqa: E402


def run(tmp, name, night, scenario, inputs, ticks, seed=17, snapshot_every=1):
    scenario_path = Path(tmp) / f"{name}-scenario.json"
    inputs_path = Path(tmp) / f"{name}-inputs.json"
    out_path = Path(tmp) / f"{name}.jsonl"
    if scenario is not None:
        scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    if inputs is not None:
        inputs_path.write_text(json.dumps(inputs), encoding="utf-8")
    cmd = [sys.executable, str(GAME), "--headless", "--seed", str(seed), "--night", str(night),
           "--ticks", str(ticks), "--out", str(out_path), "--snapshot-every", str(snapshot_every)]
    if scenario is not None:
        cmd += ["--scenario", str(scenario_path)]
    if inputs is not None:
        cmd += ["--inputs", str(inputs_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()] if out_path.exists() else []
    return proc, rows


def snap(rows, tick):
    return next(r for r in rows if r.get("type") == "snapshot" and r.get("tick") == tick)


def events(rows, name):
    return [r for r in rows if r.get("type") == "event" and r.get("name") == name]


def empty():
    return {"random_motes": False, "random_shades": False, "random_wisps": False,
            "random_charms": False, "motes": [], "shades": [], "wisps": [], "charms": []}


def main():
    passed = []
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    assert contract["contract_version"] in ("1.2", "1.3")
    assert contract["tuning"] == T
    passed.append("contract v1.2/v1.3 matches simulation constants")

    maps = {}
    for night in (1, 2, 3):
        maps[night] = json.loads((ROOT / "shared" / "maps" / f"night{night}.json").read_text(encoding="utf-8"))
    assert len(maps[1]["lanterns"]) == 5 and maps[1]["platforms"][0]["radius_m"] == 40.0
    assert len(maps[2]["lanterns"]) == 6 and len(maps[2]["wisp_spawn"]) == 2 and len(maps[2]["charm_spawn"]) == 2
    assert len(maps[3]["lanterns"]) == 7 and maps[3]["bell_tower"] and len(maps[3]["wind_zones"]) == 2
    assert any(p["type"] == "ramp" for p in maps[3]["platforms"])
    assert any(p["type"] == "jump_pad" for p in maps[3]["platforms"])
    passed.append("three maps contain required geometry and entities")

    with tempfile.TemporaryDirectory() as tmp:
        for night in (1, 2, 3):
            proc, rows = run(tmp, f"night-{night}", night, empty(), None, 1)
            assert proc.returncode == 0
            assert snap(rows, 1)["night"] == night
        passed.append("--night 1|2|3 runs")

        proc = subprocess.run([sys.executable, str(GAME), "--headless", "--night", "4", "--ticks", "1",
                               "--out", str(Path(tmp, "bad-night.jsonl"))], capture_output=True, text=True)
        assert proc.returncode == 2 and "error:" in proc.stderr
        passed.append("invalid night exits 2")

        paused = {"random_motes": False, "random_shades": False, "motes": [], "shades": [], "paused": True}
        proc, rows = run(tmp, "pause", 1, paused, {"frames": [{"tick": 3, "pause": False}]}, 6)
        final = snap(rows, 6)
        assert proc.returncode == 0 and final["tick"] == 6 and final["sim_tick"] == 3
        assert final["paused"] is False and abs(final["time_left_s"] - (300 - 3 / 60)) < 0.01
        passed.append("pause increments tick but not sim_tick and freezes time")

        proc, rows = run(tmp, "dash", 1, empty(), {"frames": [{"tick": 0, "dash": True, "move": [1, 0]}]}, 1)
        assert proc.returncode == 0 and snap(rows, 1)["player"]["pos"][0] > 0.15
        passed.append("dash moves faster than walking")

        glide_sc = empty() | {"player": {"pos": [0, 5, 0]}}
        proc, rows = run(tmp, "glide", 1, glide_sc, {"frames": [{"tick": 0, "glide": True}]}, 30)
        assert proc.returncode == 0 and snap(rows, 30)["player"]["pos"][1] > 3.5
        passed.append("glide limits falling speed")

        wisp_sc = empty() | {"player": {"pos": [0, 0, 0]}, "wisps": [{"id": "W1", "pos": [1, 0, 0]}]}
        proc, rows = run(tmp, "wisp", 2, wisp_sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["player"]["pos"][0] < -0.01
        passed.append("lost wisp pushes the player")

        charm_sc = wisp_sc | {"charms": [{"id": "C1", "pos": [0.5, 0, 0]}]}
        proc, rows = run(tmp, "charm", 2, charm_sc, None, 1)
        final = snap(rows, 1)
        assert proc.returncode == 0 and events(rows, "charm_picked") and final["wind_shield_s"] > 7.9
        assert abs(final["player"]["pos"][0]) < 0.01
        passed.append("wind charm grants immunity and blocks wisp push")

        wind_sc = empty() | {"player": {"pos": [0, 2.667, 22]}}
        proc, rows = run(tmp, "wind", 3, wind_sc, None, 10)
        assert proc.returncode == 0 and snap(rows, 10)["player"]["pos"][2] > 22.1
        wind_charm = wind_sc | {"charms": [{"id": "C1", "pos": [0, 2.667, 22.5]}]}
        proc, rows = run(tmp, "wind-charm", 3, wind_charm, None, 10)
        final = snap(rows, 10)
        assert proc.returncode == 0 and final["wind_shield_s"] > 7.5 and final["player"]["pos"][2] < 22.1
        passed.append("strong wind pushes unless a charm is active")

        fall_sc = empty() | {"player": {"pos": [41, 0, 0]}}
        proc, rows = run(tmp, "fall", 1, fall_sc, {"frames": [{"tick": 0, "move": [1, 0]}]}, 60)
        assert proc.returncode == 0 and events(rows, "player_hit")
        assert events(rows, "player_hit")[0]["data"]["by"] == "fall"
        assert snap(rows, 60)["player"]["flames"] == 2
        passed.append("fall loses a flame and respawns safely")

        # Phase 3 replaces the old early win and bell-tower rule: all lanterns
        # lit is not enough before dawn, and the dawn check only needs 60%.
        lit = {"lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 8)]}
        early_sc = empty() | lit | {"player": {"pos": [0, 0, 28], "flames": 2}, "time_left_s": 100}
        proc, rows = run(tmp, "night3-early", 3, early_sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "playing"
        passed.append("all lanterns lit does not win before dawn")

        win_sc = empty() | lit | {"player": {"pos": [0, 0, 28], "flames": 2}, "time_left_s": 0.01}
        proc, rows = run(tmp, "night3-win", 3, win_sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "won"
        passed.append("Night 3 wins at dawn without requiring the bell tower")

        five = {"lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 6)]}
        dawn_sc = empty() | five | {"player": {"pos": [0, 0, 28], "flames": 2}, "time_left_s": 0.01}
        proc, rows = run(tmp, "night3-threshold", 3, dawn_sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "won"
        four = {"lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 5)]}
        below_sc = empty() | four | {"player": {"pos": [0, 0, 28], "flames": 2}, "time_left_s": 0.01}
        proc, rows = run(tmp, "night3-below", 3, below_sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "lost"
        assert any(r.get("name") == "game_over" and r["data"]["reason"] == "not_enough_lanterns" for r in rows)
        passed.append("Night 3 dawn threshold is ceil(60% of 7) = 5")

        a_proc, _ = run(tmp, "det-a", 3, empty(), None, 60, seed=909, snapshot_every=10)
        b_proc, _ = run(tmp, "det-b", 3, empty(), None, 60, seed=909, snapshot_every=10)
        assert a_proc.returncode == b_proc.returncode == 0
        assert Path(tmp, "det-a.jsonl").read_bytes() == Path(tmp, "det-b.jsonl").read_bytes()
        passed.append("Night 3 output is deterministic")

        perf_sc = empty() | {"time_left_s": 420}
        start = time.perf_counter()
        proc, _ = run(tmp, "perf", 3, perf_sc, None, 21600, snapshot_every=600)
        elapsed = time.perf_counter() - start
        assert proc.returncode == 0 and elapsed <= 30.0, elapsed
        passed.append(f"21,600 Night 3 ticks finish in {elapsed:.2f}s")

    sync = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"],
                          capture_output=True, text=True)
    assert sync.returncode == 0, sync.stderr
    passed.append("godot/shared is in sync with contract and maps")

    print("Phase 2 core checks passed:")
    for item in passed:
        print(f"- {item}")


if __name__ == "__main__":
    main()
