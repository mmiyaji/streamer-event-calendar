# Transfer ONLY a finished JSON proposal from local Codex to the Codex data branch.
# Requires Git for Windows and an interactive, one-time Git Credential Manager login.
# No PAT, credentials, or other secrets are read from files or command arguments.
param(
  [string]$Outbox = (Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar\outbox\codex_proposals.json'),
  [string]$SyncRepo = (Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar\sync-repo')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'

function Git([string[]]$Arguments) {
  & git.exe -c credential.interactive=never -C $SyncRepo @Arguments
  if ($LASTEXITCODE -ne 0) { throw "git operation failed: $($Arguments[0])" }
}
if (!(Test-Path -LiteralPath $Outbox)) { Write-Output "No Codex outbox file"; exit 0 }
if (!(Test-Path -LiteralPath (Join-Path $SyncRepo '.git'))) {
  throw "Sync clone missing. Run install_calendar_transfer.ps1 first."
}
$info = Get-Item -LiteralPath $Outbox
if ($info.Length -gt 256000) { throw "Proposal exceeds 256KB" }
if ($info.LastWriteTimeUtc -gt (Get-Date).ToUniversalTime().AddSeconds(-5)) {
  Write-Output "Proposal still being written; retry at next poll"
  exit 0
}
$raw = [System.IO.File]::ReadAllText($Outbox, [System.Text.Encoding]::UTF8)
$data = $raw | ConvertFrom-Json
if ($data.schema_version -ne 1 -or $data.changes -isnot [System.Array]) {
  throw "Invalid schema_version or changes"
}
if ($data.changes.Count -eq 0) { Write-Output "No proposed changes"; exit 0 }
if ($data.changes.Count -gt 100) { throw "Too many changes" }
if (!$data.generated_at) { throw "generated_at missing" }
$hashAlgorithm = [System.Security.Cryptography.SHA256]::Create()
try {
  $proposalHash = [BitConverter]::ToString($hashAlgorithm.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($raw))).Replace('-', '')
} finally { $hashAlgorithm.Dispose() }
$receipt = Join-Path (Split-Path $SyncRepo -Parent) 'published.sha256'

# Prevent two overlapping scheduled runs from changing the same local clone.
$lock = Join-Path (Split-Path $SyncRepo -Parent) 'publish.lock'
try {
  $lockHandle = [System.IO.File]::Open($lock, 'OpenOrCreate', 'Write', 'None')
} catch {
  Write-Output "Another publisher invocation is running"; exit 0
}
try {
  if ((Test-Path -LiteralPath $receipt) -and ([System.IO.File]::ReadAllText($receipt).Trim() -eq $proposalHash)) {
    Write-Output "Proposal already transferred; no network request"
    exit 0
  }
  $generated = [DateTimeOffset]::Parse($data.generated_at)
  if ($generated -lt [DateTimeOffset]::Now.AddDays(-7) -or $generated -gt [DateTimeOffset]::Now.AddDays(1)) {
    throw "Proposal is stale or future-dated; regenerate before transfer"
  }
  Git -Arguments @('fetch', '--no-tags', 'origin',
    '+refs/heads/codex/calendar-updates:refs/remotes/origin/codex/calendar-updates')
  Git -Arguments @('switch', '-C', 'codex/calendar-updates', 'origin/codex/calendar-updates')

  $target = Join-Path $SyncRepo 'data\codex_proposals.json'
  $current = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)
  if ($current.Trim() -eq $raw.Trim()) {
    [System.IO.File]::WriteAllText($receipt, $proposalHash)
    Write-Output "Remote proposal already matches"
    exit 0
  }
  [System.IO.File]::WriteAllText($target, $raw,
    [System.Text.UTF8Encoding]::new($false))
  Git -Arguments @('add', '--', 'data/codex_proposals.json')
  & git.exe -C $SyncRepo diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { Write-Output "No staged changes"; exit 0 }
  if ($LASTEXITCODE -ne 1) { throw "git diff failed" }
  Git -Arguments @('commit', '-m', 'chore(codex): publish verified event proposals')
  Git -Arguments @('push', 'origin', 'HEAD:refs/heads/codex/calendar-updates')
  [System.IO.File]::WriteAllText($receipt, $proposalHash)
  Write-Output "Proposal pushed to codex/calendar-updates"
} finally {
  if ($null -ne $lockHandle) { $lockHandle.Dispose() }
}
