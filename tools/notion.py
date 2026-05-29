"""Notion API – Seiten erstellen und lesen (Phase 2)

Setup:
1. notion.so → Einstellungen → Integrationen → Neue Integration erstellen
2. Integration Token in .env speichern: NOTION_TOKEN=secret_...
3. Gewünschte Datenbank/Seite mit Integration teilen (Share-Button)
"""

import os
from datetime import datetime


def _get_client():
    from notion_client import Client
    return Client(auth=os.environ["NOTION_TOKEN"])


def create_page(title: str, content: str, database_id: str | None = None) -> str:
    client = _get_client()

    if database_id:
        response = client.pages.create(
            parent={"database_id": database_id},
            properties={"Name": {"title": [{"text": {"content": title}}]}},
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": content}}]},
            }],
        )
    else:
        page_id = os.getenv("NOTION_DEFAULT_PAGE_ID", "")
        response = client.pages.create(
            parent={"page_id": page_id},
            properties={"title": {"title": [{"text": {"content": title}}]}},
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": content}}]},
            }],
        )

    return f"Notion-Seite '{title}' erstellt: {response['url']}"


def append_to_page(page_id: str, text: str) -> str:
    client = _get_client()
    client.blocks.children.append(
        block_id=page_id,
        children=[{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": f"[{datetime.now().strftime('%H:%M')}] {text}"}
                }]
            },
        }],
    )
    return "Hinzugefügt."


def search_pages(query: str, max_results: int = 5) -> list[dict]:
    client = _get_client()
    results = client.search(query=query, page_size=max_results)
    pages = []
    for item in results.get("results", []):
        title = ""
        props = item.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                texts = prop["title"]
                if texts:
                    title = texts[0]["plain_text"]
                    break
        pages.append({"id": item["id"], "title": title, "url": item.get("url", "")})
    return pages
