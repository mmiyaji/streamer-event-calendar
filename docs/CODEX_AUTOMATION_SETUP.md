# Codex → GitHub Actions カレンダー自動更新

## 目的と責任分界

- **Codexデスクトップ定期タスク**：公式情報巡回、既存データとの比較、差分JSON作成。OpenAI APIキー不要。
- **Windowsタスクスケジューラ**：完成したJSONのみGitで codex/calendar-updates にPush。Git認証はGit Credential Manager。
- **GitHub Actions（sync-codex.yml）**：毎時17分UTCにブランチからJSONのみFetch。mainの信頼済みPythonで検証・ICSビルドし、データ専用PRを作成/更新。
- **GitHub Pages**：PRがmainにマージされたら既存Pagesワークフローが発火し、ICSとWebを更新。

GitHub Actionsが取り込むのは data/codex_proposals.json **のみ**です。
Codexブランチ上のPython/WorkflowをGitHub Actionsでは実行しません。

### 1. セキュリティ設定（最優先）

リポジトリ Settings → Rules → Rulesets で main のActiveな保護ルールを必ず作成・確認してください。
少なくとも PR必須、Force Push禁止、削除禁止、Bypass例外なしを推奨します。
加えてデータPRの必須レビュー/CIチェックを有効にすることを推奨します。

PATはFine-grained、対象はこのリポジトリのみ、Contents: Read and write。
PAT自体はブランチ限定にできないことに注意してください。
ActionsやAdministration権限は原則付与しないでください。
PATの文字列はリポジトリ内、Codexプロンプト、タスクXML、環境変数に保存しません。
現在のデフォルトはPR作成までで、自動マージは無効です。

### 2. Windowsの転送処理

Git for Windowsをインストール済みのWindows PowerShellから、このリポジトリのmainをCloneして以下を実行します：

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_calendar_transfer.ps1

これで %LOCALAPPDATA%\StreamerEventCalendar\outbox と、転送専用Cloneを作り、
StreamerCalendarCodexPublisher という15分間隔のWindowsタスクを登録します。
ユーザーがログオン中でPCが稼働している必要があります。

**最初の一度だけ**、対話型PowerShellで次を実行してGit認証を確認します：

    git -C "$env:LOCALAPPDATA\StreamerEventCalendar\sync-repo" push origin HEAD:refs/heads/codex/calendar-updates

必要であればGit Credential Managerから認証を求められます。
Fine-grained PATの秘密値はGitの資格情報入力画面だけに貼り付けてください。
CodexやチャットにPATを渡さないでください。

### 3. Codexデスクトップ定期タスク

Codexアプリで mmiyaji/streamer-event-calendar のローカルCloneを対象にしたタスクを作り、
codex/CALENDAR_AUTOMATION.md の内容を指示文として使用します。
07:00と19:00（Asia/Tokyo）の2つのスケジュールを設定します。

作業ディレクトリに書けること、公式サイトへネットワークアクセスできることを
**定期タスクの実行ログ**で必ず確認してください。
Codexの成果物出力は以下のJSONです：

    %LOCALAPPDATA%\StreamerEventCalendar\outbox\codex_proposals.json

Codexは完成JSONをatomic replaceで書き込み、GitHubへ直接Pushしません。

### 4. 動作検証

1. Codexのタスクを手動で試し、outboxのJSONが生成されることを確認する。
2. 公開前のテスト（無害な検証用実イベントは登録しない）では、changes=[]にする。
3. 内容のある正規の差分が出たら、publisherをPowerShellから手動実行してPushを確認する：

       powershell.exe -NoProfile -File "$env:LOCALAPPDATA\StreamerEventCalendar\publisher\publish_codex_proposals.ps1"

4. GitHub Actionsの Sync validated Codex calendar data を workflow_dispatch で手動実行する。
5. 正常ならautomation/codex-syncからmainへのPRが作られる。公式出典・差分を確認してマージする。
6. Pages workflowが成功し、calendar.ics, streamers.ics, sf6.ics, shadowverse-wb.ics, pokemon.ics が更新される。

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
- **publisher失敗**：Windowsタスク履歴、Git Credential Manager、PAT期限/権限
- **GitHub同期失敗**：Actionsログ、JSONスキーマ、重複、PR作成権限
- **Pages失敗**：Pages Actionsログ、build.py
- GITHUB_TOKENで作成したPRのCIが承認待ちになるケースがあるため、
  実行状態とPR画面を確認すること。
