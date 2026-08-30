param([switch]$RemoveData)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'installation.json') -Raw | ConvertFrom-Json
$docker = Find-Docker
if ($docker) {
    $compose = Get-ComposeArguments $PSScriptRoot $config
    $commandArgs = $compose + @('down')
    if ($RemoveData) { $commandArgs += '--volumes' }
    Invoke-Checked $docker $commandArgs -Timeout 300 -AllowFailure | Out-Null
}
$pidFile = Join-Path $PSScriptRoot 'broker.pid'
if (Test-Path -LiteralPath $pidFile) {
    $process = Get-Process -Id ([int](Get-Content -LiteralPath $pidFile)) -ErrorAction SilentlyContinue
    if ($process -and $process.Path -eq (Join-Path $PSScriptRoot 'VEKTOR-Host.exe')) { Get-Process -Name 'VEKTOR-Host' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $PSScriptRoot 'VEKTOR-Host.exe') } | Stop-Process -ErrorAction SilentlyContinue }
}
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$owned = Get-ItemPropertyValue -Path $runKey -Name 'VEKTOR-Desktop' -ErrorAction SilentlyContinue
if ($owned -and $owned -like "*$PSScriptRoot*") { Remove-ItemProperty -Path $runKey -Name 'VEKTOR-Desktop' }
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'VEKTOR.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
    if ($shortcut.Arguments -like "*$PSScriptRoot*") { Remove-Item -LiteralPath $shortcutPath }
}
if ($RemoveData) { Write-Warning 'Woluminy z rozmowami, pamiecia i modelami usunieto. Pliki instalacyjne pozostaly do recznego usuniecia.' } else { Write-Host 'VEKTOR zatrzymany i usuniety z autostartu. Dane i modele zachowano. Uruchom Start-VEKTOR.ps1, aby wznowic.' }
