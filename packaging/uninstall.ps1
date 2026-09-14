$ErrorActionPreference='SilentlyContinue'
$target=Join-Path $env:LOCALAPPDATA 'DigitalTimeWheel'
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "$target\python\*"} | Stop-Process -Force
Remove-Item (Join-Path $target 'backend') -Recurse -Force
Remove-Item (Join-Path $target 'frontend') -Recurse -Force
Remove-Item (Join-Path $target 'packaging') -Recurse -Force
Remove-Item (Join-Path $target 'python') -Recurse -Force
Remove-Item (Join-Path $target 'runtime') -Recurse -Force
Remove-Item (Join-Path $target 'uninstall.ps1') -Force
