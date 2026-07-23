#!/usr/bin/env python3
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"
SITE_DIR = ROOT / "site"
DIST_DIR = ROOT / "dist"


def esc(value: str) -> str:
    return str(value or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def dt_value(value: str, all_day: bool) -> tuple[str, str]:
    if all_day:
        return "VALUE=DATE", value[:10].replace("-", "")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return "", dt.strftime("%Y%m%dT%H%M%SZ")


def event_lines(event: dict) -> list[str]:
    all_day = bool(event.get("allDay"))
    start_param, start = dt_value(event["start"], all_day)
    lines = ["BEGIN:VEVENT", f"UID:{esc(event['id'])}@streamer-event-calendar", f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"]
    lines.append(f"DTSTART{';' + start_param if start_param else ''}:{start}")
    if event.get("end"):
        end_param, end = dt_value(event["end"], all_day)
        lines.append(f"DTEND{';' + end_param if end_param else ''}:{end}")
    lines += [f"SUMMARY:{esc(event['title'])}", f"CATEGORIES:{'Street Fighter 6' if event.get('category') == 'sf6' else 'Streamer'}"]
    if event.get("location"):
        lines.append(f"LOCATION:{esc(event['location'])}")
    description = event.get("notes", "")
    if event.get("persons"):
        description = f"出演: {'、'.join(event['persons'])}" + (f"\n{description}" if description else "")
    if description:
        lines.append(f"DESCRIPTION:{esc(description)}")
    if event.get("url"):
        lines.append(f"URL:{event['url']}")
    if event.get("status") == "cancelled":
        lines.append("STATUS:CANCELLED")
    lines += ["END:VEVENT"]
    return lines


def write_ics(path: Path, events: list[dict], name: str) -> None:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "PRODID:-//mmiyaji//Streamer Event Calendar//JA", f"X-WR-CALNAME:{esc(name)}", "X-WR-TIMEZONE:Asia/Tokyo"]
    for event in events:
        lines.extend(event_lines(event))
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def main() -> None:
    events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError("data/events.json must contain a JSON array")
    DIST_DIR.mkdir(exist_ok=True)
    shutil.copy2(SITE_DIR / "index.html", DIST_DIR / "index.html")
    shutil.copy2(EVENTS_PATH, DIST_DIR / "events.json")
    public = [e for e in events if e.get("confidence") in {"high", "medium"}]
    write_ics(DIST_DIR / "calendar.ics", public, "Streamer & SF6 Events")
    write_ics(DIST_DIR / "streamers.ics", [e for e in public if e.get("category") == "streamer"], "Streamer Events")
    write_ics(DIST_DIR / "sf6.ics", [e for e in public if e.get("category") == "sf6"], "Street Fighter 6 Events")
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(public)} public events into {DIST_DIR}")


if __name__ == "__main__":
    main()
