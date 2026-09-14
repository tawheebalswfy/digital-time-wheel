$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'DigitalTimeWheel\runtime'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$python = Join-Path $appRoot 'python\python.exe'
$backendPid = Join-Path $runtime 'backend.pid'
$frontendPid = Join-Path $runtime 'frontend.pid'
function Healthy($pidFile, $port) {
  if (-not (Test-Path $pidFile)) { return $false }
  try { $pid = [int](Get-Content $pidFile -Raw); $p = Get-Process -Id $pid -ErrorAction Stop; $l = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue; return [bool]($l -and ($l.OwningProcess -contains $pid)) } catch { return $false }
}
if (-not (Healthy $backendPid 8000)) {
  $p = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $appRoot -WindowStyle Hidden -PassThru
  $p.Id | Set-Content $backendPid
}
if (-not (Healthy $frontendPid 5173)) {
  $p = Start-Process -FilePath $python -ArgumentList 'packaging\static_server.py','--directory','frontend\dist','--host','127.0.0.1','--port','5173' -WorkingDirectory $appRoot -WindowStyle Hidden -PassThru
  $p.Id | Set-Content $frontendPid
}
Start-Process 'http://127.0.0.1:5173/'
