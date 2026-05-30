"""Tägliches Briefing: Zeit, Datum, Wetter"""

import datetime
import urllib.request
import json


def get_briefing(city: str = "") -> str:
    now = datetime.datetime.now()
    weekdays = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    months = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
    day_name = weekdays[now.weekday()]
    date_str = f"{day_name}, {now.day}. {months[now.month - 1]} {now.year}"
    time_str = now.strftime("%H:%M")

    weather = _get_weather(city)

    return f"Es ist {time_str} Uhr. Heute ist {date_str}. {weather}"


def _get_weather(city: str = "") -> str:
    try:
        location = city.strip() or ""
        url = f"https://wttr.in/{urllib.parse.quote(location)}?format=j1" if location else "https://wttr.in/?format=j1"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/3.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        cond = data["current_condition"][0]
        temp = cond["temp_C"]
        desc = cond["weatherDesc"][0]["value"]
        feels = cond["FeelsLikeC"]
        return f"Das Wetter: {temp} Grad, {desc}, gefühlt {feels} Grad."
    except Exception:
        return "Das Wetter konnte ich leider nicht abrufen."


# Fix missing import
import urllib.parse
