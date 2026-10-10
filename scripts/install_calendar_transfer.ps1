# Install hourly polling transfer on Windows. Requires Git for Windows.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar'
$syncRepo = Join-Path $root 'sync-repo'
$outbox = Join-Path $root 'outbox'
$publisherDir = Join-Path $root 'publisher'
$publisher = Join-Path $publisherDir 'publish_codex_proposals.ps1'
$runner = Join-Path $publisherDir 'run_calendar_transfer.ps1'
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git for Windows is required."
}
New-Item -ItemType Directory -Force -Path $outbox, $publisherDir | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'publish_codex_proposals.ps1') -Destination $publisher -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'run_calendar_transfer.ps1') -Destination $runner -Force
if (!(Test-Path (Join-Path $syncRepo '.git'))) {
  & git clone --branch codex/calendar-updates --single-branch https://github.com/mmiyaji/streamer-event-calendar.git $syncRepo
  if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }
}
& git -C $syncRepo config user.name "calendar-codex-publisher"
if ($LASTEXITCODE -ne 0) { throw "Git name configuration failed" }
& git -C $syncRepo config user.email "calendar-codex-publisher@users.noreply.github.com"
if ($LASTEXITCODE -ne 0) { throw "Git email configuration failed" }
# GCM prompts interactively on first push; never embed a PAT in a URL or script.
$taskName = 'StreamerCalendarCodexPublisher'
$command = 'powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $runner + '"'
& schtasks.exe /Create /TN $taskName /TR $command /SC HOURLY /MO 1 /ST 00:05 /F
if ($LASTEXITCODE -ne 0) { throw "Scheduled task registration failed" }
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Set-ScheduledTask -TaskName $taskName -Settings $settings | Out-Null
Write-Output "Registered scheduled task: $taskName"
Write-Output "Schedule: hourly at minute 05 (local time), with missed-run catch-up"
Write-Output "Codex output path: $(Join-Path $outbox 'codex_proposals.json')"
Write-Output "Publisher sync clone: $syncRepo"
Write-Output "IMPORTANT: Set up Git Credential Manager interactively before an unattended push."
Write-Output "Use the PAT only when prompted by GCM; never paste it into Codex."
