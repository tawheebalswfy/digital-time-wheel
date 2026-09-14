$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePath = Join-Path $projectRoot 'runtime'
New-Item -ItemType Directory -Force -Path $runtimePath | Out-Null
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = (Get-Command python).Source }
$nodePath = (Get-Command node).Source
$backendPidPath=Join-Path $runtimePath 'backend.pid'; $frontendPidPath=Join-Path $runtimePath 'frontend.pid'
function Get-HealthyPid([string]$path,[int]$port) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { $trackedPid=[int](Get-Content -LiteralPath $path -Raw).Trim(); $p=Get-Process -Id $trackedPid -ErrorAction Stop
    $listen=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($listen -and ($listen.OwningProcess -contains $trackedPid)) { return $trackedPid }
  } catch {}
  Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue; return $null
}
function Start-Detached([string]$exe,[string[]]$argList,[string]$work,[string]$out,[string]$err) {
  $argText=($argList | ForEach-Object { if ($_ -match '\s') { '"'+($_ -replace '"','\"')+'"' } else { $_ } }) -join ' '
  $psi=[Diagnostics.ProcessStartInfo]::new();$psi.FileName=$exe;$psi.Arguments=$argText;$psi.WorkingDirectory=$work;$psi.UseShellExecute=$true;$psi.WindowStyle='Hidden'
  return [Diagnostics.Process]::Start($psi)
}
$backendRunning = $false
try { $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3; $backendRunning = $health.engine_version -eq '1.0.0' } catch {}
if($backendRunning -and $health.pid){$health.pid | Set-Content -LiteralPath $backendPidPath}
if (-not $backendRunning) {
    $old=Get-HealthyPid $backendPidPath 8000
    if (-not $old) {
      $started=Start-Detached $pythonPath @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000') $projectRoot (Join-Path $runtimePath 'backend.stdout.log') (Join-Path $runtimePath 'backend.stderr.log')
      $started.Id | Set-Content -LiteralPath $backendPidPath
      Start-Sleep -Milliseconds 500
      $listener=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
      if($listener){$listener.OwningProcess | Set-Content -LiteralPath $backendPidPath}
    }
}
$frontendRunning = $false
try { $frontendRunning = (Invoke-WebRequest 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch {}
if (-not $frontendRunning) {
    $old=Get-HealthyPid $frontendPidPath 5173
    if (-not $old) {
      $started=Start-Detached $nodePath @('node_modules/vite/bin/vite.js','--host','127.0.0.1','--port','5173') (Join-Path $projectRoot 'frontend') (Join-Path $runtimePath 'frontend.stdout.log') (Join-Path $runtimePath 'frontend.stderr.log')
      $started.Id | Set-Content -LiteralPath $frontendPidPath
      Start-Sleep -Milliseconds 500
      $listener=Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
      if($listener){$listener.OwningProcess | Set-Content -LiteralPath $frontendPidPath}
    }
}
Write-Host 'Local application: http://127.0.0.1:5173/'
Write-Host 'Backend: http://127.0.0.1:8000/api/health'
Write-Host "Logs: $runtimePath"
