# Codex → GitHub Actions カレンダー自動更新

## 目的と責任分界

- **Codexデスクトップ定期タスク**：公式情報巡回、既存データとの比較、差分JSON作成。OpenAI APIキー不要。
- **Windowsタスクスケジューラ**：毎時05分（PCのローカル時刻）に完成したJSONのみGitで codex/calendar-updates にPush。Git認証はGit Credential Manager。
- **GitHub Actions（sync-codex.yml）**：毎時17分UTCにブランチからJSONのみFetch。mainの信頼済みPythonで検証・ICSビルドし、データ専用PRを作成/更新。
- **GitHub Pages**：PRがmainにマージされたら既存Pagesワークフローが発火し、ICSとWebを更新。

GitHub Actionsが取り込むのは data/codex_proposals.json **のみ**です。
Codexブランチ上のPython/WorkflowをGitHub Actionsでは実行しません。

## 実行頻度と更新までの流れ

| 処理 | タイミング | 成果物 |
| --- | --- | --- |
| Codexによる公式情報確認 | 毎日07:00・19:00（Asia/Tokyo） | ローカルoutboxの差分JSON |
| Windowsによる転送 | 毎時05分・実行を逃した場合は復帰後 | codex/calendar-updatesのJSON |
| GitHub Actionsによる検証・取り込み | 毎時17分UTC（日本時間も毎時17分） | automation/codex-syncからmainへの差分PR |
| 公開 | 人がPRを確認してマージした後 | Web・各ICS |

調査は終了時刻が一定ではないため、転送は時刻固定の1日2回ではなく1時間間隔にします。
調査終了から転送まで通常最大1時間、取り込みまでさらに通常最大1時間が目安です。
GitHubの予約実行は遅延する場合があり、公開時刻はPRの確認・マージにも依存します。
空の差分は通信・コミットせず、転送済みの同じJSONも通信しません。
失敗時は転送済みと記録せず、次回の実行で再試行します。
GitHub側も、正本overlayと完全一致する取り込み済みの差分は日数経過後も再適用しません。
未適用・変更された差分には生成日時・確認日時の鮮度検証を実施します。

### 1. セキュリティ設定（最優先）

リポジトリ Settings → Rules → Rulesets で main のActiveな保護ルールを必ず作成・確認してください。
少なくとも PR必須、Force Push禁止、削除禁止、Bypass例外なしを推奨します。
加えてデータPRの必須レビュー/CIチェックを有効にすることを推奨します。

PATはFine-grained、対象はこのリポジトリのみ、Contents: Read and write。
PAT自体はブランチ限定にできないことに注意してください。
ActionsやAdministration権限は原則付与しないでください。
PATの文字列はリポジトリ内、Codexプロンプト、タスクXML、環境変数に保存しません。
現在のデフォルトはPR作成までで、自動マージは無効です。

Settings → Actions → General → Workflow permissions の
「Allow GitHub Actions to create and approve pull requests」を有効にします。
これは差分PRを作成するために必要で、このワークフローは承認レビューを投稿しません。
標準のWorkflow permissionsはreadのままで、必要な権限はsync-codex.yml側で指定します。

### 2. Windowsの転送処理

Git for Windowsをインストール済みのWindows PowerShellから、このリポジトリのmainをCloneして以下を実行します：

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_calendar_transfer.ps1

これで %LOCALAPPDATA%\StreamerEventCalendar\outbox と、転送専用Cloneを作り、
StreamerCalendarCodexPublisher という毎時05分のWindowsタスクを登録します。
再実行するとスクリプトと既存タスクを更新します。転送専用Cloneとoutboxは保持します。
同時実行を抑止し、実行上限は10分、実行を逃した場合は復帰後に実行します。
バッテリー駆動でも実行し、PCをスリープから起こしません。
ユーザーがログオン中でPCが稼働している必要があります。

**最初の一度だけ**、対話型PowerShellで次を実行してGit認証を確認します：

    git -C "$env:LOCALAPPDATA\StreamerEventCalendar\sync-repo" push --dry-run origin HEAD:refs/heads/codex/calendar-updates

必要であればGit Credential Managerから認証を求められます。
Fine-grained PATの秘密値はGitの資格情報入力画面だけに貼り付けてください。
CodexやチャットにPATを渡さないでください。

### 3. Codexデスクトップ定期タスク

Codexアプリで mmiyaji/streamer-event-calendar のローカルCloneを対象にしたタスクを作り、
codex/CALENDAR_AUTOMATION.md の内容を指示文として使用します。
07:00と19:00（Asia/Tokyo）の2つのスケジュールを設定します。
現在はこの設定用チャットに紐づく「イベントカレンダーを朝夕更新」という定期実行を使用します。
Codexアプリを開いた状態にしてください。通常の変更なし実行は通知せず、変更・失敗・要対応のみ通知します。

作業ディレクトリに書けること、公式サイトへネットワークアクセスできることを
**定期タスクの実行ログ**で必ず確認してください。
Codexの成果物出力は以下のJSONです：

    %LOCALAPPDATA%\StreamerEventCalendar\outbox\codex_proposals.json

Codexは完成JSONをatomic replaceで書き込み、GitHubへ直接Pushしません。

### 4. 動作検証

1. Codexのタスクを試し、公式サイトへのアクセス・既存データの照合・outboxのJSON生成を確認する。
2. 公開前のテスト（無害な検証用実イベントは登録しない）では、changes=[]にする。
3. 内容のある正規の差分が出たら、publisherをPowerShellから手動実行してPushを確認する：

       powershell.exe -NoProfile -File "$env:LOCALAPPDATA\StreamerEventCalendar\publisher\run_calendar_transfer.ps1"

4. GitHub Actionsの Sync validated Codex calendar data を workflow_dispatch で手動実行する。
5. 新しい差分があればautomation/codex-syncからmainへのPRが作られる。公式出典・差分を確認してマージする。空の差分ならPRを作らず終了するのが正常。
6. Pages workflowが成功し、calendar.ics, streamers.ics, sf6.ics, shadowverse-wb.ics, pokemon.ics が更新される。

ローカルの回帰テストは以下で実行します。Windowsの転送テストでは一時ディレクトリ内に
Gitリポジトリを作り、空差分・転送・再実行・失敗後の再試行を検証します。GitHubへテストイベントは送信しません。

    python -m unittest discover -s tests -v
    python scripts/build.py

Windowsタスクそのものの試験と結果確認：

    Start-ScheduledTask -TaskName StreamerCalendarCodexPublisher
    Get-ScheduledTaskInfo -TaskName StreamerCalendarCodexPublisher
    Get-ChildItem "$env:LOCALAPPDATA\StreamerEventCalendar\logs" -Filter 'transfer-*.log'

LastTaskResult=0が正常終了です。空差分でも成功します。
非空の差分を使う試験は公式情報で確認済みの変更だけに限定します。

### 5. 運用ポリシー

- 日付が未確定なら差分に含めない。
- 情報源URLがないもの・重複が疑われるものはActionsで拒否する。
- 既存IDは維持する。中止は既存IDへのcancel操作にする。
- category=streamerかつgame=sf6/shadowverse_wbならゲーム専用ICSにも入る。
- 変更が無ければコミットしない。出力前にJSONを必ず検証する。
- Codex定期タスクが失敗してもGitHub Actionsは以前の正規データを保持する。
- 自動マージを有効化するには、保護ルールと実運用での検証を完了してから
  Repository variables に ENABLE_CALENDAR_AUTO_MERGE=true を登録する。
  確認なしの取消・曖昧な重複判定には特に注意すること。

### 6. 障害の切り分け

- **Codexログ失敗**：Codexタスク、ネットワーク、outbox書込権限
- **publisher失敗**：LastTaskResultと `%LOCALAPPDATA%\StreamerEventCalendar\logs\transfer-*.log`、Git Credential Manager、PAT期限/権限
- **GitHub同期失敗**：Actionsログ、JSONスキーマ、重複、PR作成権限
- **Pages失敗**：Pages Actionsログ、build.py
- GITHUB_TOKENで作成したPRのCIが承認待ちになるケースがあるため、
  実行状態とPR画面を確認すること。

転送ログは14日間保持します。`published.sha256` は最後に転送成功したJSONの識別値で、
秘密情報ではありません。リモートブランチを手動で戻した際に再転送するには、このファイルを削除します。
`publish.lock` は排他用で、ファイルが残っていても異常ではありません。
プロセス終了時にOSがロックを解放するため、途中終了後も次回実行できます。

## 設定・試験の記録

2026-10-11：朝夕のCodex定期実行、毎時05分のWindows転送、毎時17分のGitHub同期を基本構成とします。
main保護はPR必須・Force Push禁止・削除禁止・Bypassなしを確認済みです。
必須レビュー数は0で、レビュー承認・必須CIチェックは強制していません。自動マージは無効です。
初期設定時の空差分によるGitHub検証・ビルドは[成功](https://github.com/mmiyaji/streamer-event-calendar/actions/runs/38070724748)しました。
これは調査ジョブの予約起動、非空差分の本番PR作成、PRマージ後の公開の実証とは別です。

構成見直し後の試験（2026-10-11）：

- ローカル回帰テスト13件成功。非空差分の転送、同一JSONの通信省略、Push失敗後の再試行、残存ロックファイルからの復帰、不正形式の拒否を隔離Gitで確認。
- Web・ICSビルド成功（公開対象160件）。公開events.jsonも160件を取得できた。
- インストーラ再実行で毎時05分の設定を反映。Windowsタスクを手動起動しLastTaskResult=0、ログにも終了コード0を確認。
- GitHubの現行mainを空差分で[再試験して成功](https://github.com/mmiyaji/streamer-event-calendar/actions/runs/38071163383)。差分なしのためPR作成・Pages公開は実行していない。
- 公式情報へのアクセス試験ではShadowverse WB公式を取得できたが、Web検索ツールからSF6公式トップは403だった。取得経路によって制約が異なるため、定期調査では代替の公式ページを確認し、未確認範囲を報告する。

初回見直し時点ではWindowsのスクリプトとCodexの実行指示を反映し、リポジトリ内の修正は未コミットでした。
実データによる通し試験では、この修正を先にPR経由でmainへ反映してから差分を転送します。
SFLの自動生成日程よりも承認済みCodex overlayを後に統合し、出演者などの更新を保持します。
この統合順序と、streamers.ics・sf6.ics両方への掲載を回帰テストで確認します。
