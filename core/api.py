"""FastAPI WebSocket-Server – macht Jarvis vom iPhone / Cloudflare erreichbar"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.memory import Memory

WEB_DIR = Path(__file__).parent.parent / "web"


class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._clients:
            self._clients.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def count(self) -> int:
        return len(self._clients)


# Globaler Manager – wird von main.py geteilt
manager = ConnectionManager()


def _check_token(req_token: Optional[str], env_token: str) -> bool:
    env_token = (env_token or "").strip()
    if not env_token:
        return True  # Kein Token gesetzt → alles erlaubt
    return (req_token or "").strip() == env_token


def create_app(brain, memory: Memory, listener=None) -> FastAPI:
    app = FastAPI(title="JARVIS", docs_url=None, redoc_url=None)
    env_token = os.environ.get("JARVIS_API_TOKEN", "")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Web-UI lokal ausliefern – NUR /app, "/" NICHT mounten (würde API-Routes blockieren)
    if (WEB_DIR / "app").exists():
        app.mount("/app", StaticFiles(directory=str(WEB_DIR / "app"), html=True), name="app")

    class ChatRequest(BaseModel):
        message: str
        token: Optional[str] = None

    @app.get("/health")
    async def health():
        key = os.environ.get("GROQ_API_KEY", "")
        return {
            "status": "ok",
            "model": brain._model,
            "clients": manager.count,
            "groq_key_set": bool(key),
            "groq_key_preview": (key[:8] + "...") if key else "",
            "voice": os.environ.get("JARVIS_VOICE", "de-DE-ConradNeural"),
        }

    class SettingsRequest(BaseModel):
        groq_api_key: Optional[str] = None
        voice: Optional[str] = None

    @app.post("/settings")
    async def save_settings(req: SettingsRequest, token: Optional[str] = None):
        if not _check_token(token, env_token):
            raise HTTPException(status_code=401)

        env_path = WEB_DIR.parent / ".env"
        updated = {}

        def _set(key: str, value: str):
            os.environ[key] = value
            updated[key] = value
            # .env Datei aktualisieren
            if env_path.exists():
                lines = env_path.read_text().splitlines()
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                        break
                else:
                    lines.append(f"{key}={value}")
                env_path.write_text("\n".join(lines) + "\n")

        if req.groq_api_key and req.groq_api_key.strip():
            _set("GROQ_API_KEY", req.groq_api_key.strip())
        if req.voice and req.voice.strip():
            _set("JARVIS_VOICE", req.voice.strip())

        return {"updated": updated, "status": "ok"}

    @app.post("/transcribe")
    async def transcribe(audio: UploadFile = File(...), token: Optional[str] = None):
        """Empfängt WebM-Audio vom Browser und gibt transkribierten Text zurück."""
        if not _check_token(token, env_token):
            raise HTTPException(status_code=401)
        if listener is None:
            raise HTTPException(status_code=503, detail="Listener nicht verfügbar")
        data = await audio.read()
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, listener.transcribe_webm, data)
        return {"text": text}

    @app.post("/chat")
    async def chat(req: ChatRequest):
        if not _check_token(req.token, env_token):
            raise HTTPException(status_code=401, detail="Ungültiger Token")

        await manager.broadcast({"type": "user", "text": req.message})

        try:
            parts = []
            async for sentence in brain.process_stream(req.message):
                parts.append(sentence)
                await manager.broadcast({"type": "assistant", "text": sentence})
            response = " ".join(parts)
        except Exception as e:
            response = f"Fehler: {e}"
            await manager.broadcast({"type": "assistant", "text": response})

        return {"response": response}

    @app.get("/history")
    async def history(token: Optional[str] = None, limit: int = 60):
        if not _check_token(token, env_token):
            raise HTTPException(status_code=401)
        cursor = memory._db.execute(
            "SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = [{"role": r, "content": c, "ts": ts} for r, c, ts in reversed(cursor.fetchall())]
        return {"messages": rows}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket, token: Optional[str] = None):
        if not _check_token(token, env_token):
            await ws.close(code=4001)
            return
        await manager.connect(ws)
        try:
            while True:
                # Eingehende Chat-Nachrichten direkt über WebSocket verarbeiten
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                    if data.get("type") == "chat" and data.get("text"):
                        msg = data["text"]
                        await manager.broadcast({"type": "user", "text": msg})
                        response = await brain.process(msg)
                        await manager.broadcast({"type": "assistant", "text": response})
                except Exception:
                    pass
        except WebSocketDisconnect:
            manager.disconnect(ws)

    return app


async def start_server(brain, memory: Memory, listener=None):
    port = int(os.getenv("JARVIS_API_PORT", "8080"))
    app = create_app(brain=brain, memory=memory, listener=listener)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(config)
    print(f"[API] Server läuft auf http://0.0.0.0:{port}")
    await server.serve()
