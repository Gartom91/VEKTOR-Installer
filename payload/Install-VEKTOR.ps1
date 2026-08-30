param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'Programs\VEKTOR'),
    [switch]$AcceptDockerLicense,
    [switch]$EnableHost,
    [switch]$Autostart,
    [switch]$PlanOnly,
    [switch]$NoShortcuts,
    [switch]$SkipModelDownload
)
. (Join-Path $PSScriptRoot 'Common.ps1')
$lock = New-Object Threading.Mutex($false, 'Local\VEKTOR.DesktopInstaller')
$ownsLock = $false
try {
    try { $ownsLock = $lock.WaitOne(0) } catch [Threading.AbandonedMutexException] { $ownsLock = $true }
    if (-not $ownsLock) { throw 'Inna instalacja VEKTORA jest w toku.' }
    $os = Get-CimInstance Win32_OperatingSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    if ([int]$os.BuildNumber -lt 19045 -or $os.ProductType -ne 1 -or $cpu.Architecture -ne 9) { throw 'Wymagany Windows 10 22H2 / Windows 11 x64 (nie Server ani ARM64).' }
    $ram = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    $vram = 0
    $nvidia = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
    if ($nvidia) {
        $probe = Invoke-Checked $nvidia.Source @('--query-gpu=memory.total', '--format=csv,noheader,nounits') -Timeout 15 -AllowFailure
        if ($probe.ExitCode -eq 0) { $vram = [int](($probe.Output.Trim() -split '\r?\n' | ForEach-Object { [int]$_ } | Measure-Object -Maximum).Maximum) }
    }
    $profile = Get-HardwareProfile $ram $vram
    Write-Host "RAM: $([math]::Round($ram,1)) GB; NVIDIA: $vram MB; model: $($profile.Model); kontekst: $($profile.Context)."
    if ($PlanOnly) { Write-Host 'PLAN ONLY: brak zmian systemu, plikow, kontenerow i rejestru.'; exit 0 }
    if (-not $AcceptDockerLicense) { throw 'Wymagana jawna akceptacja licencji Docker Desktop.' }
    if (-not [IO.Path]::IsPathRooted($InstallDir) -or $InstallDir -match '[\r\n"$]') { throw 'Wybierz bezwzgledna sciezke bez cudzyslowow i znaku dolara.' }
    $InstallDir = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\')
    if ($InstallDir -eq [IO.Path]::GetPathRoot($InstallDir).TrimEnd('\')) { throw 'Nie instaluj w katalogu glownym dysku.' }
    $configPath = Join-Path $InstallDir 'installation.json'
    if ((Test-Path -LiteralPath $InstallDir) -and -not (Test-Path -LiteralPath $configPath) -and @(Get-ChildItem -LiteralPath $InstallDir -Force).Count -gt 0) { throw 'Wybierz pusty folder albo istniejaca instalacje VEKTORA.' }
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    $config = if (Test-Path -LiteralPath $configPath) { Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json } else { $null }
    if ($config -and $config.HostEnabled) {
        $pidFile = Join-Path $InstallDir 'broker.pid'
        if (Test-Path -LiteralPath $pidFile) {
            $running = Get-Process -Id ([int](Get-Content -LiteralPath $pidFile)) -ErrorAction SilentlyContinue
            if ($running -and $running.Path -eq (Join-Path $InstallDir 'VEKTOR-Host.exe')) {
                Get-Process -Name 'VEKTOR-Host' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $InstallDir 'VEKTOR-Host.exe') } | Stop-Process -ErrorAction SilentlyContinue
            }
        }
    }
    foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -File) { Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $InstallDir $file.Name) -Force }
    if (-not $config) {
        $workspace = Join-Path $InstallDir 'workspace'
        New-Item -ItemType Directory -Path $workspace -Force | Out-Null
        $config = [pscustomobject]@{ Version = '1.0.0'; Port = (Get-FreePort 8765); BrokerPort = (Get-FreePort 8877); Model = $profile.Model; Context = $profile.Context; GPU = $profile.GPU; HostEnabled = [bool]$EnableHost; HostRoots = @([IO.Path]::GetPathRoot($env:USERPROFILE)); Workspace = $workspace; Autostart = [bool]$Autostart }
    }
    # Save resumable state before prerequisites; a restart never discards data.
    Write-PrivateFile $configPath ($config | ConvertTo-Json)
    $wsl = Invoke-Checked 'wsl.exe' @('--version') -Timeout 30 -AllowFailure
    if ($wsl.ExitCode -ne 0) {
        Write-Host 'Instalacja WSL2 wymaga UAC. Po niej zrestartuj komputer i ponow instalator.'
        $p = Start-Process -FilePath 'wsl.exe' -ArgumentList '--install --no-distribution' -Verb RunAs -WindowStyle Hidden -PassThru
        $handle = $p.Handle; $p.WaitForExit()
        if ($p.ExitCode -notin @(0, 3010)) { throw "Instalacja WSL2: kod $($p.ExitCode)." }
        exit 3010
    }
    $docker = Find-Docker
    if (-not $docker) {
        Write-Host 'Pobieranie Docker Desktop z serwera producenta (kilkaset MB)...'
        $download = Join-Path $InstallDir 'DockerDesktopInstaller.exe'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' -OutFile $download -UseBasicParsing
        $signature = Get-AuthenticodeSignature -LiteralPath $download
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:CN|O)=Docker(?: Inc\.?|,|$)') { throw 'Podpis instalatora Docker nie jest prawidlowy. Nie uruchomiono pliku.' }
        $result = Invoke-Checked $download @('install', '--user', '--quiet', '--backend=wsl-2', '--accept-license') -Timeout 1800 -AllowFailure
        if ($result.ExitCode -eq 3010) { exit 3010 }
        if ($result.ExitCode -ne 0) { throw $result.Output }
        $docker = Find-Docker
        if (-not $docker) { throw 'Instalacja Docker nie udostepnila CLI. Zrestartuj Windows i ponow.' }
    }
    Write-Host 'Oczekiwanie na silnik Docker (do 300 s)...'
    Wait-Docker $docker
    $release = Get-Content -LiteralPath (Join-Path $InstallDir 'release.json') -Raw | ConvertFrom-Json
    if ($config.GPU) {
        Write-Host 'Test dostepnosci NVIDIA wewnatrz kontenera...'
        $gpu = Invoke-Checked $docker @('run', '--rm', '--gpus', 'all', '--entrypoint', 'nvidia-smi', $release.ollamaImage, '-L') -Timeout 1800 -AllowFailure
        if ($gpu.ExitCode -ne 0) {
            Write-Host 'GPU niedostepne dla Dockera: wybieram CPU. Sprawdz sterowniki NVIDIA/WSL2.'
            $profile = Get-HardwareProfile $ram 0
            $config.GPU = $false; $config.Model = $profile.Model; $config.Context = $profile.Context
        }
    }
    $envPath = Join-Path $InstallDir '.env'
    $token = ''
    if (Test-Path -LiteralPath $envPath) { $old = Get-Content -LiteralPath $envPath | Where-Object { $_.StartsWith('BROKER_TOKEN=') }; if ($old) { $token = $old.Substring(13) } }
    if (-not $token) { $bytes = New-Object byte[] 32; $rng = [Security.Cryptography.RandomNumberGenerator]::Create(); $rng.GetBytes($bytes); $rng.Dispose(); $token = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant() }
    $envText = @("VEKTOR_IMAGE=$($release.agentImage)", "OLLAMA_IMAGE=$($release.ollamaImage)", "VEKTOR_PORT=$($config.Port)", "BROKER_PORT=$($config.BrokerPort)", "BROKER_TOKEN=$token", "HOST_ENABLED=$(([string]$config.HostEnabled).ToLowerInvariant())", "VEKTOR_WORKSPACE=$($config.Workspace.Replace('\','/'))", "LOCAL_MODEL=$($config.Model)", "LOCAL_CONTEXT=$($config.Context)", "CLOUD_MODEL=$($release.cloudModel)", "STRONG_MODEL=$($release.strongModel)", 'MODEL_MODE=auto') -join "`n"
    Write-PrivateFile $envPath $envText
    Write-PrivateFile $configPath ($config | ConvertTo-Json)
    $compose = Get-ComposeArguments $InstallDir $config
    $running = Invoke-Checked $docker ($compose + @('ps', '-q', '--status', 'running', 'agent')) -Timeout 30 -AllowFailure
    if ($running.ExitCode -eq 0 -and $running.Output.Trim()) {
        Write-Host 'Kopia bezpieczenstwa bazy przed aktualizacja...'
        $backupCode = 'import sqlite3,datetime,pathlib; p=pathlib.Path("/app/data/backups"); p.mkdir(exist_ok=True); sqlite3.connect("/app/data/agent.db").backup(sqlite3.connect(str(p/("pre-update-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+".db"))))'
        $null = Invoke-Checked $docker ($compose + @('exec', '-T', 'agent', 'python', '-c', $backupCode)) -Timeout 120
    }
    Write-Host 'Pobieranie przypietych obrazow VEKTORA i Ollamy...'
    $null = Invoke-Checked $docker ($compose + @('pull')) -Timeout 3600
    Start-Broker $InstallDir $config
    $null = Invoke-Checked $docker ($compose + @('up', '-d', '--wait', '--wait-timeout', '240')) -Timeout 300
    foreach ($model in @($config.Model, 'gemma3:4b')) {
        if ($SkipModelDownload) { Write-Host 'Test instalacji: pominieto pobieranie modeli.'; break }
        Write-Host "Pobieranie modelu $model (zaleznie od lacza moze trwac kilkanascie minut)..."
        $null = Invoke-Checked $docker ($compose + @('exec', '-T', 'ollama', 'ollama', 'pull', $model)) -Timeout 7200
    }
    $health = Invoke-RestMethod "http://127.0.0.1:$($config.Port)/api/health" -TimeoutSec 30
    if (-not $health.ollama.connected) { throw 'VEKTOR nie laczy sie z Ollama.' }
    if ($config.HostEnabled) {
        $null = Invoke-Checked $docker ($compose + @('exec', '-T', 'agent', 'python', '-c', 'import os,urllib.request; urllib.request.urlopen(os.environ["HOST_BROKER_URL"]+"/health",timeout=10)')) -Timeout 30
    }
    if (-not $NoShortcuts) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'VEKTOR.lnk'))
    $shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$(Join-Path $InstallDir 'Start-VEKTOR.ps1')`""
    $shortcut.WorkingDirectory = $InstallDir; $shortcut.Description = 'VEKTOR - asystent AI'; $shortcut.IconLocation = 'shell32.dll,14'; $shortcut.Save()
    if ($config.Autostart) {
        $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
        New-Item -Path $key -Force | Out-Null
        New-ItemProperty -Path $key -Name 'VEKTOR-Desktop' -Value "`"$($shortcut.TargetPath)`" $($shortcut.Arguments)" -PropertyType String -Force | Out-Null
    }
    }
    Write-Host "GOTOWE: http://127.0.0.1:$($config.Port). Logowanie cloud: Cloud-Login.ps1. Dane i modele zachowane w woluminach vektor-desktop."
} catch { Write-Host "ERROR: $($_.Exception.Message)"; Write-Host $_.ScriptStackTrace; exit 1 }
finally { if ($ownsLock) { $lock.ReleaseMutex() }; $lock.Dispose() }
