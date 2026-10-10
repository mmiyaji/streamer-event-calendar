# Transfer ONLY a finished JSON proposal from local Codex to the Codex data branch.
# Requires Git for Windows and an interactive, one-time Git Credential Manager login.
# No PAT, credentials, or other secrets are read from files or command arguments.
param(
  [string]$Outbox = (Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar\outbox\codex_proposals.json'),
  [string]$SyncRepo = (Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar\sync-repo')
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Git([string[]]$Arguments) {
  & git -C $SyncRepo @Arguments
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
if ($data.schema_version -ne 1 -or $null -eq $data.changes) {
  throw "Invalid schema_version or changes"
}
if ($data.changes.Count -eq 0) { Write-Output "No proposed changes"; exit 0 }
if ($data.changes.Count -gt 100) { throw "Too many changes" }
if (!$data.generated_at) { throw "generated_at missing" }

# Prevent two overlapping scheduled runs from changing the same local clone.
$lock = Join-Path (Split-Path $SyncRepo -Parent) 'publish.lock'
try {
  $lockHandle = [System.IO.File]::Open($lock, 'CreateNew', 'Write', 'None')
} catch {
  Write-Output "Another publisher invocation is running"; exit 0
}
try {
  Git @('fetch', '--no-tags', 'origin',
    '+refs/heads/codex/calendar-updates:refs/remotes/origin/codex/calendar-updates')
  Git @('switch', '-C', 'codex/calendar-updates', 'origin/codex/calendar-updates')

  $target = Join-Path $SyncRepo 'data\codex_proposals.json'
  $current = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)
  if ($current.Trim() -eq $raw.Trim()) {
    Write-Output "Remote proposal already matches"
    exit 0
  }
  [System.IO.File]::WriteAllText($target, $raw,
    [System.Text.UTF8Encoding]::new($false))
  Git @('add', '--', 'data/codex_proposals.json')
  & git -C $SyncRepo diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { Write-Output "No staged changes"; exit 0 }
  Git @('commit', '-m', 'chore(codex): publish verified event proposals')
  Git @('push', 'origin', 'HEAD:refs/heads/codex/calendar-updates')
  Write-Output "Proposal pushed to codex/calendar-updates"
} finally {
  if ($null -ne $lockHandle) { $lockHandle.Dispose() }
  Remove-Item -LiteralPath $lock -Force -ErrorAction SilentlyContinue
}
