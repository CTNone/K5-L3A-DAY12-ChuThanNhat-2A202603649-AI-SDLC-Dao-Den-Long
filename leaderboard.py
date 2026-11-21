"""Persistent top-10 leaderboard for Dao Den Long."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

MIN_NAME = 3
MAX_NAME = 12
MAX_ENTRIES = 10
VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean_name(name: str) -> str:
    text = " ".join(str(name).strip().split())
    if not (MIN_NAME <= len(text) <= MAX_NAME):
        raise ValueError(f"name must be {MIN_NAME}-{MAX_NAME} characters")
    if any(ord(ch) < 32 for ch in text):
        raise ValueError("name must not contain control characters")
    return text


def validate_entry(entry: dict, require_time: bool = True) -> dict:
    if not isinstance(entry, dict):
        raise ValueError("leaderboard entry must be an object")
    name = clean_name(entry.get("name", ""))
    try:
        score = int(entry["score"])
        nights_won = int(entry["nights_won"])
        seed = int(entry["seed"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("score, nights_won and seed must be integers") from exc
    if score < 0 or nights_won < 0:
        raise ValueError("score and nights_won must be non-negative")
    achieved_at = str(entry.get("achieved_at", "")).strip()
    if require_time:
        if not achieved_at:
            raise ValueError("achieved_at is required")
        try:
            datetime.fromisoformat(achieved_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("achieved_at must be ISO-8601") from exc
        if not (achieved_at.endswith("Z") or "+" in achieved_at[10:] or "-" in achieved_at[10:]):
            raise ValueError("achieved_at must include a timezone")
    return {
        "name": name,
        "score": score,
        "nights_won": nights_won,
        "achieved_at": achieved_at,
        "seed": seed,
    }


def _time_key(entry: dict) -> str:
    return str(entry.get("achieved_at", ""))


def sort_entries(entries: list[dict]) -> list[dict]:
    return sorted(
        entries,
        key=lambda e: (-int(e["score"]), _time_key(e), -int(e["nights_won"]), str(e["name"]).lower()),
    )


def normalize(entries: list[dict]) -> list[dict]:
    best: dict[str, dict] = {}
    for raw in entries:
        entry = validate_entry(raw, require_time=False)
        old = best.get(entry["name"])
        if old is None or sort_entries([entry, old])[0] is entry:
            best[entry["name"]] = entry
    return sort_entries(list(best.values()))[:MAX_ENTRIES]


def load(path: str | os.PathLike) -> list[dict]:
    file = Path(path)
    if not file.exists():
        return []
    data = json.loads(file.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("leaderboard must contain an entries array")
    return normalize(data)


def save(path: str | os.PathLike, entries: list[dict]) -> list[dict]:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    ordered = normalize(entries)
    payload = {"version": VERSION, "entries": ordered}
    temp = file.with_suffix(file.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    temp.replace(file)
    return ordered


def add(path: str | os.PathLike, name: str, score: int, nights_won: int, seed: int, achieved_at: str | None = None) -> list[dict]:
    entry = validate_entry({
        "name": name,
        "score": score,
        "nights_won": nights_won,
        "seed": seed,
        "achieved_at": achieved_at or now_iso(),
    })
    ordered = normalize(load(path) + [entry])
    save(path, ordered)
    return ordered


def export(path: str | os.PathLike, source: str | os.PathLike) -> list[dict]:
    ordered = load(source)
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return ordered
