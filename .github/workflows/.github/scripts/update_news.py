"""Скачивает экономический календарь текущей недели и сохраняет в news.json.
Сначала пробует Forex Factory, если не вышло — календарь TradingView."""
import json, sys, urllib.request
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def forex_factory():
    d = get("https://nfs.faireconomy.media/ff_calendar_thisweek.json")
    assert isinstance(d, list) and d
    return d

def tradingview():
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk)
    mon = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    sun = mon + timedelta(days=7) - timedelta(seconds=1)
    url = ("https://economic-calendar.tradingview.com/events"
           f"?from={mon.astimezone(timezone.utc):%Y-%m-%dT%H:%M:%S.000Z}"
           f"&to={sun.astimezone(timezone.utc):%Y-%m-%dT%H:%M:%S.000Z}"
           "&countries=US,EU,GB,JP,CN,DE")
    d = get(url, {"Origin": "https://www.tradingview.com", "Referer": "https://www.tradingview.com/"})
    imp = {-1: "Low", 0: "Medium", 1: "High"}
    out = [{
        "title": x.get("title", ""), "country": (x.get("currency") or "").upper(),
        "date": x.get("date"), "impact": imp.get(x.get("importance"), "Low"),
        "forecast": "" if x.get("forecast") is None else str(x["forecast"]),
        "previous": "" if x.get("previous") is None else str(x["previous"]),
        "actual": "" if x.get("actual") is None else str(x["actual"]),
        "time": "",
    } for x in d.get("result", []) if x.get("currency")]
    assert out
    return out

for name, fn in (("Forex Factory", forex_factory), ("TradingView", tradingview)):
    try:
        data = fn()
        with open("news.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"OK: {name}, событий: {len(data)}")
        sys.exit(0)
    except Exception as e:
        print(f"{name} не ответил: {e}")
sys.exit(1)
