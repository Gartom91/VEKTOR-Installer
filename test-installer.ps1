$ErrorActionPreference = 'Stop'
$errors = @()
foreach ($file in Get-ChildItem payload -Filter *.ps1) {
    $parseErrors = $null
    [void][Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$null, [ref]$parseErrors)
    if ($parseErrors) { $errors += $parseErrors }
}
if ($errors) { $errors | Out-String | Write-Error; exit 1 }
. ./payload/Common.ps1
$profiles = @(
    @{ Ram = 8; Vram = 0; Model = 'qwen3:1.7b'; Context = 4096; GPU = $false },
    @{ Ram = 16; Vram = 0; Model = 'qwen3:4b'; Context = 4096; GPU = $false },
    @{ Ram = 16; Vram = 4096; Model = 'qwen3:4b'; Context = 4096; GPU = $true },
    @{ Ram = 32; Vram = 6144; Model = 'qwen3:8b'; Context = 8192; GPU = $true },
    @{ Ram = 32; Vram = 12000; Model = 'qwen3:8b'; Context = 16384; GPU = $true }
)
foreach ($case in $profiles) {
    $actual = Get-HardwareProfile $case.Ram $case.Vram
    foreach ($key in 'Model','Context','GPU') { if ($actual[$key] -ne $case[$key]) { throw "Hardware profile mismatch: $($case | ConvertTo-Json -Compress)" } }
}
try { Get-HardwareProfile 4 0; throw 'Low RAM must fail' } catch { if ($_.Exception.Message -notlike '*8 GB*') { throw } }
$listener = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback, 29700); $listener.Start()
try { if ((Get-FreePort 29700) -eq 29700) { throw 'Port detection failed' } } finally { $listener.Stop() }
$release = Get-Content payload/release.json -Raw | ConvertFrom-Json
if ($release.agentImage -notmatch '@sha256:[a-f0-9]{64}$' -or $release.ollamaImage -notmatch '@sha256:[a-f0-9]{64}$') { throw 'Images must be pinned by digest' }
if ((Get-Content payload/compose.yaml -Raw) -notmatch 'OLLAMA_MAX_LOADED_MODELS: "1"') { throw 'Local model limit missing' }
$result = Invoke-Checked (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') @('-NoProfile', '-Command', 'exit 7') -AllowFailure
if ($result.ExitCode -ne 7) { throw 'Child exit code lost' }
Write-Host 'PASS: parser, 5 hardware profiles, low RAM, occupied port, pinned images, local model limit, process exit code.'
$privateTest = Join-Path ([IO.Path]::GetTempPath()) ('vektor-acl-' + [guid]::NewGuid().ToString('N') + '.txt')
try {
    Write-PrivateFile $privateTest 'test-not-a-secret'
    Write-PrivateFile $privateTest 'updated'
    if (-not (Get-Acl -LiteralPath $privateTest).AreAccessRulesProtected) { throw 'Private file ACL is inherited' }
    if ((Get-Content -LiteralPath $privateTest) -ne 'updated') { throw 'Private file update failed' }
} finally { if (Test-Path -LiteralPath $privateTest) { Remove-Item -LiteralPath $privateTest } }
Write-Host 'PASS: private ACL create and update without administrator privileges.'
