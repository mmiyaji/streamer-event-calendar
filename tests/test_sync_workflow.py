"""Run the production Actions scripts against local Git and a simulated GitHub CLI."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
BASH = shutil.which("bash")
if os.name == "nt":
    BASH = Path(shutil.which("git")).parents[1] / "bin/bash.exe"


class SyncWorkflowTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "work"
        self.repo.mkdir()
        self.git("init", "--bare", "../remote.git")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.git("remote", "add", "origin", "../remote.git")
        self.overlay = self.repo / "data/codex_synced_events.json"
        self.overlay.parent.mkdir()
        self.overlay.write_bytes(b"[]\n")
        self.git("add", "data")
        self.git("commit", "-m", "baseline")
        self.git("push", "-u", "origin", "main")
        self.mock = self.root / "github.sh"

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True,
                              capture_output=True, text=True).stdout.strip()

    def workflow(self, name, *args):
        return subprocess.run([str(BASH), (SCRIPTS / name).as_posix(), *args], cwd=self.repo,
                              env={**os.environ, "BASH_ENV": self.mock.as_posix()},
                              capture_output=True, text=True, timeout=60)

    def test_retry_creates_pr_without_second_push(self):
        self.mock.write_text("""
gh() {
  case "$1 $2" in
    'pr list') if [[ -f ../open ]]; then echo 1; fi ;;
    'pr create') echo create >> ../attempts; [[ -f ../allow ]] || return 1; touch ../open ;;
    *) return 99 ;;
  esac
}
""", encoding="utf-8", newline="\n")
        args = ("refresh_calendar_pr.sh", "../validated.json")
        validated = self.root / "validated.json"
        validated.write_bytes(b'[{"id":"sample"}]\n')
        self.overlay.write_bytes(validated.read_bytes())
        self.assertNotEqual(self.workflow(*args).returncode, 0)
        pushed = self.git("rev-parse", "origin/automation/codex-sync")
        self.assertEqual(self.git("show", f"{pushed}:data/codex_synced_events.json"), '[{"id":"sample"}]')
        self.git("switch", "main")
        self.overlay.write_bytes(validated.read_bytes())
        (self.root / "allow").touch()
        for _ in range(2):
            result = self.workflow(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.git("rev-parse", "origin/automation/codex-sync"), pushed)
        self.assertEqual((self.root / "attempts").read_text().splitlines(), ["create", "create"])

    def test_missing_publication_retries_until_deployed(self):
        self.mock.write_text("""
gh() {
  case "$1 $2" in
    'run list')
      case " $* " in
        *' --status success '*) cat ../published ;;
        *" --commit $(git rev-parse origin/main) "*) cat ../status ;;
        *) return 99 ;;
      esac ;;
    'workflow run')
      [[ "$*" == 'workflow run pages.yml --ref main' ]] || return 99
      echo dispatch >> ../attempts
      [[ -f ../allow ]] || return 1
      echo queued > ../status ;;
    *) return 99 ;;
  esac
}
""", encoding="utf-8", newline="\n")
        published = self.root / "published"
        status = self.root / "status"
        published.write_text(self.git("rev-parse", "main"))
        status.touch()
        self.overlay.write_bytes(b'[{"id":"merged"}]\n')
        self.git("commit", "-am", "merge calendar data")
        self.git("push")
        script = "reconcile_calendar_pages.sh"
        self.assertNotEqual(self.workflow(script).returncode, 0)
        (self.root / "allow").touch()
        for state in ("", "in_progress", "completed"):
            status.write_text(state)
            result = self.workflow(script)
            self.assertEqual(result.returncode, 0, result.stderr)
        published.write_text(self.git("rev-parse", "main"))
        (self.repo / "README.md").write_text("docs")
        self.git("add", "README.md")
        self.git("commit", "-m", "docs only")
        self.git("push")
        status.write_text("completed")
        result = self.workflow(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "attempts").read_text().splitlines(), ["dispatch"] * 3)
