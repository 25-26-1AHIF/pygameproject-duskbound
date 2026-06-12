import json
from pathlib import Path
from typing import Any


# KI-Anfang
# KI: ChatGPT
# prompt: Korrigiere das SAVE System da es bei uns aktuell nicht ganz funktioniert.
def save_game(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_game(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_rankings(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def save_ranking(path: Path, name: str, score: int, time_seconds: int) -> list[dict[str, Any]]:
    rankings = load_rankings(path)
    rankings.append({
        "name": name.strip()[:18] or "Spieler",
        "score": int(score),
        "time_seconds": int(time_seconds),
    })
    rankings.sort(key=lambda entry: (-entry["score"], entry["time_seconds"]))
    rankings = rankings[:10]
    path.write_text(json.dumps(rankings, indent=2), encoding="utf-8")
    return rankings
# KI-Ende
