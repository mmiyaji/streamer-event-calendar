# Build an unregistered Task Scheduler definition for the installed VBS runner.
param([Parameter(Mandatory)][string]$HiddenRunner)
$ErrorActionPreference = 'Stop'
$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\wscript.exe') `
  -Argument ('//B //NoLogo "' + $HiddenRunner + '"')
$trigger = New-ScheduledTaskTrigger -Once -At ([DateTime]::Today.AddMinutes(5)) `
  -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings
