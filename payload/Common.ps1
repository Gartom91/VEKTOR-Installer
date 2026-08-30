$ErrorActionPreference = 'Stop'

function Find-Docker {
    foreach ($candidate in @((Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'), (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'))) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $command = Get-Command docker.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    return $null
}

function Invoke-Checked([string]$File, [string[]]$Arguments, [int]$Timeout = 900, [switch]$AllowFailure) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $File
    $info.Arguments = ($Arguments | ForEach-Object { if ($_ -ne '' -and $_ -notmatch '[\s"]') { $_ } else { '"' + ($_ -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"' } }) -join ' '
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $outTask = $process.StandardOutput.ReadToEndAsync()
        $errTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($Timeout * 1000)) { $process.Kill(); throw "Timeout po $Timeout s: $([IO.Path]::GetFileName($File))" }
        $process.WaitForExit()
        $result = [pscustomobject]@{ ExitCode = $process.ExitCode; Output = $outTask.Result + $errTask.Result }
        if ($result.ExitCode -ne 0 -and -not $AllowFailure) { throw "Kod $($result.ExitCode): $($result.Output)" }
        return $result
    } finally { $process.Dispose() }
}

function Get-HardwareProfile([double]$RamGB, [int]$VramMB) {
    if ($RamGB -lt 7.5) { throw 'Wymagane co najmniej 8 GB RAM.' }
    if ($VramMB -ge 10000) { return @{ Model = 'qwen3:8b'; Context = 16384; GPU = $true } }
    if ($VramMB -ge 6000) { return @{ Model = 'qwen3:8b'; Context = 8192; GPU = $true } }
    if ($VramMB -ge 4000) { return @{ Model = 'qwen3:4b'; Context = 4096; GPU = $true } }
    if ($RamGB -ge 16) { return @{ Model = 'qwen3:4b'; Context = 4096; GPU = $false } }
    return @{ Model = 'qwen3:1.7b'; Context = 4096; GPU = $false }
}

function Get-FreePort([int]$Preferred) {
    foreach ($port in $Preferred..($Preferred + 50)) {
        $listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, $port)
        try { $listener.Start(); return $port } catch {} finally { $listener.Stop() }
    }
    throw 'Brak wolnego portu lokalnego.'
}

function Get-ComposeArguments([string]$InstallDir, $Config) {
    $result = @('compose', '--project-name', 'vektor-desktop', '--project-directory', $InstallDir, '--env-file', (Join-Path $InstallDir '.env'), '-f', (Join-Path $InstallDir 'compose.yaml'))
    if ($Config.GPU) { $result += @('-f', (Join-Path $InstallDir 'compose.gpu.yaml')) }
    return $result
}

function Write-PrivateFile([string]$Path, [string]$Content) {
    [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding($false)))
    $acl = [IO.File]::GetAccessControl($Path, [Security.AccessControl.AccessControlSections]::Access)
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
    $user = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($user, 'FullControl', 'Allow')))
    $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule('SYSTEM', 'FullControl', 'Allow')))
    [IO.File]::SetAccessControl($Path, $acl)
}

function Wait-Docker([string]$Docker) {
    $check = Invoke-Checked $Docker @('info', '--format', '{{.OSType}}') -Timeout 20 -AllowFailure
    if ($check.ExitCode -eq 0) {
        if ($check.Output.Trim() -ne 'linux') { throw 'Przelacz Docker Desktop na Linux containers.' }
        return
    }
    . (Join-Path $PSScriptRoot 'docker-runtime.ps1')
    if (-not (Test-VektorDockerProcess)) {
        Repair-VektorDockerRuntime | ForEach-Object { Write-Host "Zachowano stare endpointy Dockera: $($_.Backup)" }
        $desktop = @((Join-Path $env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe'), (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe')) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        if (-not $desktop) { throw 'Nie znaleziono Docker Desktop.' }
        Start-Process -FilePath $desktop -WindowStyle Hidden
    }
    $deadline = (Get-Date).AddSeconds(300)
    do {
        Start-Sleep -Seconds 3
        $check = Invoke-Checked $Docker @('info', '--format', '{{.OSType}}') -Timeout 15 -AllowFailure
        if ($check.ExitCode -eq 0 -and $check.Output.Trim() -eq 'linux') { return }
    } while ((Get-Date) -lt $deadline)
    throw 'Docker nie wystartowal w 300 s. Sprawdz jego okno, WSL2, wirtualizacje BIOS i ewentualny wymagany restart.'
}

function Start-Broker([string]$InstallDir, $Config) {
    if (-not $Config.HostEnabled) { return }
    $exe = Join-Path $InstallDir 'VEKTOR-Host.exe'
    $pidFile = Join-Path $InstallDir 'broker.pid'
    if (Test-Path -LiteralPath $pidFile) {
        $brokerProcess = Get-Process -Id ([int](Get-Content -LiteralPath $pidFile)) -ErrorAction SilentlyContinue
        if ($brokerProcess -and $brokerProcess.Path -eq $exe) { return }
    }
    $line = Get-Content -LiteralPath (Join-Path $InstallDir '.env') | Where-Object { $_.StartsWith('BROKER_TOKEN=') }
    $env:HOST_BROKER_TOKEN = $line.Substring(13)
    $env:HOST_BROKER_PORT = [string]$Config.BrokerPort
    $env:HOST_BROKER_ROOTS = ($Config.HostRoots -join ';')
    try {
        $child = Start-Process -FilePath $exe -WorkingDirectory $InstallDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $InstallDir 'broker-out.log') -RedirectStandardError (Join-Path $InstallDir 'broker-error.log')
        [IO.File]::WriteAllText($pidFile, [string]$child.Id)
    } finally { Remove-Item Env:HOST_BROKER_TOKEN -ErrorAction SilentlyContinue }
}
