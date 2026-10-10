"""Exercise the installed PowerShell publisher against isolated local Git repos."""
import datetime as dt
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_codex_proposals.ps1"


@unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows publisher")
class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="calendar-transfer-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.repo = self.root / "sync-repo"
        self.outbox = self.root / "proposal.json"
        self.git("init", "--bare", str(self.remote))
        self.git("clone", str(self.remote), str(self.repo))
        self.git("config", "user.name", "Publisher Test", cwd=self.repo)
        self.git("config", "user.email", "test@example.invalid", cwd=self.repo)
        self.git("switch", "-c", "codex/calendar-updates", cwd=self.repo)
        (self.repo / "data").mkdir()
        (self.repo / "data/codex_proposals.json").write_text('{"schema_version":1,"changes":[]}', encoding="utf-8")
        self.git("add", ".", cwd=self.repo)
        self.git("commit", "-m", "isolated test seed", cwd=self.repo)
        self.git("push", "origin", "HEAD", cwd=self.repo)

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()

    def proposal(self, changes):
        self.outbox.write_text(json.dumps({"schema_version": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "changes": changes}), encoding="utf-8")
        os.utime(self.outbox, (0, 0))

    def run_publisher(self):
        return subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), "-Outbox", str(self.outbox), "-SyncRepo", str(self.repo)], capture_output=True, text=True, timeout=30)

    def test_empty_does_not_commit(self):
        before = self.git("rev-parse", "HEAD", cwd=self.repo)
        self.proposal([])
        result = self.run_publisher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No proposed changes", result.stdout)
        self.assertEqual(before, self.git("rev-parse", "HEAD", cwd=self.repo))

    def test_publish_and_repeat_without_network_with_old_lock_file(self):
        # Payload is a transport fixture only, never sent to GitHub or public data.
        self.proposal([{"operation": "transport-test"}])
        (self.root / "publish.lock").touch()
        first = self.run_publisher()
        self.assertEqual(first.returncode, 0, first.stderr)
        remote_json = self.git("--git-dir", str(self.remote), "show", "codex/calendar-updates:data/codex_proposals.json")
        self.assertEqual(json.loads(remote_json), json.loads(self.outbox.read_text()))
        self.git("remote", "set-url", "origin", str(self.root / "missing.git"), cwd=self.repo)
        second = self.run_publisher()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("no network request", second.stdout)

    def test_failed_push_retries_without_receipt(self):
        self.proposal([{"operation": "transport-test"}])
        self.git("remote", "set-url", "--push", "origin", str(self.root / "missing.git"), cwd=self.repo)
        failed = self.run_publisher()
        self.assertNotEqual(failed.returncode, 0)
        self.assertFalse((self.root / "published.sha256").exists())
        self.git("config", "--unset", "remote.origin.pushurl", cwd=self.repo)
        retried = self.run_publisher()
        self.assertEqual(retried.returncode, 0, retried.stderr)
        self.assertTrue((self.root / "published.sha256").exists())

    def test_non_array_changes_rejected(self):
        self.proposal({"operation": "transport-test"})
        result = self.run_publisher()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "published.sha256").exists())


if __name__ == "__main__":
    unittest.main()
