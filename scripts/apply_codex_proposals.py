#!/usr/bin/env python3
"""Validate untrusted Codex proposals and stage full events in one canonical overlay.

Does not execute code from the Codex branch. Fails closed on malformed data or
likely duplicates. An empty / unchanged proposal is a no-op.
"""
from __future__ import annotations
import argparse
import datetime as dt
import difflib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse
import build

JST = dt.timezone(dt.timedelta(hours=9))
FIELDS = {"id", "title", "category", "type", "game", "priority", "source",
          "official", "region", "tags", "verified_at", "lastChecked",
          "start", "allDay", "sourceUrls"}
TYPES = {"tournament", "qualifier", "update", "stream", "offline_event"}
CATEGORIES = {"streamer", "sf6", "shadowverse_wb", "pokemon"}
DATE_ONLY = re.compile(r"20\d\d-\d\d-\d\d$")
EVENT_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{4,120}$")


def parse_time(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be ISO date/time")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} invalid ISO date/time: {value!r}") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{field} must have a time zone")
    return parsed


def valid_https(url):
    if not isinstance(url, str) or len(url) > 1500:
        return False
    try:
        p = urlparse(url)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def normalize_title(value):
    s = unicodedata.normalize("NFKC", value).lower()
    s = re.sub(r"[\s【】「」『』()（）\-ー:：／/.,・_!！]+", "", s)
    return s


def validate(e, operation, today):
    if not isinstance(e, dict):
        raise ValueError("event must be an object")
    missing = FIELDS - set(e)
    if missing:
        raise ValueError(f"{e.get('id', '?')}: missing {sorted(missing)}")
    eid = e["id"]
    if not isinstance(eid, str) or not EVENT_ID.fullmatch(eid):
        raise ValueError(f"invalid event ID: {eid!r}")
    if not isinstance(e["title"], str) or not (6 <= len(e["title"]) <= 220):
        raise ValueError(f"{eid}: invalid title")
    if e["category"] not in CATEGORIES or e["type"] not in TYPES:
        raise ValueError(f"{eid}: unsupported category/type")
    if e["priority"] not in {"major", "normal"}:
        raise ValueError(f"{eid}: unsupported priority")
    if e["source"] != "official" or e["official"] is not True:
        raise ValueError(f"{eid}: official source required")
    if e["region"] not in {"jp", "global", "asia", "emeaa", "americas", "eu"}:
        raise ValueError(f"{eid}: invalid region")
    if not isinstance(e["tags"], list) or any(not isinstance(t, str) for t in e["tags"]):
        raise ValueError(f"{eid}: invalid tags")
    if not isinstance(e.get("persons", []), list):
        raise ValueError(f"{eid}: persons must be an array")
    if e["category"] in {"sf6", "shadowverse_wb", "pokemon"} and e["game"] != e["category"]:
        raise ValueError(f"{eid}: category/game mismatch")
    if e["game"] is not None and not isinstance(e["game"], str):
        raise ValueError(f"{eid}: invalid game")
    if not isinstance(e["allDay"], bool):
        raise ValueError(f"{eid}: allDay must be boolean")
    if not isinstance(e["sourceUrls"], list) or not e["sourceUrls"] or not all(valid_https(u) for u in e["sourceUrls"]):
        raise ValueError(f"{eid}: official source URLs required")
    if not valid_https(e.get("url", e["sourceUrls"][0])):
        raise ValueError(f"{eid}: invalid URL")
    checked = parse_time(e["verified_at"], "verified_at")
    if e["verified_at"] != e["lastChecked"]:
        raise ValueError(f"{eid}: verified_at != lastChecked")
    if checked.date() > today + dt.timedelta(days=1) or checked.date() < today - dt.timedelta(days=10):
        raise ValueError(f"{eid}: stale/future verification date")
    if e["allDay"]:
        if not isinstance(e["start"], str) or not DATE_ONLY.fullmatch(e["start"]):
            raise ValueError(f"{eid}: all-day start must be YYYY-MM-DD")
        start_date = dt.date.fromisoformat(e["start"])
        if "end" in e and e["end"] is not None:
            if not DATE_ONLY.fullmatch(e["end"]) or dt.date.fromisoformat(e["end"]) <= start_date:
                raise ValueError(f"{eid}: all-day end must be an exclusive later date")
    else:
        start = parse_time(e["start"], "start")
        start_date = start.date()
        if e.get("end") is not None and parse_time(e["end"], "end") <= start:
            raise ValueError(f"{eid}: end must be later than start")
    if start_date < today - dt.timedelta(days=14) or start_date > today + dt.timedelta(days=450):
        raise ValueError(f"{eid}: outside allowed date window")
    if operation == "cancel":
        if e.get("status") != "cancelled":
            raise ValueError(f"{eid}: cancellation status required")
    elif e.get("status", "confirmed") != "confirmed":
        raise ValueError(f"{eid}: upsert status must be confirmed")
    if e.get("confidence", "high") != "high":
        raise ValueError(f"{eid}: confidence must be high")
    e.setdefault("status", "confirmed")
    e.setdefault("confidence", "high")
    e.setdefault("persons", [])
    e.setdefault("url", e["sourceUrls"][0])
    return e


def baseline():
    paths = [
        build.EVENTS_PATH, build.SHADOWVERSE_EVENTS_PATH, build.DISCOVERED_EVENTS_PATH,
        build.STREAMER_LEAGUE_EVENTS_PATH, build.SHADOWVERSE_OCS_EVENTS_PATH,
        build.SHADOWVERSE_MAJOR_EVENTS_PATH, build.AUTOMATION_EVENTS_PATH,
        build.AUTOMATION_DELTA_EVENTS_PATH, build.EVENT_OVERRIDES_PATH,
        build.AUTOMATION_LATEST_EVENTS_PATH, build.AUTOMATION_INBOX_EVENTS_PATH,
        build.AUTOMATION_TGS_EVENTS_PATH, build.AUTOMATION_20260925_EVENTS_PATH,
    ]
    groups = [(p, build.load_events(p)) for p in paths]
    groups.append((build.SFL_SCHEDULE_PATH, build.build_sfl_events(build.SFL_SCHEDULE_PATH)))
    return {e["id"]: e for e in build.merge_events(groups)}


def apply(proposal, current, existing, today):
    if not isinstance(proposal, dict) or proposal.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    changes = proposal.get("changes")
    if not isinstance(changes, list) or len(changes) > 100:
        raise ValueError("changes must be an array with <=100 entries")
    # Hourly polling sees the last proposal long after it was merged. Exact
    # matches to the trusted overlay need no new verification or data write.
    current_by_id = {e["id"]: e for e in current}
    if changes and all(
        isinstance(item, dict)
        and item.get("operation") in {"upsert", "cancel"}
        and isinstance(item.get("event"), dict)
        and isinstance(item["event"].get("id"), str)
        and item["event"] == current_by_id.get(item["event"]["id"])
        and item["event"].get("status") == ("cancelled" if item["operation"] == "cancel" else "confirmed")
        for item in changes
    ):
        ids = [item["event"]["id"] for item in changes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate proposal ID")
        return sorted(current, key=lambda x: (x["start"], x["id"])), 0
    if changes:
        generated = parse_time(proposal.get("generated_at"), "generated_at")
        if generated.date() > today + dt.timedelta(days=1) or generated.date() < today - dt.timedelta(days=7):
            raise ValueError("proposal is stale or future-dated")
    new_by_id = {e["id"]: e for e in current}
    all_by_id = {**existing, **new_by_id}
    ids_seen = set()
    accepted = 0
    for item in changes:
        if not isinstance(item, dict) or item.get("operation") not in {"upsert", "cancel"}:
            raise ValueError("unknown operation")
        e = validate(item.get("event"), item["operation"], today)
        eid = e["id"]
        if eid in ids_seen:
            raise ValueError(f"duplicate proposal ID {eid}")
        ids_seen.add(eid)
        previous = all_by_id.get(eid)
        if item["operation"] == "cancel" and previous is None:
            raise ValueError(f"cannot cancel unknown ID {eid}")
        if previous:
            old_checked = previous.get("verified_at")
            if old_checked and parse_time(old_checked, "existing verified_at") > parse_time(e["verified_at"], "verified_at"):
                continue
            if previous.get("status") == "cancelled" and item["operation"] != "cancel":
                raise ValueError(f"reopening cancellation requires manual review: {eid}")
        else:
            title = normalize_title(e["title"])
            date = e["start"][:10]
            for old in all_by_id.values():
                if old.get("status") == "cancelled" or str(old.get("start", ""))[:10] != date:
                    continue
                other_title = normalize_title(old.get("title", ""))
                similarity = difflib.SequenceMatcher(None, title, other_title).ratio()
                if title == other_title or (similarity >= 0.88 and e["start"] == old.get("start")):
                    raise ValueError(f"possible duplicate: {eid} ~ {old.get('id')} ({similarity:.2f})")
        if previous and all(previous.get(k) == v for k, v in e.items()):
            continue
        new_by_id[eid] = e
        all_by_id[eid] = e
        accepted += 1
    return sorted(new_by_id.values(), key=lambda x: (x["start"], x["id"])), accepted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proposal", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    if args.proposal.stat().st_size > 256_000:
        raise ValueError("proposal exceeds 256KB")
    data = json.loads(args.proposal.read_text(encoding="utf-8-sig"))
    current = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else []
    if not isinstance(current, list):
        raise ValueError("current events must be an array")
    next_events, accepted = apply(data, current, baseline(), dt.datetime.now(JST).date())
    old = json.dumps(current, ensure_ascii=False, sort_keys=True)
    new = json.dumps(next_events, ensure_ascii=False, sort_keys=True)
    if old != new:
        args.output.write_text(json.dumps(next_events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Accepted {accepted} changes; output changed={old != new}; total overlay events={len(next_events)}")


if __name__ == "__main__":
    main()
