# Event Calendar

特定の配信者の出演イベント、主要なストリートファイター6大会、Shadowverse: Worlds Beyondの大会・大型イベント・予告アップデートをまとめる個人利用目的の静的Webカレンダーです。

このカレンダーは個人の情報整理と予定確認のために運用しています。掲載対象、選定基準、情報の優先度は作成者個人の関心や好みに基づくものであり、イベントを網羅するものではありません。

掲載内容はWeb上の公開情報をもとに自動または半自動で整理するため、誤り、更新遅延、予定変更の未反映が含まれる場合があります。正確な日時・出演情報については、各イベントの公式情報をご確認ください。

## 対象

- たいじ
- もこう
- 加藤純一
- なるお
- あっさりしょこ
- バトラ
- ストリートファイター6の主要大会
- Shadowverse: Worlds Beyondのプロリーグ、大規模大会・イベント、事前告知された主要アップデート

## 情報源の優先順位

### 配信者イベント

1. 本人・所属先・主催者の公式告知
2. イベント公式サイト、公式配信ページ、チケットページ
3. 信頼できるゲーム・エンタメ媒体
4. 複数の関連出演者による一致した告知

### ストリートファイター6大会

1. CAPCOM、Capcom Pro Tour、大会主催者などの公式情報
2. **格ゲーチェッカー**
3. start.gg、Liquipediaなどの大会情報サービス
4. 信頼できるeスポーツ・ゲーム媒体
5. 選手・チームの公式告知

### Shadowverse: Worlds Beyond

1. Shadowverse: Worlds Beyond公式サイト・公式ニュース
2. Shadowverse Premier Series、RAGEなど各大会の公式サイト
3. Cygamesおよび大会主催者の公式SNS・配信告知
4. 信頼できるゲーム・eスポーツ媒体

掲載対象は、Premier Seriesなどのプロリーグ、RAGE・国際大会・World Grand Prix関連大会などの大型競技イベント、公式オフラインイベント、実施日が事前発表された大型アップデートや新カードパックです。小規模キャンペーン、通常メンテナンス、修正パッチのみの更新は原則として除外します。

## SF6大会の掲載ルール

- 本戦、グループステージ、プレーオフ、Top 8、決勝を掲載対象とします。
- Last Chance Qualifier（LCQ）、オープン予選、地域予選など、本戦出場権に関係する重要な予選も掲載対象とします。
- 予選イベントは、本戦との混同を避けるためタイトル先頭に `【予選】` を付けます。
- チェックイン、エントリー締切、練習日、メディアデーのみの日程は原則として掲載しません。

## 公開URL

- Web: `https://mmiyaji.github.io/streamer-event-calendar/`
- 全イベントICS: `https://mmiyaji.github.io/streamer-event-calendar/calendar.ics`
- 配信者ICS: `https://mmiyaji.github.io/streamer-event-calendar/streamers.ics`
- SF6 ICS: `https://mmiyaji.github.io/streamer-event-calendar/sf6.ics`
- Shadowverse WB ICS: `https://mmiyaji.github.io/streamer-event-calendar/shadowverse-wb.ics`

## データ更新

通常イベントは `data/events.json`、Shadowverse WBイベントは `data/shadowverse_wb_events.json` に保存します。`main` ブランチへの更新時にGitHub Actionsが統合JSONと各ICSを生成し、GitHub Pagesへデプロイします。

### イベント形式

```json
{
  "id": "unique-event-id",
  "title": "イベント名",
  "category": "shadowverse_wb",
  "persons": [],
  "start": "2026-08-01T13:00:00+09:00",
  "end": "2026-08-01T18:00:00+09:00",
  "allDay": false,
  "location": "会場名",
  "url": "https://example.com/event",
  "sourceUrls": ["https://example.com/announcement"],
  "status": "confirmed",
  "confidence": "high",
  "lastChecked": "2026-07-23T17:00:00+09:00",
  "notes": "補足"
}
```

`category` は `streamer`、`sf6`、`shadowverse_wb`、`confidence` は `high` または `medium` を公開対象とします。
