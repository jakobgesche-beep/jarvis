"""GPT-4o mini Integration mit Tool-Calling und Smart-Routing zu Ollama"""

import json
import os
from typing import Any

from openai import AsyncOpenAI

from core.memory import Memory
from tools.macos import open_app, send_notification, get_frontmost_app, run_applescript

_SYSTEM_PROMPT = """Du bist Jarvis, ein persönlicher KI-Assistent auf einem MacBook Air M4.
Du kommunizierst auf Deutsch, bist präzise und hilfreich.
Du hast Zugriff auf macOS, E-Mails, Kalender, Browser und Notizen.
Antworte immer kurz und natürlich – du wirst vorgelesen."""

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Öffnet eine macOS-App",
            "parameters": {
                "type": "object",
                "properties": {"app_name": {"type": "string", "description": "Name der App, z.B. 'Safari'"}},
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
            "name": "run_applescript",
            "description": "Führt AppleScript direkt aus",
            "parameters": {
                "type": "object",
                "properties": {"script": {"type": "string"}},
                "required": ["script"],
            },
        },
    },
    # TODO Phase 2: search_web, read_emails, send_email, calendar tools, notion
]

_TOOL_MAP = {
    "open_app": lambda args: open_app(args["app_name"]),
    "send_notification": lambda args: send_notification(args["title"], args["message"]),
    "run_applescript": lambda args: run_applescript(args["script"]),
}

_SIMPLE_TASK_KEYWORDS = ["öffne", "open", "wecker", "timer", "schreib auf", "notiz"]


class Brain:
    def __init__(self, memory: Memory):
        self._client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._memory = memory
        self._model = os.getenv("JARVIS_LLM_MODEL", "gpt-4o-mini")
        self._complex_model = os.getenv("JARVIS_LLM_COMPLEX_MODEL", "gpt-4o")

    def _is_simple_task(self, text: str) -> bool:
        return any(kw in text.lower() for kw in _SIMPLE_TASK_KEYWORDS)

    async def process(self, user_input: str) -> str:
        context = await self._memory.get_context(user_input)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            *context,
            {"role": "user", "content": user_input},
        ]

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
            max_tokens=500,
        )

        msg = response.choices[0].message

        if msg.tool_calls:
            tool_results = []
            for call in msg.tool_calls:
                args = json.loads(call.function.arguments)
                fn = _TOOL_MAP.get(call.function.name)
                result = fn(args) if fn else f"Tool '{call.function.name}' noch nicht implementiert"
                tool_results.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                })

            follow_up = await self._client.chat.completions.create(
                model=self._model,
                messages=[*messages, msg, *tool_results],
                max_tokens=300,
            )
            answer = follow_up.choices[0].message.content or "Erledigt."
        else:
            answer = msg.content or "Ich habe das nicht verstanden."

        await self._memory.save_turn(user_input, answer)
        return answer
