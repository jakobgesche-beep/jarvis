"""Groq LLM-Kern mit Tool-Calling und ReAct-Loop (kostenlos)"""

import asyncio
import json
import os

from openai import AsyncOpenAI

from core.memory import Memory
from tools.macos import open_app, send_notification, run_applescript, set_volume, open_url
from tools.gmail import read_emails, send_email
from tools.calendar import get_events, create_event
from tools.browser import search_web
from tools.notion import create_page, search_pages
from tools.briefing import get_briefing

_SYSTEM_PROMPT = """Du bist Jarvis, ein persönlicher KI-Assistent auf einem MacBook Air M4.
Du kommunizierst auf Deutsch, bist präzise, freundlich und hilfreich.
Du hast Zugriff auf macOS, E-Mails, Kalender, Browser und Notizen.
Antworte immer kurz und natürlich – du wirst vorgelesen.
Kein Markdown, keine Listen, keine Sonderzeichen – nur fließenden gesprochenen Text."""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Öffnet eine macOS-App",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string", "description": "Name der App, z.B. Safari, Finder, Spotify"}},
                "required": ["app_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Zeigt eine macOS-Benachrichtigung an",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["title", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Setzt die Lautstärke des Macs (0-100)",
            "parameters": {
                "type": "object",
                "properties": {"level": {"type": "integer", "minimum": 0, "maximum": 100}},
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Öffnet eine URL im Browser",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_applescript",
            "description": "Führt AppleScript direkt aus für komplexe macOS-Aktionen",
            "parameters": {
                "type": "object",
                "properties": {"script": {"type": "string"}},
                "required": ["script"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_emails",
            "description": "Liest E-Mails aus Gmail",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "default": 5},
                    "query": {"type": "string", "default": "is:unread"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Sendet eine E-Mail über Gmail",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Zeigt Kalendertermine der nächsten Tage",
            "parameters": {
                "type": "object",
                "properties": {"days_ahead": {"type": "integer", "default": 7}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Erstellt einen neuen Kalendertermin",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_iso": {"type": "string", "description": "ISO 8601, z.B. 2025-06-01T10:00:00"},
                    "duration_minutes": {"type": "integer", "default": 60},
                    "description": {"type": "string", "default": ""},
                },
                "required": ["title", "start_iso"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Sucht im Web via DuckDuckGo",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_notion",
            "description": "Speichert eine Notiz in Notion",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_briefing",
            "description": "Gibt ein tägliches Briefing mit Uhrzeit, Datum und aktuellem Wetter zurück",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "default": "", "description": "Stadt für Wetter, leer = automatisch"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_notion",
            "description": "Durchsucht Notion nach Seiten",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
]

_TOOL_MAP = {
    "open_app": lambda a: open_app(a["app_name"]),
    "send_notification": lambda a: send_notification(a["title"], a["message"]),
    "set_volume": lambda a: set_volume(a["level"]),
    "open_url": lambda a: open_url(a["url"]),
    "run_applescript": lambda a: run_applescript(a["script"]),
    "read_emails": lambda a: read_emails(a.get("max_results", 5), a.get("query", "is:unread")),
    "send_email": lambda a: send_email(a["to"], a["subject"], a["body"]),
    "get_calendar_events": lambda a: get_events(a.get("days_ahead", 7)),
    "create_calendar_event": lambda a: create_event(
        a["title"], a["start_iso"], a.get("duration_minutes", 60), a.get("description", "")
    ),
    "search_web": lambda a: search_web(a["query"]),  # async
    "get_briefing": lambda a: get_briefing(a.get("city", "")),
    "save_to_notion": lambda a: create_page(a["title"], a["content"]),
    "search_notion": lambda a: search_pages(a["query"]),
}

_MAX_REACT_STEPS = 5
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


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
            return f"Tool '{name}' ist noch nicht implementiert."
        result = fn(args)
        if asyncio.iscoroutine(result):
            result = await result
        if isinstance(result, (list, dict)):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    async def process(self, user_input: str) -> str:
        context = await self._memory.get_context(user_input)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            *context,
            {"role": "user", "content": user_input},
        ]

        # ReAct-Loop: Think → Act → Observe (max. _MAX_REACT_STEPS Iterationen)
        answer = "Ich habe das nicht verstanden."
        for _ in range(_MAX_REACT_STEPS):
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=_TOOLS,
                tool_choice="auto",
                max_tokens=500,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                answer = msg.content or answer
                break

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

        await self._memory.save_turn(user_input, answer)
        return answer
