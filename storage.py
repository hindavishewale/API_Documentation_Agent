from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class KnowledgeStore:
    def __init__(self, path: str = "api_knowledge.db"):
        self.path = Path(path)
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY, created_at TEXT, source_hash TEXT, payload TEXT NOT NULL)")
            connection.commit()

    def save(self, payload: dict[str, Any], source_hash: str = "") -> int:
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute("INSERT INTO analyses(created_at, source_hash, payload) VALUES (?, ?, ?)", (datetime.now(timezone.utc).isoformat(), source_hash, json.dumps(payload)))
            connection.commit()
            return int(cursor.lastrowid)

    def latest(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.path) as connection:
            row = connection.execute("SELECT payload FROM analyses ORDER BY id DESC LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None
