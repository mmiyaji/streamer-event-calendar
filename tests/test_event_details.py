"""Exercise the site's event-click handler in a headless browser without the CDN."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

SITE = Path(__file__).resolve().parents[1] / "site"
CHROME = shutil.which("google-chrome") or shutil.which("chromium")
if not CHROME and os.name == "nt":
    for base, path in [("ProgramFiles", "Google/Chrome/Application/chrome.exe"),
                       ("ProgramFiles(x86)", "Microsoft/Edge/Application/msedge.exe")]:
        candidate = Path(os.environ.get(base, "")) / path
        if candidate.is_file():
            CHROME = str(candidate)
            break


@unittest.skipUnless(CHROME, "Chrome or Chromium required for the browser test")
class EventDetailTests(unittest.TestCase):
    def test_event_click_renders_text_links_and_dates(self):
        # Supply only FullCalendar's public eventClick interface and an empty feed.
        # The page registers its own handler and uses the browser's real dialog/DOM.
        stub = """<script>
        window.fetch = async () => ({ok:true, json:async () => []});
        window.FullCalendar = {Calendar: class {
          constructor(el, options) { window.clickEvent = options.eventClick; }
          render() {}
        }};
        </script>"""
        checks = """<script>
        window.addEventListener('load', () => {
          const body = document.querySelector('#detail-body');
          const dialog = document.querySelector('#detail');
          const mark = '<em>会場案内</em>';
          const event = {title: mark, start: new Date(2026, 6, 31), end: new Date(2026, 7, 1),
            allDay: true, extendedProps: {persons: [mark], notes: mark, location: mark, url: 'https://example.org/'}};
          function check(value, description) { if (!value) throw Error(description); }
          function open() { if (dialog.open) dialog.close(); clickEvent({event}); }
          try {
            open();
            check(dialog.open, 'dialog opened');
            check(document.querySelector('#detail-title').textContent === mark, 'plain title');
            check(!body.querySelector('em') && body.textContent.split(mark).length === 4, 'plain detail fields');
            check(body.querySelector('a').href === event.extendedProps.url, 'source link');
            check(body.firstChild.textContent === '日時: 2026/7/31', 'single day');
            event.end = new Date(2026, 7, 3);
            for (const url of ['http://example.org/', '/relative', 'invalid']) {
              event.extendedProps.url = url;
              open();
              check(!body.querySelector('a'), 'invalid link cleared');
              check(body.firstChild.textContent === '日時: 2026/7/31 ～ 2026/8/2', 'multi-day end');
            }
            event.end = null;
            open();
            check(body.firstChild.textContent === '日時: 2026/7/31', 'no explicit end');
            event.allDay = false;
            event.end = new Date(2026, 6, 31, 12, 30);
            open();
            check(body.firstChild.textContent.endsWith(event.end.toLocaleString('ja-JP')), 'timed end');
            document.body.dataset.testResult = 'passed';
          } catch (error) { document.body.dataset.testResult = error.message; }
        });
        </script>"""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            html = (SITE / "index.html").read_text(encoding="utf-8")
            html, count = re.subn(r'<script src="https://[^"]*fullcalendar[^"]*"></script>', stub, html)
            self.assertEqual(count, 1)
            page = root / "index.html"
            page.write_text(html.replace("</body>", checks + "</body>"), encoding="utf-8")
            shutil.copyfile(SITE / "event-detail.js", root / "event-detail.js")
            result = subprocess.run(
                [CHROME, "--headless", "--disable-gpu", "--disable-background-networking",
                 "--no-first-run", "--disable-extensions", f"--user-data-dir={root / 'profile'}",
                 "--dump-dom", page.as_uri()], capture_output=True, timeout=60, check=True,
            )
            outcome = re.search(rb'<body[^>]* data-test-result="([^"]*)"', result.stdout)
            self.assertIsNotNone(outcome, result.stderr[-1000:])
            self.assertEqual(outcome[1], b"passed")
