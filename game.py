#!/usr/bin/env python3
"""Đảo Đèn Lồng — deterministic 60 Hz simulation and contract runner."""
import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

HZ = 60
ROOT = Path(__file__).resolve().parent
T = {
    "player_speed": 6.5, "carry_capacity": 10,
    "capacity_per_light": 2, "capacity_max": 20,
    "new_light_cost": 10, "relight_cost": 5,
    "lantern_fuel_max": 100, "refuel_fuel_per_mote": 10,
    "ambient_drain_per_s": 1, "shade_drain_per_s": 5,
    "shade_drain_radius_m": 2.0, "shade_chase_radius_m": 10.0,
    "safe_fuel_threshold": 30,
    "dawn_lantern_ratio": 0.6,
    "fuel_push_radius_m": 7.0, "fuel_push_m": 2.0,
    "lantern_count_night1": 5, "lantern_count_night2": 6, "lantern_count_night3": 7,
    "pickup_radius": 1.2, "interact_radius": 2.0, "pulse_cost": 1, "pulse_radius": 7.0,
    "night1_duration_s": 300, "night2_duration_s": 360, "night3_duration_s": 420,
    "flames": 3, "invuln_s": 2.0, "hit_drop_ratio": 0.5,
    "pulse_stun_s": 2.0, "pulse_push_m": 2.0, "pulse_cooldown_s": 3.0,
    "safe_radius": 3.0, "shade_speed": 2.5, "shade_hit_radius": 1.0,
    "fall_enabled": True,
    "island_radius_m": 40.0, "jump_velocity_m_s": 7.0, "gravity_m_s2": 18.0,
    "lantern_ring_radius_m": 25.0, "initial_mote_count": 40,
    "initial_mote_spawn_radius_m": 36.0, "initial_shade_count": 3,
    "initial_shade_spawn_radius_m": 32.0,
    "dash_speed_m_s": 12.0, "dash_duration_s": 0.2, "dash_cooldown_s": 1.5,
    "glide_fall_speed_m_s": 2.0,
    "lost_wisp_speed_m_s": 2.0, "lost_wisp_radius_m": 2.0, "lost_wisp_push_m_s": 3.0,
    "wind_charm_radius_m": 1.2, "wind_charm_duration_s": 8.0,
    "strong_wind_speed_m_s": 2.5, "bell_tower_radius_m": 3.0,
    "step_height_m": 0.8, "fall_y_m": -8.0,
    "night2_shade_speed": 2.8, "night3_shade_speed": 3.1,
    "night2_lost_wisp_speed_m_s": 2.0, "night3_lost_wisp_speed_m_s": 2.6,
    "score": {"per_mote": 10, "per_lantern": 100, "per_relight": 50, "per_stun": 25, "per_flame_left": 50, "dawn_bonus": 500},
}


def dist_xz(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def load_json(path, kind):
    try:
        with open(path, encoding="utf-8-sig") as f:
            value = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"cannot read {kind}: {e}") from e
    return value


def load_map(night):
    path = ROOT / "shared" / "maps" / f"night{night}.json"
    value = load_json(path, f"map night {night}")
    if not isinstance(value, dict):
        raise ValueError(f"map night {night} must be an object")
    for key in ("platforms", "lanterns"):
        if not isinstance(value.get(key), list):
            raise ValueError(f"map night {night}.{key} must be an array")
    return value


def load_inputs(path):
    if not path:
        return []
    obj = load_json(path, "inputs")
    if not isinstance(obj, dict) or not isinstance(obj.get("frames"), list):
        raise ValueError("inputs.frames must be an array")
    frames = []
    last = -1
    for f in obj["frames"]:
        if not isinstance(f, dict) or isinstance(f.get("tick"), bool) or not isinstance(f.get("tick"), int) or f["tick"] < 0 or f["tick"] <= last:
            raise ValueError("input ticks must be nonnegative and increase strictly")
        last = f["tick"]
        for b in ("jump", "interact", "pulse", "dash", "glide", "pause"):
            if b in f and not isinstance(f[b], bool):
                raise ValueError(f"{b} must be boolean")
        if "move" in f and (not isinstance(f["move"], list) or len(f["move"]) != 2 or any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or not -1 <= v <= 1 for v in f["move"])):
            raise ValueError("move components must be finite and in [-1,1]")
        if "cam_yaw_deg" in f and (isinstance(f["cam_yaw_deg"], bool) or not isinstance(f["cam_yaw_deg"], (int, float)) or not math.isfinite(f["cam_yaw_deg"])):
            raise ValueError("cam_yaw_deg must be finite numeric")
        frames.append(f)
    return frames


class Game:
    def __init__(self, seed=1, scenario=None, night=1):
        self.night = night
        self.map = load_map(night)
        self.rng = random.Random(seed)
        self.tick = 0
        self.sim_tick = 0
        self.paused = False
        self.state = "playing"
        self.result = None
        self.initial_time_left = float(self.map.get("duration_s", T[f"night{night}_duration_s"]))
        self.score = 0
        self.carried = 0
        self.successful_lights = 0
        self.color_mode = "default"
        self.flames = T["flames"]
        self.pos = [float(x) for x in self.map.get("player_spawn", [0, 0, 0])]
        self.vy = 0.0
        self.on_ground = True
        self.invuln = 0
        self.pulse_cd = 0
        self.dash_cd = 0
        self.dash_t = 0
        self.dash_dir = [0.0, 0.0]
        self.wind_shield_s = 0.0
        self.safe_pos = list(self.pos)
        self.events = []
        self.motes = []
        self.shades = []
        self.wisps = []
        self.charms = []
        self.lanterns = []
        self.mote_serial = 0
        self.shade_serial = 0
        self.wisp_serial = 0
        self.charm_serial = 0
        self.random_motes = True
        self.random_shades = True
        self.random_wisps = True
        self.random_charms = True
        self._build_from_map()
        if scenario:
            self._scenario(scenario)
            self.events.clear()

    def _build_from_map(self):
        for item in self.map["lanterns"]:
            self.lanterns.append({
                "id": str(item["id"]),
                "pos": [float(x) for x in item["pos"]],
                "lit": False,
                "fuel": 0,
                "deposited": 0,
                "ever_lit": False,
                "relit_count": 0,
                "drain_acc": 0,
            })
        for item in self.map.get("shade_spawn", []):
            shade_id = str(item.get("id", f"S{self.shade_serial + 1}"))
            self._shade(item["pos"], shade_id)
            self.event("shade_spawned", {"id": shade_id})
        for item in self.map.get("wisp_spawn", []):
            self.wisps.append({"id": str(item.get("id", f"W{self.wisp_serial + 1}")), "pos": [float(x) for x in item["pos"]]})
        for item in self.map.get("charm_spawn", []):
            self.charms.append({"id": str(item.get("id", f"C{self.charm_serial + 1}")), "pos": [float(x) for x in item["pos"]], "collected": False})
        spawn = self.map.get("mote_spawn", {})
        count = int(spawn.get("count", T["initial_mote_count"]))
        center = spawn.get("center", [0, 0])
        radius = float(spawn.get("radius_m", T["initial_mote_spawn_radius_m"]))
        for _ in range(count):
            self._mote(self._random_surface_point(center, radius))

    def _random_surface_point(self, center, radius):
        for _ in range(100):
            angle = self.rng.random() * 2 * math.pi
            distance = math.sqrt(self.rng.random()) * radius
            x = center[0] + distance * math.cos(angle)
            z = center[1] + distance * math.sin(angle)
            height = self.surface_height(x, z)
            if height is not None:
                return [x, height, z]
        return [float(center[0]), 0.0, float(center[1])]

    def _mote(self, p):
        self.mote_serial += 1
        self.motes.append({"id": f"M{self.mote_serial}", "pos": [float(x) for x in p]})

    def _shade(self, p, ident=None):
        self.shade_serial += 1
        self.shades.append({
            "id": ident or f"S{self.shade_serial}",
            "pos": [float(x) for x in p],
            "state": "wander",
            "stun": 0,
            "drain_target": None,
        })

    def _wisp(self, p, ident=None):
        self.wisp_serial += 1
        self.wisps.append({"id": ident or f"W{self.wisp_serial}", "pos": [float(x) for x in p]})

    def _charm(self, p, ident=None):
        self.charm_serial += 1
        self.charms.append({"id": ident or f"C{self.charm_serial}", "pos": [float(x) for x in p], "collected": False})

    def surface_height(self, x, z):
        best = None
        for platform in self.map["platforms"]:
            kind = platform.get("type")
            height = None
            if kind == "circle":
                cx, cz = platform["center"]
                if math.hypot(x - cx, z - cz) <= float(platform["radius_m"]):
                    height = float(platform.get("height_m", 0.0))
            elif kind == "rect":
                min_x, min_z = platform["min"]
                max_x, max_z = platform["max"]
                if min_x <= x <= max_x and min_z <= z <= max_z:
                    height = float(platform.get("height_m", 0.0))
            elif kind == "ramp":
                min_x, min_z = platform["min"]
                max_x, max_z = platform["max"]
                if min_x <= x <= max_x and min_z <= z <= max_z:
                    low = float(platform.get("height_min_m", 0.0))
                    high = float(platform.get("height_max_m", low))
                    if platform.get("axis") == "x":
                        t = (x - min_x) / (max_x - min_x) if max_x != min_x else 0.0
                    else:
                        t = (z - min_z) / (max_z - min_z) if max_z != min_z else 0.0
                    height = low + (high - low) * t
            elif kind == "jump_pad":
                cx, cz = platform["center"]
                if math.hypot(x - cx, z - cz) <= float(platform["radius_m"]):
                    height = float(platform.get("height_m", 0.0))
            if height is not None and (best is None or height > best):
                best = height
        return best

    def _jump_pad_at(self, x, z, y):
        for platform in self.map["platforms"]:
            if platform.get("type") != "jump_pad":
                continue
            cx, cz = platform["center"]
            height = float(platform.get("height_m", 0.0))
            if math.hypot(x - cx, z - cz) <= float(platform["radius_m"]) and abs(y - height) <= T["step_height_m"]:
                return platform
        return None

    def _in_wind(self, pos):
        for zone in self.map.get("wind_zones", []):
            min_x, min_z = zone["min"]
            max_x, max_z = zone["max"]
            if min_x <= pos[0] <= max_x and min_z <= pos[2] <= max_z:
                return zone
        return None

    def _scenario(self, sc):
        if not isinstance(sc, dict):
            raise ValueError("scenario must be a JSON object")
        pl = sc.get("player", {})
        if not isinstance(pl, dict):
            raise ValueError("player must be an object")
        self.pos = self._vec(pl.get("pos", [0, 0, 0]), "player.pos")
        self.carried = self._integer(pl.get("carried", 0), "player.carried", 0)
        self.flames = self._integer(pl.get("flames", T["flames"]), "player.flames", 0)
        for flag in ("random_motes", "random_shades", "random_wisps", "random_charms", "paused"):
            if flag in sc and not isinstance(sc[flag], bool):
                raise ValueError(f"{flag} must be boolean")
        self.random_motes = bool(sc.get("random_motes", True))
        self.random_shades = bool(sc.get("random_shades", True))
        self.random_wisps = bool(sc.get("random_wisps", True))
        self.random_charms = bool(sc.get("random_charms", True))
        self.paused = bool(sc.get("paused", False))
        if "successful_lights" in sc:
            self.successful_lights = self._integer(sc["successful_lights"], "successful_lights", 0)
        if "color_mode" in sc:
            if sc["color_mode"] not in ("default", "colorblind"):
                raise ValueError("color_mode must be 'default' or 'colorblind'")
            self.color_mode = str(sc["color_mode"])
        if not self.random_motes and "motes" not in sc:
            self.motes = []
        if not self.random_shades and "shades" not in sc:
            self.shades = []
        if not self.random_wisps and "wisps" not in sc:
            self.wisps = []
        if not self.random_charms and "charms" not in sc:
            self.charms = []
        if "motes" in sc:
            if not isinstance(sc["motes"], list):
                raise ValueError("motes must be an array")
            self.motes = []
            self.mote_serial = 0
            for p in sc["motes"]:
                self._mote(self._vec(p, "mote"))
        if "shades" in sc:
            if not isinstance(sc["shades"], list):
                raise ValueError("shades must be an array")
            self.shades = []
            self.shade_serial = 0
            for s in sc["shades"]:
                if not isinstance(s, dict):
                    raise ValueError("shade must be an object")
                shade_id = str(s["id"]) if "id" in s else f"S{self.shade_serial + 1}"
                self._shade(self._vec(s.get("pos", [0, 0, 0]), "shade.pos"), shade_id)
                self.event("shade_spawned", {"id": shade_id})
        if "wisps" in sc:
            if not isinstance(sc["wisps"], list):
                raise ValueError("wisps must be an array")
            self.wisps = []
            self.wisp_serial = 0
            for w in sc["wisps"]:
                if not isinstance(w, dict):
                    raise ValueError("wisp must be an object")
                self._wisp(self._vec(w.get("pos", [0, 0, 0]), "wisp.pos"), str(w["id"]) if "id" in w else None)
        if "charms" in sc:
            if not isinstance(sc["charms"], list):
                raise ValueError("charms must be an array")
            self.charms = []
            self.charm_serial = 0
            for c in sc["charms"]:
                if not isinstance(c, dict):
                    raise ValueError("charm must be an object")
                self._charm(self._vec(c.get("pos", [0, 0, 0]), "charm.pos"), str(c["id"]) if "id" in c else None)
        if "lanterns" in sc:
            if not isinstance(sc["lanterns"], list):
                raise ValueError("lanterns must be an array")
            byid = {l["id"]: l for l in self.lanterns}
            for item in sc["lanterns"]:
                if not isinstance(item, dict) or item.get("id") not in byid:
                    raise ValueError(f"lantern id must be one of {sorted(byid)}")
                lantern = byid[item["id"]]
                if "pos" in item:
                    lantern["pos"] = self._vec(item["pos"], "lantern.pos")
                if "lit" in item and not isinstance(item["lit"], bool):
                    raise ValueError("lantern lit must be boolean")
                if "ever_lit" in item and not isinstance(item["ever_lit"], bool):
                    raise ValueError("lantern ever_lit must be boolean")
                if "fuel" in item and "deposited" in item:
                    if item["fuel"] != item["deposited"]:
                        raise ValueError("lantern fuel and deposited must match")
                raw_fuel = item.get("fuel", item.get("deposited"))
                if raw_fuel is None:
                    fuel = T["lantern_fuel_max"] if item.get("lit", False) else 0
                else:
                    fuel = self._integer(raw_fuel, "lantern fuel", 0)
                    if fuel > T["lantern_fuel_max"]:
                        raise ValueError(f"lantern fuel must be <= {T['lantern_fuel_max']}")
                lit = bool(item.get("lit", fuel > 0))
                if lit and fuel <= 0:
                    raise ValueError("a lit lantern needs fuel > 0")
                if not lit and fuel > 0:
                    raise ValueError("an unlit lantern must have fuel 0")
                relit_count = self._integer(item.get("relit_count", 0), "lantern relit_count", 0)
                ever_lit = bool(item.get("ever_lit", False)) or lit or fuel > 0 or relit_count > 0
                lantern.update({
                    "fuel": fuel,
                    "deposited": fuel,
                    "lit": lit,
                    "ever_lit": ever_lit,
                    "relit_count": relit_count,
                    "drain_acc": 0,
                })
        if "time_left_s" in sc:
            if isinstance(sc["time_left_s"], bool) or not isinstance(sc["time_left_s"], (int, float)):
                raise ValueError("time_left_s must be numeric")
            self.initial_time_left = float(sc["time_left_s"])
            if not math.isfinite(self.initial_time_left) or self.initial_time_left < 0:
                raise ValueError("time_left_s must be nonnegative")
        spawn = self.map.get("player_spawn", [0, 0, 0])
        self.safe_pos = [float(spawn[0]), float(spawn[1]), float(spawn[2])]
        if self.flames == 0:
            self.finish("lost", "no_flames")

    @staticmethod
    def _integer(n, name, minimum):
        if isinstance(n, bool) or not isinstance(n, int) or n < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
        return n

    @staticmethod
    def _vec(p, name):
        if not isinstance(p, list) or len(p) != 3 or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in p):
            raise ValueError(f"{name} must be a finite [x,y,z] array")
        return [float(x) for x in p]

    def event(self, name, data=None):
        self.events.append({"type": "event", "tick": self.tick, "name": name, "data": data or {}})

    @property
    def time_left(self):
        return max(0.0, self.initial_time_left - self.sim_tick / HZ)

    @property
    def capacity(self):
        return min(T["capacity_max"], T["carry_capacity"] + T["capacity_per_light"] * self.successful_lights)

    @property
    def dawn_threshold(self):
        return math.ceil(T["dawn_lantern_ratio"] * len(self.lanterns))

    @property
    def lit_count(self):
        return sum(1 for lantern in self.lanterns if lantern["lit"])

    def _try_move(self, x, z):
        height = self.surface_height(x, z)
        return height is None or height <= self.pos[1] + T["step_height_m"]

    def _fall(self):
        self.flames = max(0, self.flames - 1)
        dropped = math.floor(self.carried * T["hit_drop_ratio"])
        self.carried -= dropped
        self.pos = list(self.safe_pos)
        self.vy = 0.0
        self.on_ground = True
        self.invuln = round(T["invuln_s"] * HZ)
        self.event("player_hit", {"by": "fall", "flames": self.flames, "dropped": dropped})
        if self.flames == 0:
            self.finish("lost", "no_flames")

    def _lantern_can_receive(self, lantern, carried):
        if lantern["lit"]:
            if lantern["fuel"] >= T["lantern_fuel_max"]:
                return False
            needed = math.ceil((T["lantern_fuel_max"] - lantern["fuel"]) / T["refuel_fuel_per_mote"])
            return min(carried, needed) > 0
        cost = T["relight_cost"] if lantern["ever_lit"] else T["new_light_cost"]
        return carried >= cost

    def _receive_lantern(self, lantern):
        before_fuel = lantern["fuel"]
        if lantern["lit"]:
            needed = math.ceil((T["lantern_fuel_max"] - before_fuel) / T["refuel_fuel_per_mote"])
            used = min(self.carried, needed)
            if used <= 0:
                return
            self.carried -= used
            lantern["fuel"] = min(T["lantern_fuel_max"], before_fuel + used * T["refuel_fuel_per_mote"])
            lantern["deposited"] = lantern["fuel"]
            self.event("deposit", {
                "lantern_id": lantern["id"],
                "amount": used,
                "fuel": lantern["fuel"],
                "deposited": lantern["deposited"],
                "carried": self.carried,
            })
        else:
            mode = "relight" if lantern["ever_lit"] else "new"
            cost = T["relight_cost"] if mode == "relight" else T["new_light_cost"]
            if self.carried < cost:
                return
            self.carried -= cost
            lantern["fuel"] = T["lantern_fuel_max"]
            lantern["deposited"] = lantern["fuel"]
            lantern["lit"] = True
            lantern["ever_lit"] = True
            lantern["drain_acc"] = 0
            if mode == "relight":
                lantern["relit_count"] += 1
            self.successful_lights += 1
            self.score += T["score"]["per_relight"] if mode == "relight" else T["score"]["per_lantern"]
            self.event("lantern_lit", {
                "lantern_id": lantern["id"],
                "mode": mode,
                "fuel": lantern["fuel"],
                "successful_lights": self.successful_lights,
                "capacity": self.capacity,
                "relit_count": lantern["relit_count"],
            })
        if before_fuel < T["safe_fuel_threshold"] <= lantern["fuel"]:
            self._push_shades_from_lantern(lantern)

    def _push_shades_from_lantern(self, lantern):
        pushed = []
        for shade in self.shades:
            if dist_xz(shade["pos"], lantern["pos"]) > T["fuel_push_radius_m"]:
                continue
            dx, dz = shade["pos"][0] - lantern["pos"][0], shade["pos"][2] - lantern["pos"][2]
            length = math.hypot(dx, dz)
            if length <= 1e-9:
                dx, dz, length = 1.0, 0.0, 1.0
            shade["pos"][0] += dx / length * T["fuel_push_m"]
            shade["pos"][2] += dz / length * T["fuel_push_m"]
            shade["state"] = "wander"
            shade["stun"] = 0
            shade["drain_target"] = None
            pushed.append(shade["id"])
        if pushed:
            self.event("shade_pushed", {"lantern_id": lantern["id"], "pushed_ids": pushed})

    def _wander_target(self, shade):
        lit = [l for l in self.lanterns if l["lit"] and l["fuel"] > 0]
        if not lit:
            return None
        return min(lit, key=lambda l: (l["fuel"], dist_xz(shade["pos"], l["pos"]), l["id"]))

    def _drain_lanterns(self):
        drain_units = {}
        for lantern in self.lanterns:
            if lantern["lit"]:
                drain_units[lantern["id"]] = drain_units.get(lantern["id"], 0) + T["ambient_drain_per_s"]
        for shade in self.shades:
            target_id = shade.get("drain_target")
            if shade["state"] == "drain" and target_id is not None:
                drain_units[target_id] = drain_units.get(target_id, 0) + T["shade_drain_per_s"]
        for lantern in sorted(self.lanterns, key=lambda l: l["id"]):
            if not lantern["lit"]:
                continue
            units = drain_units.get(lantern["id"], 0)
            if units <= 0:
                continue
            lantern["drain_acc"] += units
            while lantern["drain_acc"] >= HZ and lantern["fuel"] > 0:
                lantern["drain_acc"] -= HZ
                lantern["fuel"] -= 1
            lantern["deposited"] = lantern["fuel"]
            if lantern["fuel"] <= 0:
                lantern["fuel"] = 0
                lantern["lit"] = False
                lantern["deposited"] = 0
                lantern["drain_acc"] = 0
                self.event("lantern_out", {
                    "lantern_id": lantern["id"],
                    "fuel": 0,
                    "ever_lit": lantern["ever_lit"],
                    "relit_count": lantern["relit_count"],
                })

    def step(self, inp):
        if self.state != "playing":
            return
        self.tick += 1
        if "pause" in inp:
            if not isinstance(inp["pause"], bool):
                raise ValueError("pause must be boolean")
            self.paused = inp["pause"]
        if self.paused:
            return
        self.sim_tick += 1
        self.invuln = max(0, self.invuln - 1)
        self.pulse_cd = max(0, self.pulse_cd - 1)
        self.dash_cd = max(0, self.dash_cd - 1)
        self.wind_shield_s = max(0.0, self.wind_shield_s - 1 / HZ)
        dt = 1 / HZ

        mv = inp.get("move", [0, 0])
        yaw = math.radians(float(inp.get("cam_yaw_deg", 0)))
        x, z = float(mv[0]), float(mv[1])
        mag = math.hypot(x, z)
        if mag > 1:
            x, z = x / mag, z / mag
        wx, wz = x * math.cos(yaw) + z * math.sin(yaw), -x * math.sin(yaw) + z * math.cos(yaw)

        if inp.get("dash") and not inp.get("_dash_prev") and self.dash_cd == 0 and self.on_ground:
            if mag > 0:
                length = math.hypot(wx, wz) or 1.0
                self.dash_dir = [wx / length, wz / length]
            else:
                self.dash_dir = [math.sin(yaw), math.cos(yaw)]
            self.dash_t = round(T["dash_duration_s"] * HZ)
            self.dash_cd = round(T["dash_cooldown_s"] * HZ)

        if self.dash_t > 0:
            self.dash_t -= 1
            vx, vz = self.dash_dir[0] * T["dash_speed_m_s"], self.dash_dir[1] * T["dash_speed_m_s"]
        else:
            vx, vz = wx * T["player_speed"], wz * T["player_speed"]

        nx, nz = self.pos[0] + vx * dt, self.pos[2] + vz * dt
        if self._try_move(nx, nz):
            self.pos[0], self.pos[2] = nx, nz
        else:
            if self._try_move(nx, self.pos[2]):
                self.pos[0] = nx
            if self._try_move(self.pos[0], nz):
                self.pos[2] = nz

        zone = self._in_wind(self.pos)
        if zone and self.wind_shield_s <= 0:
            push = zone.get("push", [0, 0, 0])
            speed = T["strong_wind_speed_m_s"]
            self.pos[0] += push[0] * speed * dt
            self.pos[2] += push[2] * speed * dt

        if inp.get("jump") and not inp.get("_jump_prev") and self.on_ground:
            self.vy = T["jump_velocity_m_s"]
            self.on_ground = False

        height = self.surface_height(self.pos[0], self.pos[2])
        if self.on_ground:
            if height is None:
                self.on_ground = False
            elif abs(height - self.pos[1]) <= T["step_height_m"]:
                self.pos[1] = height
            else:
                self.on_ground = False

        if not self.on_ground:
            self.pos[1] += self.vy * dt
            self.vy -= T["gravity_m_s2"] * dt
            if inp.get("glide") and self.vy < -T["glide_fall_speed_m_s"]:
                self.vy = -T["glide_fall_speed_m_s"]
            height = self.surface_height(self.pos[0], self.pos[2])
            if height is not None and self.pos[1] <= height and self.vy <= 0:
                self.pos[1] = height
                self.vy = 0.0
                self.on_ground = True

        if self.on_ground:
            pad = self._jump_pad_at(self.pos[0], self.pos[2], self.pos[1])
            if pad:
                self.vy = float(pad["launch_velocity_m_s"])
                self.on_ground = False
            if not self._in_wind(self.pos):
                self.safe_pos = list(self.pos)

        if inp.get("interact") and not inp.get("_interact_prev"):
            receiving = [
                l for l in self.lanterns
                if dist_xz(self.pos, l["pos"]) <= T["interact_radius"] and self._lantern_can_receive(l, self.carried)
            ]
            if receiving:
                lantern = min(receiving, key=lambda a: (dist_xz(self.pos, a["pos"]), a["id"]))
                self._receive_lantern(lantern)
            else:
                choices = [m for m in self.motes if dist_xz(self.pos, m["pos"]) <= T["pickup_radius"]]
                if choices and self.carried < self.capacity:
                    mote = min(choices, key=lambda a: dist_xz(self.pos, a["pos"]))
                    self.motes.remove(mote)
                    self.carried += 1
                    self.score += T["score"]["per_mote"]
                    self.event("mote_picked", {"carried": self.carried})

        if inp.get("pulse") and not inp.get("_pulse_prev") and self.pulse_cd == 0 and self.carried >= T["pulse_cost"]:
            self.carried -= T["pulse_cost"]
            self.pulse_cd = round(T["pulse_cooldown_s"] * HZ)
            hit = []
            for shade in self.shades:
                if shade["state"] != "stunned" and dist_xz(self.pos, shade["pos"]) <= T["pulse_radius"]:
                    dx, dz = shade["pos"][0] - self.pos[0], shade["pos"][2] - self.pos[2]
                    length = math.hypot(dx, dz) or 1.0
                    shade["pos"][0] += dx / length * T["pulse_push_m"]
                    shade["pos"][2] += dz / length * T["pulse_push_m"]
                    shade["state"] = "stunned"
                    shade["stun"] = round(T["pulse_stun_s"] * HZ)
                    shade["drain_target"] = None
                    hit.append(shade["id"])
                    self.score += T["score"]["per_stun"]
            self.event("pulse", {"stunned_ids": hit})

        for charm in self.charms:
            if not charm["collected"] and dist_xz(self.pos, charm["pos"]) <= T["wind_charm_radius_m"]:
                charm["collected"] = True
                self.wind_shield_s = T["wind_charm_duration_s"]
                self.event("charm_picked", {"id": charm["id"], "duration_s": self.wind_shield_s})

        wisp_speed = T.get(f"night{self.night}_lost_wisp_speed_m_s", T["lost_wisp_speed_m_s"])
        for wisp in self.wisps:
            targets = [l for l in self.lanterns if not l["lit"]]
            if targets:
                target = min(targets, key=lambda a: dist_xz(wisp["pos"], a["pos"]))
                dx, dz = target["pos"][0] - wisp["pos"][0], target["pos"][2] - wisp["pos"][2]
                length = math.hypot(dx, dz)
                if length > 0.05:
                    move = min(length, wisp_speed * dt)
                    wisp["pos"][0] += dx / length * move
                    wisp["pos"][2] += dz / length * move
            if self.wind_shield_s <= 0 and dist_xz(self.pos, wisp["pos"]) <= T["lost_wisp_radius_m"]:
                dx, dz = self.pos[0] - wisp["pos"][0], self.pos[2] - wisp["pos"][2]
                length = math.hypot(dx, dz) or 1.0
                self.pos[0] += dx / length * T["lost_wisp_push_m_s"] * dt
                self.pos[2] += dz / length * T["lost_wisp_push_m_s"] * dt

        shade_speed = T.get(f"night{self.night}_shade_speed", T["shade_speed"])
        for shade in self.shades:
            shade["drain_target"] = None
            if shade["state"] == "stunned":
                shade["stun"] -= 1
                if shade["stun"] <= 0:
                    shade["state"] = "wander"
                continue
            safe = any(
                l["lit"] and l["fuel"] >= T["safe_fuel_threshold"] and dist_xz(shade["pos"], l["pos"]) <= T["safe_radius"]
                for l in self.lanterns
            )
            if safe:
                shade["state"] = "wander"
                continue
            player_distance = dist_xz(shade["pos"], self.pos)
            if player_distance <= T["shade_chase_radius_m"]:
                shade["state"] = "chase"
                dx, dz = self.pos[0] - shade["pos"][0], self.pos[2] - shade["pos"][2]
                distance = math.hypot(dx, dz)
                if distance > 0.05:
                    move = min(distance, shade_speed * dt)
                    shade["pos"][0] += dx / distance * move
                    shade["pos"][2] += dz / distance * move
            else:
                drain_target = None
                for lantern in self.lanterns:
                    if not lantern["lit"]:
                        continue
                    if dist_xz(shade["pos"], lantern["pos"]) > T["shade_drain_radius_m"]:
                        continue
                    if drain_target is None or (dist_xz(shade["pos"], lantern["pos"]), lantern["id"]) < (dist_xz(shade["pos"], drain_target["pos"]), drain_target["id"]):
                        drain_target = lantern
                if drain_target is not None:
                    shade["state"] = "drain"
                    shade["drain_target"] = drain_target["id"]
                else:
                    shade["state"] = "wander"
                    target = self._wander_target(shade)
                    if target is not None:
                        dx, dz = target["pos"][0] - shade["pos"][0], target["pos"][2] - shade["pos"][2]
                        distance = math.hypot(dx, dz)
                        if distance > T["shade_drain_radius_m"] + 0.01:
                            move = min(distance - T["shade_drain_radius_m"], shade_speed * dt)
                            shade["pos"][0] += dx / distance * move
                            shade["pos"][2] += dz / distance * move
            if shade["state"] == "chase" and dist_xz(shade["pos"], self.pos) <= T["shade_hit_radius"] and self.invuln == 0:
                self.flames = max(0, self.flames - 1)
                dropped = math.floor(self.carried * T["hit_drop_ratio"])
                self.carried -= dropped
                self.invuln = round(T["invuln_s"] * HZ)
                self.event("player_hit", {"by": "shade", "flames": self.flames, "dropped": dropped})
                if self.flames == 0:
                    self.finish("lost", "no_flames")
                break

        if self.state == "playing":
            self._drain_lanterns()
        if self.state == "playing" and self.pos[1] < T["fall_y_m"] and self.invuln == 0:
            self._fall()
        if self.state == "playing" and self.flames == 0:
            self.finish("lost", "no_flames")
        if self.state == "playing" and self.time_left <= 1e-9:
            if self.lit_count >= self.dawn_threshold:
                self.finish("won", "dawn")
            else:
                self.finish("lost", "not_enough_lanterns")

    def finish(self, state, reason):
        self.state, self.result = state, reason
        if state == "won":
            self.score += T["score"]["dawn_bonus"] + self.flames * T["score"]["per_flame_left"]
        self.event("game_over", {
            "result": state,
            "reason": reason,
            "lit_lanterns": self.lit_count,
            "dawn_threshold": self.dawn_threshold,
            "score": self.score,
        })

    def snapshot(self):
        return {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "paused": self.paused,
            "night": self.night,
            "state": self.state,
            "time_left_s": round(self.time_left, 3),
            "score": self.score,
            "color_mode": self.color_mode,
            "lit_lanterns": self.lit_count,
            "dawn_threshold": self.dawn_threshold,
            "player": {
                "pos": [round(v, 3) for v in self.pos],
                "flames": self.flames,
                "carried": self.carried,
                "capacity": self.capacity,
                "successful_lights": self.successful_lights,
            },
            "lanterns": [{
                "id": l["id"],
                "pos": [round(v, 3) for v in l["pos"]],
                "lit": l["lit"],
                "fuel": l["fuel"],
                "deposited": l["deposited"],
                "ever_lit": l["ever_lit"],
                "relit_count": l["relit_count"],
            } for l in self.lanterns],
            "shades": [{
                "id": s["id"],
                "pos": [round(v, 3) for v in s["pos"]],
                "state": s["state"],
                "drain": s["state"] == "drain",
            } for s in self.shades],
            "wisps": [{"id": w["id"], "pos": [round(v, 3) for v in w["pos"]]} for w in self.wisps],
            "charms": [{"id": c["id"], "pos": [round(v, 3) for v in c["pos"]], "collected": c["collected"]} for c in self.charms],
            "wind_shield_s": round(self.wind_shield_s, 3),
            "motes_active": len(self.motes),
        }


def headless(args):
    scenario = load_json(args.scenario, "scenario") if args.scenario else None
    frames = load_inputs(args.inputs)
    fidx = 0
    current = {"move": [0, 0], "cam_yaw_deg": 0, "jump": False, "interact": False, "pulse": False, "dash": False, "glide": False}
    game = Game(args.seed, scenario, args.night)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as stream:
        for event in game.events:
            stream.write(json.dumps(event, separators=(",", ":")) + "\n")
        game.events.clear()
        stream.write(json.dumps(game.snapshot(), separators=(",", ":")) + "\n")
        for k in range(args.ticks):
            while fidx < len(frames) and frames[fidx]["tick"] == k:
                current.update({key: value for key, value in frames[fidx].items() if key != "tick"})
                fidx += 1
            if game.state != "playing":
                break
            current["_jump_prev"] = getattr(game, "_last_jump", False)
            current["_interact_prev"] = getattr(game, "_last_interact", False)
            current["_pulse_prev"] = getattr(game, "_last_pulse", False)
            current["_dash_prev"] = getattr(game, "_last_dash", False)
            game.step(current)
            game._last_jump = current["jump"]
            game._last_interact = current["interact"]
            game._last_pulse = current["pulse"]
            game._last_dash = current["dash"]
            for event in game.events:
                stream.write(json.dumps(event, separators=(",", ":")) + "\n")
            game.events.clear()
            if game.tick % args.snapshot_every == 0:
                stream.write(json.dumps(game.snapshot(), separators=(",", ":")) + "\n")
            if game.state != "playing":
                break
        stream.write(json.dumps({"type": "end", "ticks": game.tick, "sim_ticks": game.sim_tick, "state": game.state, "score": game.score}, separators=(",", ":")) + "\n")


def find_godot():
    candidates = [Path("C:/Tools/Godot/Godot_v4.7.2-stable_win64_console.exe"), Path("C:/Tools/Godot/Godot_v4.7.2-stable_win64.exe")]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for name in ("godot4", "godot"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def template_dir():
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Godot"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "Godot"
    else:
        base = Path.home() / ".local" / "share" / "godot"
    return base / "export_templates" / "4.7.2.stable"


def web_status():
    build = ROOT / "build" / "web" / "index.html"
    return build, template_dir(), find_godot()


def check_web():
    build, templates, godot = web_status()
    print(f"contract: {ROOT / 'game.contract.json'}")
    print(f"godot: {godot or 'not found'}")
    print(f"templates: {templates if templates.exists() else 'missing'}")
    print(f"build: {build if build.exists() else 'missing'}")
    return 0 if build.exists() else 2


def run_web(args):
    build, templates, godot = web_status()
    if args.build:
        result = subprocess.call([sys.executable, str(ROOT / "tools" / "build_web.py")])
        if result != 0:
            return result
        build, templates, godot = web_status()
    if not build.exists():
        print("Web build missing. Install Godot 4.7.2 export templates, then run:", file=sys.stderr)
        print("  python tools/build_web.py", file=sys.stderr)
        print(f"Godot: {godot or 'not found'}; templates: {templates}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(ROOT / "tools" / "serve_web.py"), "--dir", str(ROOT / "build" / "web"), "--port", str(args.port)]
    if args.no_browser:
        cmd.append("--no-browser")
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Đảo Đèn Lồng")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--night", type=int, default=1)
    parser.add_argument("--scenario")
    parser.add_argument("--inputs")
    parser.add_argument("--ticks", type=int, default=18000)
    parser.add_argument("--out", default="out.jsonl")
    parser.add_argument("--snapshot-every", type=int, default=10)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.night not in (1, 2, 3):
            raise ValueError("night must be 1, 2 or 3")
        if args.ticks < 0 or args.snapshot_every <= 0:
            raise ValueError("ticks must be >= 0 and snapshot-every must be > 0")
        if args.check:
            return check_web()
        if args.headless:
            headless(args)
        else:
            return run_web(args)
    except (ValueError, TypeError, AttributeError, KeyError, OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
