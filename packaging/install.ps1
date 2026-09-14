param([string]$Payload = (Join-Path $PSScriptRoot 'package.zip'), [switch]$SkipExtract)
$ErrorActionPreference = 'Stop'
$target = Join-Path $env:LOCALAPPDATA 'DigitalTimeWheel'
New-Item -ItemType Directory -Force -Path $target | Out-Null
if (-not $SkipExtract) { $tmp = Join-Path $env:TEMP ('DigitalTimeWheel-' + [guid]::NewGuid()); Expand-Archive -LiteralPath $Payload -DestinationPath $tmp -Force; Get-ChildItem $tmp -Force | Copy-Item -Destination $target -Recurse -Force; Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
$start = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Digital Time Wheel.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($start)
$shortcut.TargetPath = 'powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + (Join-Path $target 'packaging\run-app.ps1') + '"'
$shortcut.WorkingDirectory = $target
$shortcut.Save()
Write-Host 'Digital Time Wheel installed to' $target
Start-Process powershell.exe -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',(Join-Path $target 'packaging\run-app.ps1') -WorkingDirectory $target
