param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$sourceRoot = $root
$venv = Join-Path $root '.venv'
if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) { & $Python -m venv $venv }
$python = Join-Path $venv 'Scripts\python.exe'
& $python -m pip install --disable-pip-version-check --quiet 'pyinstaller==6.22.2' 'fastapi==0.141.0' 'uvicorn==0.52.0' 'pydantic==2.12.5'
if ($LASTEXITCODE) { throw 'Nie mozna przygotowac host brokera.' }
Push-Location $root
try {
    & $python -m PyInstaller --noconfirm --clean --onefile --name VEKTOR-Host --paths $sourceRoot --collect-all uvicorn --collect-all fastapi payload/host_main.py
    if ($LASTEXITCODE) { throw 'PyInstaller failed.' }
    Copy-Item -LiteralPath dist/VEKTOR-Host.exe -Destination payload/VEKTOR-Host.exe -Force
    Remove-Item payload.zip -ErrorAction SilentlyContinue
    Compress-Archive -Path payload/* -DestinationPath payload.zip -CompressionLevel Optimal
    & dotnet publish src/VEKTOR.Setup.csproj -c Release -r win-x64 -o dist/setup
    if ($LASTEXITCODE) { throw 'dotnet publish failed.' }
    Copy-Item -LiteralPath dist/setup/VEKTOR-Setup.exe -Destination dist/VEKTOR-Setup-x64.exe -Force
    Copy-Item -LiteralPath payload/release.json -Destination dist/release.json -Force
    Get-FileHash dist/VEKTOR-Setup-x64.exe,dist/release.json -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  $([IO.Path]::GetFileName($_.Path))" } | Set-Content dist/SHA256SUMS.txt -Encoding ascii
} finally { Pop-Location }
