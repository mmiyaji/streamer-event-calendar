# Event Calendar

特定の配信者の出演イベント、主要なストリートファイター6大会・予告アップデート、Shadowverse: Worlds Beyondの大会・大型イベント・予告アップデートをまとめる個人利用目的の静的Webカレンダーです。

このカレンダーは個人の情報整理と予定確認のために運用しています。掲載対象、選定基準、情報の優先度は作成者個人の関心や好みに基づくものであり、イベントを網羅するものではありません。

掲載内容はWeb上の公開情報をもとに自動または半自動で整理するため、誤り、更新遅延、予定変更の未反映が含まれる場合があります。正確な日時・出演情報については、各イベントの公式情報をご確認ください。

## 対象

- たいじ
- もこう
- 加藤純一
- なるお
- あっさりしょこ
- バトラ
- ストリートファイター6の主要大会と事前告知された主要アップデート
- Shadowverse: Worlds Beyondのプロリーグ、大規模大会・イベント、事前告知された主要アップデート

## 情報源の優先順位

### 配信者イベント

1. 本人・所属先・主催者の公式告知
2. イベント公式サイト、公式配信ページ、チケットページ
3. 信頼できるゲーム・エンタメ媒体
4. 複数の関連出演者による一致した告知

### ストリートファイター6

1. CAPCOM、Street Fighter 6公式サイト、Capcom Pro Tour、大会主催者などの公式情報
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

## SF6の掲載ルール

### 大会

- 本戦、グループステージ、プレーオフ、Top 8、決勝を掲載対象とします。
- Last Chance Qualifier（LCQ）、オープン予選、地域予選など、本戦出場権に関係する重要な予選も掲載対象とします。
- 予選イベントは、本戦との混同を避けるためタイトル先頭に `【予選】` を付けます。
- チェックイン、エントリー締切、練習日、メディアデーのみの日程は原則として掲載しません。

### 予告アップデート

- 新キャラクター、新シーズン、大規模バランス調整、主要システム変更、新ステージなど、影響の大きいアップデートを掲載対象とします。
- 公式情報で具体的な実施日が確認できたものだけ登録し、タイトル先頭に `【アップデート】` を付けます。
- 「夏」「秋」「2027年初頭」など時期だけが発表されているものは、具体的な日付が決まるまで登録しません。
- 通常メンテナンス、軽微な不具合修正、短期キャンペーンのみの更新は原則として除外します。
- 配信開始時刻やメンテナンス時間が未発表の場合は終日予定として登録し、判明後に更新します。

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
  "category": "sf6",
  "type": "tournament",
  "game": "sf6",
  "priority": "major",
  "source": "official",
  "official": true,
  "region": "jp",
  "tags": ["cpt", "premier"],
  "verified_at": "2026-07-24T18:00:00+09:00",
  "persons": [],
  "start": "2026-08-01T13:00:00+09:00",
  "end": "2026-08-01T18:00:00+09:00",
  "allDay": false,
  "location": "会場名",
  "url": "https://example.com/event",
  "sourceUrls": ["https://example.com/announcement"],
  "status": "confirmed",
  "confidence": "high",
  "lastChecked": "2026-07-24T18:00:00+09:00",
  "notes": "補足"
}
```

### メタデータ

- `category`: UIとICSの大分類。`streamer`、`sf6`、`shadowverse_wb`
- `type`: 内容の種類。`tournament`、`qualifier`、`update`、`stream`、`offline_event`
- `game`: 対象ゲーム。`sf6`、`shadowverse_wb`。配信者イベントでゲームを特定しない場合は `null`
- `priority`: 重要度。`major` または `normal`
- `source`: 主に採用した情報源。`official`、`kakuge-checker`、`rage`、`premier-series`、`media` など
- `official`: 主情報源が公式情報なら `true`
- `region`: 主な対象地域。`jp` または `global`
- `tags`: 検索・表示フィルター向けの補助分類
- `verified_at`: LLMまたは運営者が内容を最後に確認した日時

既存互換性のため `lastChecked` も保持します。当面は `verified_at` と同じ日時を設定します。`confidence` は `high` または `medium` を公開対象とします。
