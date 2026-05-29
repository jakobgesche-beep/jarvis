"""Playwright Browser-Automation – Suchen, Screenshots, Formulare (Phase 2)

Installation:
    pip install playwright
    playwright install chromium
"""

import asyncio
import base64
from pathlib import Path


async def search_web(query: str) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"https://duckduckgo.com/?q={query.replace(' ', '+')}")
        await page.wait_for_load_state("networkidle")

        results = await page.evaluate("""() => {
            const items = document.querySelectorAll('[data-result="snippet"]');
            return Array.from(items).slice(0, 3).map(el => el.innerText);
        }""")

        await browser.close()
        return "\n\n".join(results) if results else "Keine Ergebnisse gefunden."


async def take_screenshot_and_describe(url: str) -> str:
    """Screenshot machen und via GPT-4o Vision analysieren"""
    import os
    from openai import AsyncOpenAI
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        await page.goto(url, wait_until="networkidle")
        screenshot = await page.screenshot(type="png")
        await browser.close()

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    b64 = base64.b64encode(screenshot).decode()

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                {"type": "text", "text": "Was ist auf dieser Webseite zu sehen? Fasse es kurz zusammen."},
            ],
        }],
        max_tokens=300,
    )
    return response.choices[0].message.content or "Keine Beschreibung verfügbar."


async def goto_and_extract(url: str, selector: str = "body") -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        text = await page.inner_text(selector)
        await browser.close()
        return text[:2000]
