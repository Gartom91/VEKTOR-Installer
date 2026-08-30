# Must match host_broker.updater.compose_lock_name (Windows, per installation).
function Get-VektorComposeMutexName([string]$InstallDir) {
    $canonical = [IO.Path]::GetFullPath($InstallDir).TrimEnd('\').ToLowerInvariant()
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canonical))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
    return 'Local\VEKTOR.UpdateCompose.' + $hash.Substring(0,24)
}

function Enter-VektorComposeOperation([string]$InstallDir, [int]$TimeoutSeconds = 300) {
    $mutex = New-Object Threading.Mutex($false, (Get-VektorComposeMutexName $InstallDir))
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    try {
        do {
            $owned = $false
            try { $owned = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $owned = $true }
            if ($owned) {
                if (-not (Test-Path -LiteralPath (Join-Path $InstallDir 'data\updater\transaction.json'))) { return $mutex }
                $mutex.ReleaseMutex()
                $statePath = Join-Path $InstallDir 'data\updater\status.json'
                if (Test-Path -LiteralPath $statePath) {
                    $phase = (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json).phase
                    if ($phase -eq 'recovery_required') { throw 'Przerwana aktualizacja wymaga diagnostyki. Nie uruchamiam kontenera podczas niepewnego odtwarzania danych. Sprawdz data/updater/status.json.' }
                }
            }
            Start-Sleep -Milliseconds 500
        } while ((Get-Date) -lt $deadline)
        throw 'Aktualizacja lub odtwarzanie danych nadal trwa. Poczekaj i uruchom VEKTORA ponownie; nie usuwaj kopii ani dziennika aktualizacji.'
    } catch { $mutex.Dispose(); throw }
}
