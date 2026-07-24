#!/usr/bin/env python3
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "events.json"
SHADOWVERSE_EVENTS_PATH = ROOT / "data" / "shadowverse_wb_events.json"
DISCOVERED_EVENTS_PATH = ROOT / "data" / "discovered_events.json"
SFL_SCHEDULE_PATH = ROOT / "data" / "sfl_2026_schedule.json"
SITE_DIR = ROOT / "site"
DIST_DIR = ROOT / "dist"

CATEGORY_NAMES = {
    "streamer": "Streamer",
    "sf6": "Street Fighter 6",
    "shadowverse_wb": "Shadowverse: Worlds Beyond",
}

REQUIRED_METADATA = {
    "category",
    "type",
    "game",
    "priority",
    "source",
    "official",
    "region",
    "tags",
    "verified_at",
    "lastChecked",
}
ALLOWED_TYPES = {"tournament", "qualifier", "update", "stream", "offline_event"}
ALLOWED_PRIORITIES = {"major", "normal"}


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
    lines = [
        "BEGIN:VEVENT",
        f"UID:{esc(event['id'])}@streamer-event-calendar",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
    ]
    lines.append(f"DTSTART{';' + start_param if start_param else ''}:{start}")
    if event.get("end"):
        end_param, end = dt_value(event["end"], all_day)
        lines.append(f"DTEND{';' + end_param if end_param else ''}:{end}")
    category = CATEGORY_NAMES.get(event.get("category"), event.get("category", "Event"))
    lines += [f"SUMMARY:{esc(event['title'])}", f"CATEGORIES:{esc(category)}"]
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
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "PRODID:-//mmiyaji//Streamer Event Calendar//JA",
        f"X-WR-CALNAME:{esc(name)}",
        "X-WR-TIMEZONE:Asia/Tokyo",
    ]
    for event in events:
        lines.extend(event_lines(event))
    lines.append("END:VCALENDAR")
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_events(path: Path) -> list[dict]:
    events = load_json(path)
    if not isinstance(events, list):
        raise ValueError(f"{path} must contain a JSON array")
    return events


def validate_event(event: dict, source_path: Path) -> None:
    missing = REQUIRED_METADATA.difference(event)
    if missing:
        raise ValueError(f"{source_path}: {event.get('id', '<unknown>')} is missing metadata: {sorted(missing)}")
    if event["type"] not in ALLOWED_TYPES:
        raise ValueError(f"{source_path}: {event['id']} has unsupported type {event['type']!r}")
    if event["priority"] not in ALLOWED_PRIORITIES:
        raise ValueError(f"{source_path}: {event['id']} has unsupported priority {event['priority']!r}")
    if event["lastChecked"] != event["verified_at"]:
        raise ValueError(f"{source_path}: {event['id']} must keep lastChecked equal to verified_at")
    if not isinstance(event["official"], bool):
        raise ValueError(f"{source_path}: {event['id']} official must be a boolean")
    if not isinstance(event["tags"], list):
        raise ValueError(f"{source_path}: {event['id']} tags must be an array")


def build_sfl_events(path: Path) -> list[dict]:
    config = load_json(path)
    verified_at = config["verified_at"]
    start_time = config["startTime"]
    end_time = config["estimatedEndTime"]
    source_urls = config["sourceUrls"]
    events = []
    for item in config["rounds"]:
        division = item["division"].upper()
        round_number = int(item["round"])
        date = item["date"]
        division_slug = division.lower()
        events.append(
            {
                "id": f"sf6-sfl-japan-2026-division-{division_slug}-round-{round_number}",
                "title": f"ストリートファイターリーグ: Pro-JP 2026 Division {division} 第{round_number}節",
                "category": "sf6",
                "type": "tournament",
                "game": "sf6",
                "priority": "major",
                "source": "official",
                "official": True,
                "region": "jp",
                "tags": ["sfl", "pro-league", f"division-{division_slug}", f"round-{round_number}", "regular-season"],
                "verified_at": verified_at,
                "persons": [],
                "start": f"{date}T{start_time}",
                "end": f"{date}T{end_time}",
                "allDay": False,
                "location": "オンライン配信",
                "url": source_urls[0],
                "sourceUrls": source_urls,
                "status": "confirmed",
                "confidence": "high",
                "lastChecked": verified_at,
                "notes": "公式発表では18:30頃に配信開始予定。配信時間は約3〜4時間の予定のため、終了時刻は便宜上22:30として登録。進行により変動する可能性あり。",
            }
        )
    return events


def merge_events(event_groups: list[tuple[Path, list[dict]]]) -> list[dict]:
    merged: dict[str, dict] = {}
    for source_path, events in event_groups:
        for event in events:
            validate_event(event, source_path)
            event_id = event.get("id")
            if not event_id:
                raise ValueError(f"{source_path}: event id is required")
            merged[event_id] = event
    return list(merged.values())


def main() -> None:
    event_groups = [
        (EVENTS_PATH, load_events(EVENTS_PATH)),
        (SHADOWVERSE_EVENTS_PATH, load_events(SHADOWVERSE_EVENTS_PATH)),
        (DISCOVERED_EVENTS_PATH, load_events(DISCOVERED_EVENTS_PATH)),
        (SFL_SCHEDULE_PATH, build_sfl_events(SFL_SCHEDULE_PATH)),
    ]
    events = merge_events(event_groups)
    events.sort(key=lambda event: event["start"])

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    for item in SITE_DIR.iterdir():
        target = DIST_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    (DIST_DIR / "events.json").write_text(
        json.dumps(events, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    public = [e for e in events if e.get("confidence") in {"high", "medium"}]
    write_ics(DIST_DIR / "calendar.ics", public, "Streamer, SF6 & Shadowverse WB Events")
    write_ics(DIST_DIR / "streamers.ics", [e for e in public if e.get("category") == "streamer"], "Streamer Events")
    write_ics(DIST_DIR / "sf6.ics", [e for e in public if e.get("category") == "sf6"], "Street Fighter 6 Events")
    write_ics(
        DIST_DIR / "shadowverse-wb.ics",
        [e for e in public if e.get("category") == "shadowverse_wb"],
        "Shadowverse: Worlds Beyond Events",
    )
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(public)} public events into {DIST_DIR}")


if __name__ == "__main__":
    main()
