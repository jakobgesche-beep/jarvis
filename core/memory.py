"""Long-Term Memory: SQLite für Fakten, ChromaDB für semantische Suche"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "./data/jarvis.db"))
CHROMA_PATH = Path(os.getenv("JARVIS_CHROMA_PATH", "./data/chroma"))
CONTEXT_WINDOW = 20  # Letzte N Nachrichten als Short-Term Memory


class Memory:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup_db()
        self._chroma = None

    def _setup_db(self):
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        self._db.commit()

    def _get_chroma(self):
        if self._chroma is None:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self._chroma = client.get_or_create_collection("jarvis_memory")
        return self._chroma

    async def get_context(self, query: str) -> list[dict]:
        """Short-Term: letzte N Nachrichten + Long-Term: semantisch relevante"""
        cursor = self._db.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (CONTEXT_WINDOW,)
        )
        recent = [{"role": r, "content": c} for r, c in reversed(cursor.fetchall())]
        return recent

    async def save_turn(self, user_input: str, response: str):
        now = datetime.now().isoformat()
        self._db.executemany(
            "INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)",
            [(now, "user", user_input), (now, "assistant", response)]
        )
        self._db.commit()

    def save_fact(self, key: str, value: str):
        self._db.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat())
        )
        self._db.commit()

    def get_fact(self, key: str) -> str | None:
        cursor = self._db.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None
