$ErrorActionPreference = 'Stop'
$InstallDir = $PSScriptRoot
. (Join-Path $InstallDir 'Common.ps1')
$state = Join-Path $env:LOCALAPPDATA 'VEKTOR-Desktop'
New-Item -ItemType Directory -Path $state -Force | Out-Null
$log = Join-Path $state 'startup.log'
$startupMutex = New-Object Threading.Mutex($false, 'Local\VEKTOR.DesktopStartup')
$ownsStartup = $false
try {
    try { $ownsStartup = $startupMutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $ownsStartup = $true }
    if (-not $ownsStartup) { exit 0 }
    $config = Get-Content -LiteralPath (Join-Path $InstallDir 'installation.json') -Raw | ConvertFrom-Json
    $docker = Find-Docker
    if (-not $docker) { throw 'Brak Docker Desktop. Uruchom ponownie instalator VEKTORA.' }
    Wait-Docker $docker
    Start-Broker $InstallDir $config
    $composeOperation = Enter-VektorComposeOperation $InstallDir
    try {
    $compose = Get-ComposeArguments $InstallDir $config
    $null = Invoke-Checked $docker ($compose + @('up', '-d', '--no-build')) -Timeout 300
    } finally { $composeOperation.ReleaseMutex(); $composeOperation.Dispose() }
    $url = "http://127.0.0.1:$($config.Port)"
    $ready = $false
    foreach ($attempt in 1..90) {
        try { $health = Invoke-RestMethod ($url + '/api/health') -TimeoutSec 3; if ($health.status -eq 'ok' -and $health.ollama.connected) { $ready = $true; break } } catch {}
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'VEKTOR lub Ollama nie przeszly healthchecku w 180 s.' }
    $browser = @((Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'), (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'), (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'), (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe')) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
    if ($browser) { Start-Process -FilePath $browser -ArgumentList "--app=$url --start-maximized --no-first-run --user-data-dir=`"$(Join-Path $state 'BrowserProfile')`"" | Out-Null } else { Start-Process $url }
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) READY $url"
} catch {
    Add-Content -LiteralPath $log -Value "$(Get-Date -Format o) ERROR $($_.Exception.Message)"
    Add-Type -AssemblyName PresentationFramework
    [Windows.MessageBox]::Show("VEKTOR nie uruchomil sie.`n`n$($_.Exception.Message)`n`nLog: $log", 'VEKTOR', 'OK', 'Error') | Out-Null
    exit 1
} finally {
    if ($ownsStartup) { $startupMutex.ReleaseMutex() }
    $startupMutex.Dispose()
}
