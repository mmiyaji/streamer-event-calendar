Option Explicit
Dim shell, files, runner, command, result
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
runner = files.BuildPath(files.GetParentFolderName(WScript.ScriptFullName), "run_calendar_transfer.ps1")
command = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File " & Chr(34) & runner & Chr(34)
' GUI host plus hidden child prevents a console flash on interactive desktops.
result = shell.Run(command, 0, True)
WScript.Quit result
