"""Groq LLM – Streaming, Tool-Calling, ReAct"""

import asyncio
import json
import os
import re
from typing import AsyncGenerator

from openai import AsyncOpenAI

from core.memory import Memory
from tools.macos import open_app, send_notification, run_applescript, set_volume, open_url
from tools.gmail import read_emails, send_email
from tools.calendar import get_events, create_event
from tools.browser import search_web
from tools.notion import create_page, search_pages
from tools.briefing import get_briefing

_SYSTEM_PROMPT = """Du bist Jarvis, ein persönlicher KI-Assistent auf einem MacBook Air M4.
Du kommunizierst auf Deutsch. Antworte IMMER in maximal 2 kurzen Sätzen – du wirst vorgelesen.
Kein Markdown, keine Listen. Direkt und präzise wie ein professioneller Assistent.
Bei Fragen die kein Tool brauchen: sofort antworten ohne Umwege."""

_TOOLS = [
    {"type":"function","function":{"name":"open_app","description":"Öffnet eine macOS-App","parameters":{"type":"object","properties":{"app_name":{"type":"string"}},"required":["app_name"]}}},
    {"type":"function","function":{"name":"send_notification","description":"macOS-Benachrichtigung anzeigen","parameters":{"type":"object","properties":{"title":{"type":"string"},"message":{"type":"string"}},"required":["title","message"]}}},
    {"type":"function","function":{"name":"set_volume","description":"Mac-Lautstärke setzen (0-100)","parameters":{"type":"object","properties":{"level":{"type":"integer"}},"required":["level"]}}},
    {"type":"function","function":{"name":"open_url","description":"URL im Browser öffnen","parameters":{"type":"object","properties":{"url":{"type":"string"}},"required":["url"]}}},
    {"type":"function","function":{"name":"run_applescript","description":"AppleScript ausführen","parameters":{"type":"object","properties":{"script":{"type":"string"}},"required":["script"]}}},
    {"type":"function","function":{"name":"read_emails","description":"Ungelesene Gmail-Mails lesen","parameters":{"type":"object","properties":{"max_results":{"type":"integer","default":5},"query":{"type":"string","default":"is:unread"}},"required":[]}}},
    {"type":"function","function":{"name":"send_email","description":"E-Mail über Gmail senden","parameters":{"type":"object","properties":{"to":{"type":"string"},"subject":{"type":"string"},"body":{"type":"string"}},"required":["to","subject","body"]}}},
    {"type":"function","function":{"name":"get_calendar_events","description":"Kalendertermine der nächsten Tage","parameters":{"type":"object","properties":{"days_ahead":{"type":"integer","default":7}},"required":[]}}},
    {"type":"function","function":{"name":"create_calendar_event","description":"Kalendertermin erstellen","parameters":{"type":"object","properties":{"title":{"type":"string"},"start_iso":{"type":"string"},"duration_minutes":{"type":"integer","default":60},"description":{"type":"string","default":""}},"required":["title","start_iso"]}}},
    {"type":"function","function":{"name":"search_web","description":"Im Web suchen","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
    {"type":"function","function":{"name":"get_briefing","description":"Tägliches Briefing: Uhrzeit, Datum, Wetter","parameters":{"type":"object","properties":{"city":{"type":"string","default":""}},"required":[]}}},
    {"type":"function","function":{"name":"save_to_notion","description":"Notiz in Notion speichern","parameters":{"type":"object","properties":{"title":{"type":"string"},"content":{"type":"string"}},"required":["title","content"]}}},
    {"type":"function","function":{"name":"search_notion","description":"Notion durchsuchen","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}},
]

_TOOL_MAP = {
    "open_app":             lambda a: open_app(a["app_name"]),
    "send_notification":    lambda a: send_notification(a["title"], a["message"]),
    "set_volume":           lambda a: set_volume(a["level"]),
    "open_url":             lambda a: open_url(a["url"]),
    "run_applescript":      lambda a: run_applescript(a["script"]),
    "read_emails":          lambda a: read_emails(a.get("max_results", 5), a.get("query", "is:unread")),
    "send_email":           lambda a: send_email(a["to"], a["subject"], a["body"]),
    "get_calendar_events":  lambda a: get_events(a.get("days_ahead", 7)),
    "create_calendar_event":lambda a: create_event(a["title"], a["start_iso"], a.get("duration_minutes", 60), a.get("description", "")),
    "search_web":           lambda a: search_web(a["query"]),
    "get_briefing":         lambda a: get_briefing(a.get("city", "")),
    "save_to_notion":       lambda a: create_page(a["title"], a["content"]),
    "search_notion":        lambda a: search_pages(a["query"]),
}

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_SENTENCE_SEP = re.compile(r'(?<=[.!?])\s+')


class Brain:
    def __init__(self, memory: Memory):
        self._client = AsyncOpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url=_GROQ_BASE_URL,
        )
        self._memory = memory
        self._model = os.getenv("JARVIS_LLM_MODEL", "llama-3.3-70b-versatile")

    async def _call_tool(self, name: str, args: dict) -> str:
        fn = _TOOL_MAP.get(name)
        if fn is None:
            return f"Tool '{name}' nicht implementiert."
        result = fn(args)
        if asyncio.iscoroutine(result):
            result = await result
        if isinstance(result, (list, dict)):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    async def _build_messages(self, user_input: str) -> list:
        context = await self._memory.get_context(user_input)
        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            *context,
            {"role": "user", "content": user_input},
        ]

    async def process_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """Streamt Antwort satzweise → TTS startet sofort beim ersten Satz."""
        messages = await self._build_messages(user_input)
        full_answer = ""

        # Erster Call: Tool-Detection (nicht streamend, weil Tool-Calls kein Streaming unterstützen)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
            max_tokens=400,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            # Tools ausführen
            messages.append(msg)
            tool_results = []
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments)
                print(f"[Brain] Tool: {call.function.name}({args})")
                result = await self._call_tool(call.function.name, args)
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })
            messages.extend(tool_results)

            # Zweiter Call: Antwort STREAMEN
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
                max_tokens=200,
            )

            buffer = ""
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                buffer += delta
                full_answer += delta

                # Satz fertig? → sofort ausgeben
                while True:
                    m = re.search(r'[.!?](\s|$)', buffer)
                    if not m:
                        break
                    end = m.start() + 1
                    sentence = buffer[:end].strip()
                    buffer = buffer[end:].lstrip()
                    if sentence:
                        yield sentence

            if buffer.strip():
                full_answer_remaining = buffer.strip()
                yield full_answer_remaining

        else:
            # Kein Tool → Antwort direkt streamen
            direct = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
                max_tokens=200,
            )

            buffer = ""
            async for chunk in direct:
                delta = chunk.choices[0].delta.content or ""
                buffer += delta
                full_answer += delta

                while True:
                    m = re.search(r'[.!?](\s|$)', buffer)
                    if not m:
                        break
                    end = m.start() + 1
                    sentence = buffer[:end].strip()
                    buffer = buffer[end:].lstrip()
                    if sentence:
                        yield sentence

            if buffer.strip():
                yield buffer.strip()

        await self._memory.save_turn(user_input, full_answer)

    async def process(self, user_input: str) -> str:
        """Nicht-streamende Version für API-Calls."""
        parts = []
        async for sentence in self.process_stream(user_input):
            parts.append(sentence)
        return " ".join(parts)
