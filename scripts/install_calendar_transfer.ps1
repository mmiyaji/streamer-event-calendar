# Install 15-minute polling transfer on Windows. Requires Git for Windows.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar'
$syncRepo = Join-Path $root 'sync-repo'
$outbox = Join-Path $root 'outbox'
$publisherDir = Join-Path $root 'publisher'
$publisher = Join-Path $publisherDir 'publish_codex_proposals.ps1'
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git for Windows is required."
}
New-Item -ItemType Directory -Force -Path $outbox, $publisherDir | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'publish_codex_proposals.ps1') -Destination $publisher -Force
if (!(Test-Path (Join-Path $syncRepo '.git'))) {
  & git clone --branch codex/calendar-updates --single-branch https://github.com/mmiyaji/streamer-event-calendar.git $syncRepo
  if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }
}
& git -C $syncRepo config user.name "calendar-codex-publisher"
& git -C $syncRepo config user.email "calendar-codex-publisher@users.noreply.github.com"
# GCM prompts interactively on first push; never embed a PAT in a URL or script.
$taskName = 'StreamerCalendarCodexPublisher'
$command = 'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $publisher + '"'
& schtasks.exe /Create /TN $taskName /TR $command /SC MINUTE /MO 15 /F
if ($LASTEXITCODE -ne 0) { throw "Scheduled task registration failed" }
Write-Output "Registered scheduled task: $taskName"
Write-Output "Codex output path: $(Join-Path $outbox 'codex_proposals.json')"
Write-Output "Publisher sync clone: $syncRepo"
Write-Output "IMPORTANT: Set up Git Credential Manager interactively before an unattended push."
Write-Output "Use the PAT only when prompted by GCM; never paste it into Codex."
