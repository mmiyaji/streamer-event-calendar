#!/usr/bin/env python3
"""Validate Codex-produced proposal JSON; does not modify calendar data."""
import datetime
import json
import sys
from urllib.parse import urlparse

def check(data):
    assert isinstance(data, dict) and data.get("schema_version") == 1
    changes = data.get("changes")
    assert isinstance(changes, list) and len(changes) <= 100
    ids = set()
    for item in changes:
        assert item.get("operation") in ("upsert", "cancel")
        e = item.get("event")
        assert isinstance(e, dict)
        for key in ("id", "title", "category", "type", "game", "priority", "source",
                    "official", "region", "tags", "verified_at", "lastChecked", "start",
                    "allDay", "sourceUrls"):
            assert key in e, f"missing {key}"
        assert isinstance(e["id"], str) and e["id"] and e["id"] not in ids
        ids.add(e["id"])
        assert e["category"] in ("streamer", "sf6", "shadowverse_wb", "pokemon")
        assert e["type"] in ("tournament", "qualifier", "update", "stream", "offline_event")
        assert e["priority"] in ("major", "normal")
        assert e["official"] is True and isinstance(e["tags"], list)
        assert e["verified_at"] == e["lastChecked"]
        assert isinstance(e["allDay"], bool)
        datetime.date.fromisoformat(e["start"][:10])
        assert e["sourceUrls"] and all(urlparse(u).scheme == "https" for u in e["sourceUrls"])
        if e["category"] == "sf6": assert e["game"] == "sf6"
        if e["category"] == "shadowverse_wb": assert e["game"] == "shadowverse_wb"
    print(f"Validated {len(changes)} proposals; manual review required before merge.")

if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        check(json.load(f))
