param(
    [string]$Installer = (Join-Path $PSScriptRoot 'dist\VEKTOR-Setup-x64.exe'),
    [string]$OutputDir = (Join-Path ([IO.Path]::GetTempPath()) ('vektor-payload-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
$Installer = (Resolve-Path -LiteralPath $Installer).Path
$OutputDir = [IO.Path]::GetFullPath($OutputDir)
if (Test-Path -LiteralPath $OutputDir) { throw 'Payload test requires a new, empty output directory.' }
New-Item -ItemType Directory -Path $OutputDir | Out-Null
$extract = Start-Process -FilePath $Installer -ArgumentList @('--extract', ('"' + $OutputDir + '"')) -PassThru -Wait -WindowStyle Hidden
if ($extract.ExitCode -ne 0) { throw 'Installer extraction failed.' }
$expected = Get-Content (Join-Path $PSScriptRoot 'payload\release.json') -Raw | ConvertFrom-Json
$packaged = Get-Content (Join-Path $OutputDir 'release.json') -Raw | ConvertFrom-Json
foreach ($key in 'version','agentImage','diffusionImage','ollamaImage','cloudModel','visionModel','updateProtocol') {
    if ($packaged.$key -ne $expected.$key) { throw "Wrong embedded release field: $key" }
}
$actualVersion = [Diagnostics.FileVersionInfo]::GetVersionInfo($Installer).FileVersion
if ($actualVersion -notlike "$($expected.version).*") { throw 'Wrong EXE version.' }
# Git checkout on Windows may use CRLF while an edited working copy uses LF.
# Normalize only line endings, never spaces, case, values or other content.
$sourceCompose = (Get-Content (Join-Path $PSScriptRoot 'payload\compose.yaml') -Raw).Replace("`r`n", "`n")
$packagedCompose = (Get-Content (Join-Path $OutputDir 'compose.yaml') -Raw).Replace("`r`n", "`n")
if ($sourceCompose -cne $packagedCompose) { throw 'Wrong embedded Compose configuration.' }
$hostExe = (Resolve-Path -LiteralPath (Join-Path $OutputDir 'VEKTOR-Host.exe')).Path
$listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 0)
$listener.Start()
$testPort = $listener.LocalEndpoint.Port
$listener.Stop()
$testToken = [guid]::NewGuid().ToString('N')
$priorEnvironment = @{}
foreach ($key in 'HOST_BROKER_TOKEN','HOST_BROKER_PORT','HOST_BROKER_ROOTS','HOST_BROKER_TOOLS_ENABLED','VEKTOR_INSTALL_ROOT','VEKTOR_APP_URL') {
    $priorEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
try {
    $env:HOST_BROKER_TOKEN = $testToken
    $env:HOST_BROKER_PORT = [string]$testPort
    $env:HOST_BROKER_ROOTS = $OutputDir
    $env:HOST_BROKER_TOOLS_ENABLED = 'false'
    Remove-Item Env:VEKTOR_INSTALL_ROOT -ErrorAction SilentlyContinue
    Remove-Item Env:VEKTOR_APP_URL -ErrorAction SilentlyContinue
    $child = Start-Process -FilePath $hostExe -WorkingDirectory $OutputDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $OutputDir 'test-host-out.log') -RedirectStandardError (Join-Path $OutputDir 'test-host-error.log')
    $deadline = (Get-Date).AddSeconds(40)
    $health = $null
    do {
        if ($child.HasExited) { throw "Packaged host exited: $($child.ExitCode). See test-host-error.log." }
        try { $health = Invoke-RestMethod "http://127.0.0.1:$testPort/health" -TimeoutSec 1 } catch {}
        if ($health.status -eq 'ok') { break }
        Start-Sleep -Milliseconds 200
    } while ((Get-Date) -lt $deadline)
    if ($health.status -ne 'ok' -or $health.configured_root_count -ne 1) { throw 'Packaged host healthcheck failed.' }
    if ($health.update_protocol -ne 2 -or $health.host_tools_enabled) { throw 'Updater protocol or host-tools opt-in is missing.' }
    $unauthorizedStatus = 0
    try { $null = Invoke-WebRequest "http://127.0.0.1:$testPort/v1/system/metrics" -UseBasicParsing -TimeoutSec 3 }
    catch { if ($_.Exception.Response) { $unauthorizedStatus = [int]$_.Exception.Response.StatusCode } else { throw } }
    if ($unauthorizedStatus -ne 401) { throw 'Packaged host accepted a missing credential.' }
    $updateStatus = 0
    try { $null = Invoke-WebRequest "http://127.0.0.1:$testPort/v1/updates" -UseBasicParsing -TimeoutSec 3 }
    catch { if ($_.Exception.Response) { $updateStatus = [int]$_.Exception.Response.StatusCode } else { throw } }
    if ($updateStatus -ne 401) { throw 'Updater accepted a missing credential.' }
    $metrics = Invoke-RestMethod "http://127.0.0.1:$testPort/v1/system/metrics" -Headers @{ Authorization = "Bearer $testToken" } -TimeoutSec 15
    if ('cpu_percent' -notin $metrics.PSObject.Properties.Name -or 'gpus' -notin $metrics.PSObject.Properties.Name) { throw 'Packaged host metrics API missing.' }
    Write-Host "PASS: EXE $actualVersion, embedded release and Compose, packaged host startup, credential gate, metrics, update protocol, disabled host tools."
    Write-Host "Test files retained: $OutputDir"
} finally {
    # Stop only this extracted copy, never an installed VEKTOR host process.
    Get-Process -Name 'VEKTOR-Host' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $hostExe } | Stop-Process -ErrorAction SilentlyContinue
    foreach ($key in $priorEnvironment.Keys) { [Environment]::SetEnvironmentVariable($key, $priorEnvironment[$key], 'Process') }
}
