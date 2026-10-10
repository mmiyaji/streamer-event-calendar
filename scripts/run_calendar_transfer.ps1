# Scheduled entry point: retain diagnostics without displaying a terminal window.
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'StreamerEventCalendar'
$logs = Join-Path $root 'logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$cutoff = (Get-Date).AddDays(-14)
Get-ChildItem -LiteralPath $logs -Filter 'transfer-*.log' -File |
  Where-Object LastWriteTime -LT $cutoff | Remove-Item -Force
$log = Join-Path $logs ('transfer-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $PID + '.log')
$result = 1
try {
  Start-Transcript -LiteralPath $log | Out-Null
  & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass `
    -File (Join-Path $PSScriptRoot 'publish_codex_proposals.ps1')
  $result = $LASTEXITCODE
  Write-Output "Transfer exit code: $result"
} finally {
  Stop-Transcript -ErrorAction SilentlyContinue | Out-Null
}
exit $result
