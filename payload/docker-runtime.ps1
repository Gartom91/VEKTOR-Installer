# Docker Desktop 4.88.1 / Windows: AF_UNIX runtime endpoints can survive shutdown
# and make the next start fail with Win32 1920. Keep this file PS 5.1 compatible.
# This is a startup workaround, not a modification of Docker's binaries.

function Test-VektorDockerProcess {
    # A backend monitor, the UI, or a shutdown in progress must prevent recovery.
    return [bool](Get-Process -Name 'Docker Desktop', 'com.docker.backend', 'com.docker.build', 'com.docker.proxy', 'docker-agent' -ErrorAction SilentlyContinue)
}

function Assert-VektorPlainDirectory([string]$Path) {
    # Do not follow user-created junctions/symlinks, including in ancestors.
    $directory = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (-not $directory.PSIsContainer) { throw "Not a directory: $Path" }
    while ($directory) {
        if ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Runtime recovery refuses a linked directory: $($directory.FullName)"
        }
        $directory = $directory.Parent
    }
}

function Repair-VektorDockerRuntime {
    [CmdletBinding()]
    param([string]$LocalAppData = [Environment]::GetFolderPath('LocalApplicationData'))

    if (Test-VektorDockerProcess) { throw 'Docker is running or stopping; runtime recovery was not performed.' }
    if (-not [IO.Path]::IsPathRooted($LocalAppData)) { throw 'LocalAppData must be an absolute path.' }
    $basePath = [IO.Path]::GetFullPath($LocalAppData).TrimEnd('\')
    if ($basePath -eq [IO.Path]::GetPathRoot($basePath).TrimEnd('\')) { throw 'Refusing a drive root.' }
    Assert-VektorPlainDirectory $basePath
    $definitions = @(
        @{ Relative = 'Docker\run'; Names = @('sailor-ingest.sock', 'dockerInference', 'dockerEthernetVfkit', 'userAnalyticsOtlpHttp.sock') },
        @{ Relative = 'docker-secrets-engine'; Names = @('engine.sock') }
    )
    $pending = @()
    # Validate BOTH directories before touching either one. Unknown files are not
    # assumed disposable, even if they happen to have a .sock suffix.
    foreach ($definition in $definitions) {
        $targetPath = [IO.Path]::GetFullPath((Join-Path $basePath $definition.Relative))
        if (-not $targetPath.StartsWith($basePath + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Unexpected runtime target: $targetPath"
        }
        if (-not (Test-Path -LiteralPath $targetPath)) { continue }
        Assert-VektorPlainDirectory $targetPath
        $children = @(Get-ChildItem -LiteralPath $targetPath -Force -ErrorAction Stop)
        if (-not $children.Count) { continue }
        foreach ($child in $children) {
            if ($child.PSIsContainer -or $definition.Names -notcontains $child.Name -or
                -not ($child.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw "Unexpected runtime content; nothing moved: $($child.FullName)"
            }
        }
        $backupPath = $targetPath + '.vektor-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
        $pending += [pscustomobject]@{ Source = $targetPath; Backup = $backupPath }
    }
    if (Test-VektorDockerProcess) { throw 'Docker started during validation; recovery was cancelled.' }
    foreach ($item in $pending) {
        if (Test-VektorDockerProcess) { throw 'Docker started during recovery; no more directories will be moved.' }
        # A same-parent rename does not traverse the inaccessible socket objects.
        # Do not delete sockets, recurse, reset Docker, change ACLs, or touch WSL.
        Move-Item -LiteralPath $item.Source -Destination $item.Backup -ErrorAction Stop
        $item
    }
}
