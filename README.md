# Streamer Event Calendar

特定の配信者の出演イベントと、主要なストリートファイター6大会をまとめる静的Webカレンダーです。

## 対象

- たいじ
- もこう
- 加藤純一
- なるお
- あっさりしょこ
- バトラ
- ストリートファイター6の主要大会

## 公開URL

GitHub Pagesを有効化すると、次のURLで公開されます。

- Web: `https://mmiyaji.github.io/streamer-event-calendar/`
- 全イベントICS: `https://mmiyaji.github.io/streamer-event-calendar/calendar.ics`
- 配信者ICS: `https://mmiyaji.github.io/streamer-event-calendar/streamers.ics`
- SF6 ICS: `https://mmiyaji.github.io/streamer-event-calendar/sf6.ics`

## データ更新

イベントは `data/events.json` に保存します。`main` ブランチへの更新時にGitHub ActionsがICSを生成し、GitHub Pagesへデプロイします。

### イベント形式

```json
{
  "id": "unique-event-id",
  "title": "イベント名",
  "category": "streamer",
  "persons": ["たいじ"],
  "start": "2026-08-01T13:00:00+09:00",
  "end": "2026-08-01T18:00:00+09:00",
  "allDay": false,
  "location": "会場名",
  "url": "https://example.com/event",
  "sourceUrls": ["https://example.com/announcement"],
  "status": "confirmed",
  "confidence": "high",
  "lastChecked": "2026-07-23T07:00:00+09:00",
  "notes": "補足"
}
```

`category` は `streamer` または `sf6`、`confidence` は `high` または `medium` を公開対象とします。
