$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$stage = Join-Path $root 'packaging\payload'
$out = Join-Path $root 'dist-installer'
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $out 'DigitalTimeWheelSetup.exe') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $out 'DigitalTimeWheelPayload.zip') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $out 'publish') -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $stage,$out | Out-Null

# Frozen application sources and production frontend only.
Copy-Item (Join-Path $root 'backend') (Join-Path $stage 'backend') -Recurse
Copy-Item (Join-Path $root 'frontend\dist') (Join-Path $stage 'frontend\dist') -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $stage 'packaging') | Out-Null
Copy-Item (Join-Path $root 'packaging\static_server.py') (Join-Path $stage 'packaging\static_server.py')
Copy-Item (Join-Path $root 'packaging\run-app.ps1') (Join-Path $stage 'packaging\run-app.ps1')
Copy-Item (Join-Path $root 'packaging\uninstall.ps1') (Join-Path $stage 'uninstall.ps1')
Copy-Item (Join-Path $root 'runtime') (Join-Path $stage 'runtime') -Recurse

# Portable CPython plus only the runtime dependencies used by the frozen backend.
$pyHome = 'C:\python311'
if (-not (Test-Path (Join-Path $pyHome 'python.exe'))) { throw 'Python 3.11 installation was not found at C:\python311' }
$portable = Join-Path $stage 'python'; New-Item -ItemType Directory -Force -Path $portable | Out-Null
Copy-Item (Join-Path $pyHome 'python.exe'),(Join-Path $pyHome 'pythonw.exe'),(Join-Path $pyHome 'python*.dll'),(Join-Path $pyHome 'vcruntime*.dll') $portable -Force
Copy-Item (Join-Path $pyHome 'DLLs') (Join-Path $portable 'DLLs') -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $portable 'Lib') | Out-Null
Get-ChildItem (Join-Path $pyHome 'Lib') -Force | Where-Object Name -ne 'site-packages' | Copy-Item -Destination (Join-Path $portable 'Lib') -Recurse -Force
New-Item -ItemType Directory -Force -Path (Join-Path $portable 'Lib\site-packages') | Out-Null
$deps = @('fastapi','fastapi-*.dist-info','starlette','starlette-*.dist-info','pydantic','pydantic-*.dist-info','pydantic_core','pydantic_core-*.dist-info','typing_extensions*','typing_inspection*','annotated_types*','annotated_doc*','anyio','anyio-*.dist-info','sniffio','sniffio-*.dist-info','idna','idna-*.dist-info','uvicorn','uvicorn-*.dist-info','click','click-*.dist-info','h11','h11-*.dist-info','httptools','httptools-*.dist-info','websockets','websockets-*.dist-info','watchfiles','watchfiles-*.dist-info','numpy','numpy.libs','numpy-*.dist-info','pandas','pandas.libs','pandas-*.dist-info','python_dateutil','python_dateutil-*.dist-info','dateutil','six.py','six-*.dist-info','pytz','pytz-*.dist-info','tzdata','tzdata-*.dist-info','MetaTrader5','metatrader5-*.dist-info','colorama','colorama-*.dist-info','packaging','packaging-*.dist-info')
$site = Join-Path $pyHome 'Lib\site-packages'; foreach($pattern in $deps){Get-Item (Join-Path $site $pattern) -ErrorAction SilentlyContinue | Copy-Item -Destination (Join-Path $portable 'Lib\site-packages') -Recurse -Force}

$zip = Join-Path $out 'DigitalTimeWheelPayload.zip'
Remove-Item $zip -Force -ErrorAction SilentlyContinue
tar.exe -a -c -f $zip -C $stage .
$stub = Join-Path $root 'packaging\InstallerStub'
Copy-Item $zip (Join-Path $stub 'DigitalTimeWheelPayload.zip') -Force
dotnet restore (Join-Path $stub 'InstallerStub.csproj') --ignore-failed-sources -p:SelfContained=false
dotnet publish (Join-Path $stub 'InstallerStub.csproj') -c Release -r win-x64 --no-restore -p:SelfContained=false /p:PublishSingleFile=true -o (Join-Path $out 'publish')
Copy-Item (Join-Path $out 'publish\DigitalTimeWheelSetup.exe') (Join-Path $out 'DigitalTimeWheelSetup.exe') -Force
if (-not (Test-Path (Join-Path $out 'DigitalTimeWheelSetup.exe'))) { throw 'The installer executable was not created' }
Write-Host ('Created ' + (Join-Path $out 'DigitalTimeWheelSetup.exe'))
