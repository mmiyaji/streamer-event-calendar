#!/usr/bin/env python3
"""Conservative scheduled discovery from official pages. Requires OPENAI_API_KEY.
Only date-explicit, official-source proposals pass validation; no key = no write.
"""
import datetime as dt
import html
import json
import os
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/automated_discoveries.json"
SOURCES = [
    "https://www.streetfighter.com/6/",
    "https://sf.esports.capcom.com/",
    "https://shadowverse-wb.com/",
    "https://ps.shadowverse-wb.com/26-27/schedule-results/",
    "https://rage-esports.jp/",
    "https://crazyraccoon.jp/",
    "https://zetadivision.com/news/",
    "https://www.openrec.tv/",
]
# Official organizers and channels; no third-party search snippet is trusted as a primary source.
DOMAINS = {"streetfighter.com", "capcom.com", "shadowverse-wb.com",
           "rage-esports.jp", "crazyraccoon.jp", "zetadivision.com",
           "openrec.tv"}
TYPES = {"tournament", "qualifier", "update", "stream", "offline_event"}
CATEGORIES = {"streamer", "sf6", "shadowverse_wb"}
PERSONS = {"たいじ", "もこう", "加藤純一", "なるお", "あっさりしょこ", "バトラ", "じゃすぱー"}

def official(url):
    try:
        p = urlparse(url)
        return p.scheme == "https" and any(p.hostname == d or p.hostname.endswith("." + d) for d in DOMAINS)
    except (ValueError, AttributeError):
        return False

def get_page(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EventCalendarBot/1.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            final = response.geturl()
            if not official(final):
                return None
            raw = response.read(220000).decode("utf-8", "replace")
        raw = re.sub(r"(?is)<(script|style|svg).*?</\\1>", " ", raw)
        raw = re.sub(r"(?s)<[^>]*>", " ", raw)
        return html.unescape(re.sub(r"\\s+", " ", raw))[:18000]
    except Exception as e:
        print(f"Source unavailable: {url}: {e}")
        return None

def propose(pages, existing):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("OPENAI_API_KEY not configured: no changes; configure repository Actions secret.")
        return []
    prompt = """Extract only NEW or CHANGED confirmed events with explicit YYYY-MM-DD dates
from these official webpage excerpts. Do not infer dates, times, participants, or cancellations.
Return JSON object {\\"events\\":[...]} with full event objects matching the existing schema.
Use only official URL from provided pages, with sourceUrls containing that URL.
Ignore past events, unconfirmed appearances, vague seasons, and duplicates.
Target: たいじ, もこう, 加藤純一, なるお, あっさりしょこ, バトラ, じゃすぱー;
SF6 major tournaments/qualifiers/updates; Shadowverse WB professional and major events.
Use category streamer for confirmed participant events even if game sf6/shadowverse_wb.
For recurring event rounds use one ID per day. Set official=true, source=official,
confidence=high, status=confirmed, priority=major or normal, region=jp or global,
type in tournament/qualifier/update/stream/offline_event.
Never return an event unless official page explicitly gives its date.
Existing event IDs and dates: """ + json.dumps(existing, ensure_ascii=False)[:16000]
    body = json.dumps({"model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
      "temperature": 0, "response_format": {"type": "json_object"},
      "messages": [{"role":"system","content":prompt},
                   {"role":"user","content":json.dumps(pages,ensure_ascii=False)}]}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=100) as response:
        result=json.load(response)
    return json.loads(result["choices"][0]["message"]["content"]).get("events", [])

def valid(e, pages, existing, now):
    if not isinstance(e, dict) or not isinstance(e.get("id"), str):
        return False
    if e.get("category") not in CATEGORIES or e.get("type") not in TYPES:
        return False
    if e.get("priority") not in {"major","normal"} or e.get("official") is not True:
        return False
    if e.get("status") != "confirmed" or e.get("confidence") != "high":
        return False
    if e.get("region") not in {"jp","global"} or not isinstance(e.get("tags"),list):
        return False
    if e.get("category") == "sf6" and e.get("game") != "sf6":
        return False
    if e.get("category") == "shadowverse_wb" and e.get("game") != "shadowverse_wb":
        return False
    if e.get("category") == "streamer" and not (set(e.get("persons",[])) & PERSONS):
        return False
    url=e.get("url","")
    if url not in pages or not official(url):
        return False
    start=e.get("start","")
    if not isinstance(start,str) or not re.match(r"^20\\d{2}-\\d{2}-\\d{2}(T.*)?$",start):
        return False
    try:
        day=dt.date.fromisoformat(start[:10])
        if day < now.date() or day > now.date()+dt.timedelta(days=400):
            return False
    except ValueError:
        return False
    # The source must contain the day in at least one common explicit format.
    source=pages[url]
    formats=[day.strftime("%Y-%m-%d"), day.strftime("%Y/%m/%d"),
             f"{day.year}年{day.month}月{day.day}日",
             f"{day.month}月{day.day}日"]
    if not any(x in source for x in formats):
        return False
    if not e.get("title") or not isinstance(e.get("allDay"),bool):
        return False
    if e.get("id") in existing and existing[e["id"]].get("start")==start:
        return False
    return True

def main():
    now=dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    pages={url:page for url in SOURCES if (page:=get_page(url))}
    existing={}
    for path in (ROOT/"data").glob("*.json"):
        try:
            entries=json.loads(path.read_text())
            if isinstance(entries,list):
                existing.update({e["id"]:e for e in entries if isinstance(e,dict) and "id" in e})
        except (ValueError,KeyError):
            pass
    proposals=propose(pages,existing)
    if not isinstance(proposals,list):
        raise ValueError("Invalid model response")
    accepted=[]
    for e in proposals:
        if valid(e,pages,existing,now):
            e["verified_at"]=now.isoformat(timespec="seconds")
            e["lastChecked"]=e["verified_at"]
            e["source"]="official"
            e["sourceUrls"]=[e["url"]]
            accepted.append(e)
    if not accepted:
        print(f"No verified changes. Pages fetched: {len(pages)}")
        return
    current=json.loads(OUTPUT.read_text())
    by_id={e["id"]:e for e in current}
    by_id.update({e["id"]:e for e in accepted})
    OUTPUT.write_text(json.dumps(list(by_id.values()),ensure_ascii=False,indent=2)+"\\n")
    print(f"Accepted {len(accepted)} changes")

if __name__=="__main__":
    main()
