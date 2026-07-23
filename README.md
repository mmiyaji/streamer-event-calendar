# Streamer Event Calendar

特定の配信者の出演イベントと、主要なストリートファイター6大会をまとめる個人利用目的の静的Webカレンダーです。

このカレンダーは個人の情報整理と予定確認のために運用しています。掲載対象、選定基準、情報の優先度は作成者個人の関心や好みに基づくものであり、配信者・大会・イベントを網羅するものではありません。

掲載内容はWeb上の公開情報をもとに自動または半自動で整理するため、誤り、更新遅延、予定変更の未反映が含まれる場合があります。正確な日時・出演情報については、各イベントの公式情報をご確認ください。

## 対象

以下の一覧は、知名度・人気・客観的評価による選定ではなく、作成者個人の好みによるものです。

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
