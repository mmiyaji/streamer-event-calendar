import copy
import datetime as dt
import sys
import unittest
import json
import tempfile
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apply_codex_proposals as mod

TODAY = dt.datetime.now(mod.JST).date()
STAMP = dt.datetime.now(mod.JST).isoformat(timespec="seconds")


def event(eid="streamer-sample-calendar-test"):
    return {
        "id": eid, "title": "Sample Confirmed Tournament",
        "category": "streamer", "type": "tournament", "game": "sf6",
        "priority": "major", "source": "official", "official": True,
        "region": "jp", "tags": ["test"], "persons": ["なるお"],
        "verified_at": STAMP, "lastChecked": STAMP,
        "start": (TODAY + dt.timedelta(days=7)).isoformat(),
        "allDay": True, "url": "https://example.org/real-source",
        "sourceUrls": ["https://example.org/real-source"],
        "status": "confirmed", "confidence": "high", "notes": "Unit test only",
    }


def proposal(changes):
    return {"schema_version": 1, "generated_at": STAMP, "changes": changes}


class ApplyCodexTests(unittest.TestCase):
    def test_build_preserves_approved_sfl_appearance(self):
        e = mod.build.build_sfl_events(mod.build.SFL_SCHEDULE_PATH)[0]
        e.update(category="streamer", persons=["なるお"], notes="Approved appearance overlay")
        with tempfile.TemporaryDirectory(prefix="calendar-build-") as folder:
            root = Path(folder)
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps([e], ensure_ascii=False), encoding="utf-8")
            with patch.object(mod.build, "CODEX_SYNCED_EVENTS_PATH", overlay), patch.object(mod.build, "DIST_DIR", root / "dist"):
                mod.build.main()
            events = json.loads((root / "dist/events.json").read_text(encoding="utf-8"))
            actual = next(item for item in events if item["id"] == e["id"])
            self.assertEqual(actual, e)
            self.assertIn(e["id"], (root / "dist/streamers.ics").read_text(encoding="utf-8"))
            self.assertIn(e["id"], (root / "dist/sf6.ics").read_text(encoding="utf-8"))

    def test_no_changes_is_noop(self):
        result, count = mod.apply(proposal([]), [], {}, TODAY)
        self.assertEqual((result, count), ([], 0))

    def test_new_event(self):
        e = event()
        result, count = mod.apply(proposal([{"operation": "upsert", "event": e}]), [], {}, TODAY)
        self.assertEqual(count, 1)
        self.assertEqual(result[0]["id"], e["id"])

    def test_same_event_is_idempotent(self):
        e = event()
        result, count = mod.apply(proposal([{"operation": "upsert", "event": e}]), [e], {}, TODAY)
        self.assertEqual(count, 0)
        self.assertEqual(len(result), 1)

    def test_duplicate_id_with_different_id_rejected(self):
        first, second = event(), event("streamer-another-calendar-test")
        with self.assertRaisesRegex(ValueError, "possible duplicate"):
            mod.apply(proposal([{"operation": "upsert", "event": second}]), [], {first["id"]: first}, TODAY)

    def test_cancel_requires_known_id(self):
        e = event()
        e["status"] = "cancelled"
        with self.assertRaisesRegex(ValueError, "unknown ID"):
            mod.apply(proposal([{"operation": "cancel", "event": e}]), [], {}, TODAY)

    def test_cancel_known_id(self):
        e = event()
        old = copy.deepcopy(e)
        e["status"] = "cancelled"
        result, count = mod.apply(proposal([{"operation": "cancel", "event": e}]), [old], {}, TODAY)
        self.assertEqual(count, 1)
        self.assertEqual(result[0]["status"], "cancelled")

    def test_http_source_rejected(self):
        e = event()
        e["sourceUrls"] = ["http://example.org/unsafe"]
        with self.assertRaisesRegex(ValueError, "source URLs"):
            mod.apply(proposal([{"operation": "upsert", "event": e}]), [], {}, TODAY)

    def test_already_applied_stale_proposal_is_noop(self):
        e = event()
        old_stamp = (dt.datetime.now(mod.JST) - dt.timedelta(days=20)).isoformat()
        e["verified_at"] = e["lastChecked"] = old_stamp
        p = {"schema_version": 1, "generated_at": old_stamp,
             "changes": [{"operation": "upsert", "event": copy.deepcopy(e)}]}
        result, count = mod.apply(p, [e], {}, TODAY)
        self.assertEqual((result, count), ([e], 0))
        p["changes"][0]["event"]["title"] = "Changed stale tournament title"
        with self.assertRaisesRegex(ValueError, "stale"):
            mod.apply(p, [e], {}, TODAY)

    def test_date_unknown_rejected(self):
        e = event()
        e["start"] = "2026-10"
        with self.assertRaisesRegex(ValueError, "all-day start"):
            mod.apply(proposal([{"operation": "upsert", "event": e}]), [], {}, TODAY)


if __name__ == "__main__":
    unittest.main()
