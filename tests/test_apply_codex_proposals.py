import copy
import datetime as dt
import sys
import unittest
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

    def test_date_unknown_rejected(self):
        e = event()
        e["start"] = "2026-10"
        with self.assertRaisesRegex(ValueError, "all-day start"):
            mod.apply(proposal([{"operation": "upsert", "event": e}]), [], {}, TODAY)


if __name__ == "__main__":
    unittest.main()
