"""Tägliches Briefing: Zeit, Datum, Wetter via wttr.in"""

import datetime
import urllib.request
import urllib.parse
import json


def get_briefing(city: str = "") -> str:
    now = datetime.datetime.now()
    weekdays = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    months = ["Januar","Februar","März","April","Mai","Juni","Juli","August",
              "September","Oktober","November","Dezember"]
    day_name = weekdays[now.weekday()]
    date_str = f"{day_name}, {now.day}. {months[now.month - 1]} {now.year}"
    time_str = now.strftime("%H:%M")
    weather = get_weather(city)
    return f"Es ist {time_str} Uhr. Heute ist {date_str}. {weather}"


def get_weather(city: str = "") -> str:
    """Schnelles Wetter via wttr.in – funktioniert ohne API-Key."""
    try:
        loc = urllib.parse.quote(city.strip()) if city.strip() else ""
        # Format: Temperatur + Beschreibung in einer Zeile, sehr schnell
        url = f"https://wttr.in/{loc}?format=j1&lang=de"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/3.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read())
        c = data["current_condition"][0]
        temp = c["temp_C"]
        feels = c["FeelsLikeC"]
        # Deutsche Beschreibung aus langTxt
        desc = next(
            (x["value"] for x in c.get("lang_de", []) if x.get("value")),
            c["weatherDesc"][0]["value"]
        )
        place = city.strip() or "deinem Standort"
        return f"In {place}: {temp} Grad, {desc}, gefühlt {feels} Grad."
    except Exception as e:
        return "Das Wetter ist gerade nicht abrufbar."
