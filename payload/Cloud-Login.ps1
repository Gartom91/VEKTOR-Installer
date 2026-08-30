$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'installation.json') -Raw | ConvertFrom-Json
$docker = Find-Docker
if (-not $docker) { throw 'Brak Docker Desktop.' }
Wait-Docker $docker
$compose = Get-ComposeArguments $PSScriptRoot $config
Write-Host 'Otworzy sie proces logowania Ollama. Dane logowania zapisuje Ollama w swoim trwalym woluminie, nie instalator VEKTORA.' -ForegroundColor Cyan
$loginArgs = $compose + @('exec', '-T', 'ollama', 'ollama', 'signin')
& $docker @loginArgs
if ($LASTEXITCODE -ne 0) { throw "Logowanie nie powiodlo sie (kod $LASTEXITCODE)." }
Write-Host 'Logowanie zakonczone. Tryb Auto moze teraz korzystac z modeli cloud.' -ForegroundColor Green
Read-Host 'Nacisnij Enter, aby zamknac'
