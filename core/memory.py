"""Short-Term Memory (SQLite) + Long-Term Memory (ChromaDB + lokale Embeddings)"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "./data/jarvis.db"))
CHROMA_PATH = Path(os.getenv("JARVIS_CHROMA_PATH", "./data/chroma"))
CONTEXT_WINDOW = 20
SEMANTIC_RESULTS = 3
# Lokales Embedding-Modell (kostenlos, ~90 MB, läuft auf CPU/Metal)
EMBED_MODEL = "all-MiniLM-L6-v2"


class Memory:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._setup_db()
        self._chroma = None
        self._embedder = None

    def _setup_db(self):
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        self._db.commit()

    def _get_chroma(self):
        if self._chroma is None:
            import chromadb
            client = chromadb.PersistentClient(path=str(CHROMA_PATH))
            self._chroma = client.get_or_create_collection(
                "jarvis_memory",
                metadata={"hnsw:space": "cosine"},
            )
        return self._chroma

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            print(f"[Memory] Lade Embedding-Modell '{EMBED_MODEL}'...")
            self._embedder = SentenceTransformer(EMBED_MODEL)
        return self._embedder

    def _embed(self, text: str) -> list[float]:
        return self._get_embedder().encode(text).tolist()

    async def _add_to_chroma(self, doc_id: str, text: str, role: str):
        try:
            embedding = self._embed(text)
            self._get_chroma().upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[{"role": role, "ts": datetime.now().isoformat()}],
            )
        except Exception as e:
            print(f"[Memory] ChromaDB-Fehler (ignoriert): {e}")

    async def _search_similar(self, query: str, n: int = SEMANTIC_RESULTS) -> list[dict]:
        try:
            chroma = self._get_chroma()
            if chroma.count() == 0:
                return []
            embedding = self._embed(query)
            results = chroma.query(
                query_embeddings=[embedding],
                n_results=min(n, chroma.count()),
                include=["documents", "metadatas"],
            )
            return [
                {"role": meta["role"], "content": doc}
                for doc, meta in zip(results["documents"][0], results["metadatas"][0])
            ]
        except Exception as e:
            print(f"[Memory] Semantische Suche fehlgeschlagen (ignoriert): {e}")
            return []

    async def get_context(self, query: str) -> list[dict]:
        """Short-Term (letzte N Nachrichten) + Long-Term (semantisch ähnliche)."""
        cursor = self._db.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (CONTEXT_WINDOW,),
        )
        recent = [{"role": r, "content": c} for r, c in reversed(cursor.fetchall())]

        semantic = await self._search_similar(query)
        recent_set = {m["content"] for m in recent}
        extra = [m for m in semantic if m["content"] not in recent_set]

        return [*extra, *recent]

    async def save_turn(self, user_input: str, response: str):
        now = datetime.now().isoformat()
        self._db.executemany(
            "INSERT INTO conversations (timestamp, role, content) VALUES (?, ?, ?)",
            [(now, "user", user_input), (now, "assistant", response)],
        )
        self._db.commit()

        row_id = self._db.execute("SELECT last_insert_rowid()").fetchone()[0]
        await self._add_to_chroma(f"user_{row_id - 1}", user_input, "user")
        await self._add_to_chroma(f"asst_{row_id}", response, "assistant")

    def save_fact(self, key: str, value: str):
        self._db.execute(
            "INSERT OR REPLACE INTO facts (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, datetime.now().isoformat()),
        )
        self._db.commit()

    def get_fact(self, key: str) -> str | None:
        cursor = self._db.execute("SELECT value FROM facts WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_all_facts(self) -> dict[str, str]:
        cursor = self._db.execute("SELECT key, value FROM facts")
        return dict(cursor.fetchall())
