"""Phase 3 / Ticket-03 acceptance checks; Python standard library only."""
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


def lantern(rows, tick, lantern_id):
    return next(l for l in snap(rows, tick)["lanterns"] if l["id"] == lantern_id)


def empty():
    return {"random_motes": False, "random_shades": False, "random_wisps": False,
            "random_charms": False, "motes": [], "shades": [], "wisps": [], "charms": []}


def main():
    passed = []
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    assert contract["contract_version"] == "1.2"
    assert contract["tuning"] == T
    for key in ("capacity_per_light", "capacity_max", "new_light_cost", "relight_cost",
                "lantern_fuel_max", "refuel_fuel_per_mote", "ambient_drain_per_s",
                "shade_drain_per_s", "shade_drain_radius_m", "shade_chase_radius_m",
                "safe_fuel_threshold", "dawn_lantern_ratio", "fuel_push_radius_m", "fuel_push_m"):
        assert key in contract["tuning"], key
    assert "lantern_cost" not in contract["tuning"]
    assert "per_second_left" not in contract["tuning"]["score"]
    assert contract["ui"] == {"color_modes": ["default", "colorblind"],
                              "default_color_mode": "default",
                              "fuel_warning_blink_hz": 1.0}
    shared = json.loads((ROOT / "godot" / "shared" / "tuning.json").read_text(encoding="utf-8"))
    assert shared["contract_version"] == "1.2" and shared["tuning"] == T and shared["ui"] == contract["ui"]
    passed.append("contract v1.2 tuning, score and ui are in sync")

    with tempfile.TemporaryDirectory() as tmp:
        proc, rows = run(tmp, "schema", 1, empty(), None, 1)
        assert proc.returncode == 0
        final = snap(rows, 1)
        assert {"color_mode", "lit_lanterns", "dawn_threshold"} <= set(final)
        assert {"capacity", "successful_lights"} <= set(final["player"])
        assert {"fuel", "deposited", "ever_lit", "relit_count"} <= set(final["lanterns"][0])
        passed.append("snapshot exposes fuel, ever_lit, capacity and dawn fields")

        # Refuel picks the nearest receiving lantern; equal distance uses the
        # smaller id. Fuel is 0..100 and each mote restores 10 fuel.
        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 5},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 50},
                                     {"id": "L2", "pos": [0.5, 0, 0], "lit": True, "fuel": 50}]}
        proc, rows = run(tmp, "refuel-nearest", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        dep = events(rows, "deposit")
        assert proc.returncode == 0 and len(dep) == 1
        assert dep[0]["data"]["lantern_id"] == "L2" and dep[0]["data"]["amount"] == 5 and dep[0]["data"]["fuel"] == 100
        final = snap(rows, 1)
        assert final["player"]["carried"] == 0 and lantern(rows, 1, "L2")["fuel"] == 100
        assert lantern(rows, 1, "L1")["fuel"] == 50
        passed.append("refuel uses the nearest receiving lantern")

        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 5},
                        "lanterns": [{"id": "L1", "pos": [1, 0, 0], "lit": True, "fuel": 50},
                                     {"id": "L2", "pos": [0, 0, 1], "lit": True, "fuel": 50}]}
        proc, rows = run(tmp, "refuel-tie", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        assert proc.returncode == 0 and events(rows, "deposit")[0]["data"]["lantern_id"] == "L1"
        passed.append("refuel tie-break uses the smaller lantern id")

        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 5},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 95}]}
        proc, rows = run(tmp, "refuel-min", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        dep = events(rows, "deposit")[0]["data"]
        assert proc.returncode == 0 and dep["amount"] == 1 and dep["fuel"] == 100
        assert snap(rows, 1)["player"]["carried"] == 4
        passed.append("refuel only spends ceil(missing fuel / 10) motes")

        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 5},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 100}]}
        proc, rows = run(tmp, "refuel-full", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        assert proc.returncode == 0 and not events(rows, "deposit")
        assert snap(rows, 1)["player"]["carried"] == 5 and snap(rows, 1)["score"] == 0
        passed.append("full lantern rejects refuel without an event or score")

        # Ambient drain is 1/s: a fuel-1 lantern goes out exactly on tick 60,
        # emitting lantern_out once and keeping ever_lit.
        sc = empty() | {"player": {"pos": [10, 0, 0]}, "time_left_s": 300,
                        "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 1}]}
        proc, rows = run(tmp, "deplete-ambient", 1, sc, None, 61)
        out = events(rows, "lantern_out")
        assert proc.returncode == 0 and len(out) == 1 and out[0]["tick"] == 60
        assert out[0]["data"]["lantern_id"] == "L1" and out[0]["data"]["ever_lit"] is True
        final = lantern(rows, 61, "L1")
        assert final["lit"] is False and final["fuel"] == 0 and final["deposited"] == 0 and final["ever_lit"] is True
        passed.append("ambient drain depletes exactly at 60 ticks and emits lantern_out")

        # A shade within 2 m adds 5/s, so ambient + shade (6/s) drains fuel 1
        # in 10 ticks. The shade is in the drain state and stops when out.
        sc = empty() | {"player": {"pos": [10, 0, 0]}, "time_left_s": 300,
                        "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 1}],
                        "shades": [{"id": "S1", "pos": [2, 0, 0]}]}
        proc, rows = run(tmp, "deplete-shade", 1, sc, None, 12)
        out = events(rows, "lantern_out")
        assert proc.returncode == 0 and len(out) == 1 and out[0]["tick"] == 10
        assert snap(rows, 1)["shades"][0]["state"] == "drain" and snap(rows, 1)["shades"][0]["drain"] is True
        assert snap(rows, 11)["shades"][0]["state"] == "wander"
        passed.append("shade drain is 5/s and stops after the lantern goes out")

        # Drain rate check: below the safe threshold a shade within 2 m adds
        # 5/s. 10 ticks of 6/s = 60 drain units, i.e. one fuel.
        sc = empty() | {"player": {"pos": [10, 0, 0]}, "time_left_s": 300,
                        "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20}],
                        "shades": [{"id": "S1", "pos": [2, 0, 0]}]}
        proc, rows = run(tmp, "drain-rate", 1, sc, None, 10)
        assert proc.returncode == 0 and lantern(rows, 10, "L1")["fuel"] == 19
        assert snap(rows, 10)["shades"][0]["state"] == "drain"
        passed.append("shade drain removes one fuel per 10 ticks below fuel 30")

        # Relighting an ever-lit lantern costs 5 motes, sets fuel 100, counts
        # relit_count, increments successful_lights and grants 50 points.
        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 5},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": False, "fuel": 0, "ever_lit": True}]}
        proc, rows = run(tmp, "relight", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        lit = events(rows, "lantern_lit")[0]["data"]
        final = snap(rows, 1)
        assert proc.returncode == 0 and lit["mode"] == "relight" and lit["fuel"] == 100
        assert lit["relit_count"] == 1 and lit["successful_lights"] == 1 and lit["capacity"] == 12
        assert final["score"] == 50 and final["player"]["capacity"] == 12
        assert lantern(rows, 1, "L1")["relit_count"] == 1 and lantern(rows, 1, "L1")["ever_lit"] is True
        passed.append("relight costs 5 motes, scores 50 and increments relit_count")

        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 10},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1]}]}
        proc, rows = run(tmp, "new-light", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        lit = events(rows, "lantern_lit")[0]["data"]
        assert proc.returncode == 0 and lit["mode"] == "new" and snap(rows, 1)["score"] == 100
        assert snap(rows, 1)["player"]["capacity"] == 12
        passed.append("new light costs 10 motes, scores 100 and raises capacity to 12")

        sc = empty() | {"successful_lights": 6}
        proc, rows = run(tmp, "capacity-max", 1, sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["player"]["capacity"] == 20
        proc, rows = run(tmp, "capacity-reset", 2, empty(), None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["player"]["capacity"] == 10
        passed.append("capacity is min(20, 10 + 2*lights) and resets each night")

        # Crossing fuel 30 pushes shades within 7 m to 2 m from the lantern.
        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 10},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 20}],
                        "shades": [{"id": "S1", "pos": [0.5, 0, 1]}]}
        proc, rows = run(tmp, "pushback", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        push = events(rows, "shade_pushed")
        shade = snap(rows, 1)["shades"][0]
        assert proc.returncode == 0 and len(push) == 1 and push[0]["data"]["lantern_id"] == "L1"
        assert push[0]["data"]["pushed_ids"] == ["S1"] and shade["state"] == "wander"
        assert abs(shade["pos"][0] - 2.5) < 0.01 and abs(shade["pos"][2] - 1.0) < 0.01
        assert snap(rows, 1)["score"] == 0 and lantern(rows, 1, "L1")["fuel"] == 100
        passed.append("refuel crossing fuel 30 pushes nearby shades")

        sc = empty() | {"player": {"pos": [0, 0, 0], "carried": 1},
                        "lanterns": [{"id": "L1", "pos": [0, 0, 1], "lit": True, "fuel": 10}],
                        "shades": [{"id": "S1", "pos": [0.5, 0, 1]}]}
        proc, rows = run(tmp, "no-pushback", 1, sc, {"frames": [{"tick": 0, "interact": True}]}, 1)
        assert proc.returncode == 0 and not events(rows, "shade_pushed")
        assert lantern(rows, 1, "L1")["fuel"] == 20
        passed.append("refuel below fuel 30 does not push shades")

        # Dawn threshold is ceil(60% of lanterns); no_flames wins precedence.
        five = {"lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 4)]}
        sc = empty() | five | {"player": {"flames": 2}, "time_left_s": 0.01}
        proc, rows = run(tmp, "dawn-win", 1, sc, None, 1)
        over = events(rows, "game_over")[0]["data"]
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "won"
        assert over["lit_lanterns"] == 3 and over["dawn_threshold"] == 3
        assert over["score"] == 500 + 2 * 50
        passed.append("dawn win needs ceil(60%) and scores 500 + flames*50")

        sc = empty() | {"lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 3)], "time_left_s": 0.01}
        proc, rows = run(tmp, "dawn-loss", 1, sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "lost"
        assert events(rows, "game_over")[0]["data"]["reason"] == "not_enough_lanterns"
        passed.append("dawn below threshold is a loss")

        sc = empty() | five | {"player": {"flames": 1}, "time_left_s": 0.01,
                               "shades": [{"id": "S1", "pos": [0.5, 0, 0]}]}
        proc, rows = run(tmp, "no-flames-first", 1, sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["state"] == "lost"
        assert events(rows, "game_over")[0]["data"]["reason"] == "no_flames"
        passed.append("no_flames takes precedence over the dawn result")

        # No time bonus: two dawn wins with different remaining time score the
        # same; each surviving flame adds 50.
        sc1 = empty() | five | {"player": {"flames": 2}, "time_left_s": 0.01}
        sc2 = empty() | five | {"player": {"flames": 2}, "time_left_s": 0.005}
        _, rows1 = run(tmp, "score-time-a", 1, sc1, None, 1)
        _, rows2 = run(tmp, "score-time-b", 1, sc2, None, 1)
        sc3 = empty() | five | {"player": {"flames": 3}, "time_left_s": 0.01}
        _, rows3 = run(tmp, "score-flames", 1, sc3, None, 1)
        assert snap(rows1, 1)["score"] == snap(rows2, 1)["score"]
        assert snap(rows3, 1)["score"] - snap(rows1, 1)["score"] == 50
        passed.append("scoring has no time bonus and pays per surviving flame")

        sc = empty() | {"color_mode": "colorblind"}
        proc, rows = run(tmp, "colorblind", 1, sc, None, 1)
        assert proc.returncode == 0 and snap(rows, 1)["color_mode"] == "colorblind"
        proc2, rows2 = run(tmp, "default-color", 1, empty(), None, 1)
        assert proc2.returncode == 0 and snap(rows2, 1)["color_mode"] == "default"
        bad = Path(tmp, "bad-color.json")
        bad.write_text('{"color_mode":"neon"}', encoding="utf-8")
        proc3 = subprocess.run([sys.executable, str(GAME), "--headless", "--scenario", str(bad),
                                "--out", str(Path(tmp, "bad-color-out.jsonl"))], capture_output=True, text=True)
        assert proc3.returncode == 2 and "error:" in proc3.stderr
        passed.append("colorblind mode is persisted/echoed and validated")

        sc = empty() | {"player": {"pos": [10, 0, 0]}, "time_left_s": 300,
                        "lanterns": [{"id": "L1", "lit": True}, {"id": "L2", "lit": True, "fuel": 50}],
                        "shades": [{"id": "S1", "pos": [2, 0, 0]}]}
        a_proc, _ = run(tmp, "det-a", 1, sc, None, 120, seed=909, snapshot_every=10)
        b_proc, _ = run(tmp, "det-b", 1, sc, None, 120, seed=909, snapshot_every=10)
        assert a_proc.returncode == b_proc.returncode == 0
        assert Path(tmp, "det-a.jsonl").read_bytes() == Path(tmp, "det-b.jsonl").read_bytes()
        passed.append("fuel/drain simulation is deterministic")

        perf_sc = empty() | {"player": {"pos": [10, 0, 0]}, "time_left_s": 420,
                             "lanterns": [{"id": f"L{i}", "lit": True} for i in range(1, 6)]}
        start = time.perf_counter()
        proc, _ = run(tmp, "perf", 3, perf_sc, None, 21600, snapshot_every=600)
        elapsed = time.perf_counter() - start
        assert proc.returncode == 0 and elapsed <= 30.0, elapsed
        passed.append(f"21,600 Night 3 fuel ticks finish in {elapsed:.2f}s")

    sync = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"],
                          capture_output=True, text=True)
    assert sync.returncode == 0, sync.stderr
    passed.append("godot/shared is in sync with contract and maps")

    print("Phase 3 core checks passed:")
    for item in passed:
        print(f"- {item}")


if __name__ == "__main__":
    main()
