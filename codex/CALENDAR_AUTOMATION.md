# Codex recurring task: update public gaming event calendar

Run this task at 07:00 and 19:00 Asia/Tokyo in the Codex desktop app.
This is a DATA GENERATION task, not a GitHub write task.

## Objective
Research confirmed schedule changes for:
- Streamers: たいじ, もこう, 加藤純一, なるお, あっさりしょこ, バトラ, じゃすぱー.
- Official events: Crazy Raccoon, げまげま/Gamers×Gamers, CR Cup, CR Streamer League, The k4sen, RAGE, CAPCOM eSports, Shadowverse: Worlds Beyond, Shadowverse Premier Series.
- Official accounts for regular streamer communities, units and programs (e.g. Blood Party Friday).
- Major SF6 tournaments/qualifiers/character and balance updates.
- Shadowverse: Worlds Beyond professional leagues/major tournaments/announced major updates.
- Pokémon 30th major goods announcements when a confirmed purchase or preorder date is published.

Use primary official websites, verified organizer/participant social accounts and the original announcement URL. Cross-check streamer appearances both via the organizer and via the person or team. Do NOT hallucinate dates or times. Events with no exact date must not enter the JSON. Do not re-create older events with a different ID.

## Input: Current authoritative calendar
Inspect the checked-out repo and published https://mmiyaji.github.io/streamer-event-calendar/events.json
before generating changes. Check against all existing IDs and the same-day titles, including
data/codex_synced_events.json and legacy event JSON. A repeated announcement with no substantive change is NOT a diff.

## Output: exactly one UTF-8 JSON file
Write to %LOCALAPPDATA%\StreamerEventCalendar\outbox\codex_proposals.json
on Windows (expand LOCALAPPDATA to its actual path).
Create the outbox directory if necessary.
Write a temporary file in that same directory, validate it with a JSON parser,
then atomically replace codex_proposals.json. NEVER write the final file incrementally.
Before replacement, run `python scripts/validate_codex_proposals.py <temporary-file>`.
For full validation against existing IDs and duplicate rules, run
`python scripts/apply_codex_proposals.py --proposal <temporary-file> --output <temporary-overlay>`
using a temporary copy of data/codex_synced_events.json (or [] if absent).
Never use the production overlay as --output. On validation failure, preserve the last
valid outbox file and report the failure. Local transfer polls hourly at minute 05;
it does not need to be invoked by this task.
You MUST NOT git push, use a PAT, alter repo configuration, or change production source files.

Use:
{
  "schema_version": 1,
  "generated_at": "2026-10-11T07:00:00+09:00",
  "changes": [
    {
      "operation": "upsert",
      "event": {
        "id": "streamer-example-tournament-2026",
        "title": "イベントの正確な名称",
        "category": "streamer",
        "type": "tournament",
        "game": "sf6",
        "priority": "major",
        "source": "official",
        "official": true,
        "region": "jp",
        "tags": ["sf6", "streamer"],
        "verified_at": "2026-10-11T07:00:00+09:00",
        "lastChecked": "2026-10-11T07:00:00+09:00",
        "persons": ["なるお"],
        "start": "2026-10-18",
        "allDay": true,
        "sourceUrls": ["https://example.com/actual-official-announcement"],
        "url": "https://example.com/actual-official-announcement",
        "confidence": "high",
        "status": "confirmed",
        "notes": "公式で確認できた内容のみ"
      }
    }
  ]
}

Example URLs are placeholders ONLY: never put example.com in actual proposals.
For start of timed events use ISO 8601 with +09:00; allDay events must use YYYY-MM-DD.
End of an all-day multi-day event is an exclusive date, or omit end.
type must be tournament/qualifier/update/stream/offline_event.
priority is major/normal. Region is jp/global/asia/emeaa/americas/eu.
category is streamer/sf6/shadowverse_wb/pokemon.
For streamer appearances related to SF6 or Shadowverse, set category=streamer and
game=sf6 or shadowverse_wb for inclusion in both ICS feeds.
For cancellation use operation=cancel and status=cancelled, preserving the exact existing ID.
Set verified_at and lastChecked to the same actual verification timestamp.
Put clear evidence in notes, include a real HTTPS announcement URL, and use stable IDs.
Keep changes empty when no genuine new/changed/cancelled event is verified.

## Output summary
After atomically writing the file, report in Japanese:
new/updated/cancelled counts, titles/dates, organizer/source URLs, and uncertainties.
If official pages cannot be accessed, report the failure without fabricating changes.
Do not treat an inaccessible source as proof that there are no changes. Report partial
coverage explicitly. Stay quiet on normal runs with no changes; notify only for verified
changes, failures, or required user action.
Do not report any GitHub publication as completed: transfer and publication are separate.
