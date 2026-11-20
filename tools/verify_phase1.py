"""Small, reproducible Phase 1 acceptance checks; Python standard library only."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game.py"
sys.path.insert(0, str(ROOT))
from game import T  # noqa: E402


def run(tmp, name, scenario, inputs, ticks=4, seed=17):
    scenario_path = Path(tmp) / f"{name}-scenario.json"
    inputs_path = Path(tmp) / f"{name}-inputs.json"
    out_path = Path(tmp) / f"{name}.jsonl"
    if scenario is not None: scenario_path.write_text(json.dumps(scenario), encoding="utf-8")
    if inputs is not None: inputs_path.write_text(json.dumps(inputs), encoding="utf-8")
    cmd = [sys.executable, str(GAME), "--headless", "--seed", str(seed), "--ticks", str(ticks), "--out", str(out_path), "--snapshot-every", "1"]
    if scenario is not None: cmd += ["--scenario", str(scenario_path)]
    if inputs is not None: cmd += ["--inputs", str(inputs_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc, [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()] if out_path.exists() else []


def main():
    passed = []
    assert "tkinter" not in sys.modules
    passed.append("headless simulation does not import Tkinter")
    contract=json.loads((ROOT/"game.contract.json").read_text(encoding="utf-8"))
    assert contract["contract_version"]=="1.1" and contract["tuning"]==T
    passed.append("contract tuning matches simulation constants")
    with tempfile.TemporaryDirectory() as tmp:
        empty = {"random_motes": False, "random_shades": False, "motes": [[0,0,0] for _ in range(5)], "shades": [],
                 "lanterns": [{"id":"L1", "pos":[9.5,0,0]}]}
        frames=[]
        for tick in (0,2,4,6,8,10):
            frames.extend([{"tick":tick,"interact":True},{"tick":tick+1,"interact":False}])
        frames.extend([{"tick":12,"move":[1,0]},{"tick":108,"move":[0,0]},{"tick":109,"interact":True},{"tick":110,"interact":False}])
        p, rows = run(tmp,"pickup-deposit",empty,{"frames":frames},111)
        assert p.returncode == 0 and any(r.get("name")=="mote_picked" for r in rows) and any(r.get("name")=="lantern_lit" for r in rows), (p.stderr, [r for r in rows if r.get("type")=="event"])
        assert rows[-1]["score"] == 150 and rows[-1]["state"] == "playing"
        passed.append("pickup, deposit and lantern lighting")

        sc={"player":{"pos":[0,0,0],"carried":2},"random_motes":False,"random_shades":False,"motes":[],"shades":[{"id":"Sx","pos":[4,0,0]}]}
        p,rows=run(tmp,"pulse",sc,{"frames":[{"tick":0,"pulse":True}]},1)
        assert p.returncode==0 and any(r.get("name")=="pulse" and r["data"]["stunned_ids"]==["Sx"] for r in rows)
        snap=next(r for r in rows if r.get("type")=="snapshot" and r.get("tick")==1)
        assert snap["score"]==25 and snap["shades"][0]["state"]=="stunned" and snap["player"]["carried"]==1
        passed.append("pulse cost, stun and score")

        sc={"player":{"pos":[0,0,0],"carried":4},"random_motes":False,"random_shades":False,"motes":[],"shades":[{"pos":[0.5,0,0]}]}
        p,rows=run(tmp,"hit",sc,None,1)
        hit=next(r for r in rows if r.get("name")=="player_hit")
        assert p.returncode==0 and hit["data"]=={"by":"shade","flames":2,"dropped":2}
        passed.append("shade collision, health and dropped motes")

        sc={"player":{"pos":[T["island_radius_m"]+1,0,0]},"random_motes":False,"random_shades":False,"motes":[],"shades":[]}
        p,rows=run(tmp,"fall",sc,{"frames":[{"tick":0,"move":[1,0]}]},60)
        assert p.returncode==0 and any(r.get("name")=="player_hit" and r["data"]["by"]=="fall" for r in rows)
        passed.append("island edge fall damage")

        sc={"player":{"flames":1},"random_motes":False,"random_shades":False,"motes":[],"shades":[{"pos":[0.5,0,0]}]}
        p,rows=run(tmp,"lost",sc,None,2)
        assert p.returncode==0 and rows[-1]["state"]=="lost" and rows[-1]["score"]==0
        passed.append("loss at zero flames")

        sc={"random_motes":False,"random_shades":False,"motes":[],"shades":[],"time_left_s":0.01}
        p,rows=run(tmp,"dawn",sc,None,1)
        assert p.returncode==0 and rows[-1]["state"]=="lost" and any(r.get("name")=="game_over" and r["data"]["reason"]=="dawn" for r in rows)
        passed.append("dawn timeout")

        sc={"player":{"flames":2},"random_motes":False,"random_shades":False,"motes":[],"shades":[],
            "lanterns":[{"id":f"L{i}","lit":True} for i in range(1,6)]}
        p,rows=run(tmp,"win",sc,None,1)
        assert p.returncode==0 and rows[-1]["state"]=="won" and rows[-1]["score"]==399
        passed.append("win and end bonus")

        a,_=run(tmp,"seed-a",None,None,60,909); first=Path(tmp,"seed-a.jsonl").read_bytes()
        b,_=run(tmp,"seed-b",None,None,60,909); second=Path(tmp,"seed-b.jsonl").read_bytes()
        assert a.returncode==b.returncode==0 and first==second
        passed.append("same-seed deterministic JSONL output")

        bad=Path(tmp,"bad-input.json"); bad.write_text('{"frames":[{"tick":1},{"tick":1}]}',encoding="utf-8")
        proc=subprocess.run([sys.executable,str(GAME),"--headless","--inputs",str(bad),"--out",str(Path(tmp,"bad.jsonl"))],capture_output=True,text=True)
        assert proc.returncode==2 and "error:" in proc.stderr
        bad_scenario=Path(tmp,"bad-scenario.json"); bad_scenario.write_text('{"player":null}',encoding="utf-8")
        proc2=subprocess.run([sys.executable,str(GAME),"--headless","--scenario",str(bad_scenario),"--out",str(Path(tmp,"bad-scenario-out.jsonl"))],capture_output=True,text=True)
        assert proc2.returncode==2 and "error:" in proc2.stderr
        passed.append("invalid input and scenario exit with code 2")
    print("Phase 1 core checks passed:")
    for item in passed: print(f"- {item}")


if __name__=="__main__": main()
