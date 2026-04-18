"""
history.py — persist and load chat history as JSON.
"""
import json
import os
from datetime import datetime
from typing import List, Dict
from config import HISTORY_PATH


def _load() -> List[Dict]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(records: List[Dict]) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def append(role: str, text: str) -> None:
    records = _load()
    records.append({
        "role": role,
        "text": text,
        "ts":   datetime.now().isoformat(timespec="seconds"),
    })
    _save(records)


def load_all() -> List[Dict]:
    return _load()


def clear() -> None:
    _save([])
