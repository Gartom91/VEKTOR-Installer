$ErrorActionPreference = 'Stop'
$errors = @()
foreach ($file in (@(Get-ChildItem payload -Filter *.ps1) + @(Get-ChildItem . -Filter *.ps1))) {
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
if ($release.agentImage -notmatch '@sha256:[a-f0-9]{64}$' -or $release.ollamaImage -notmatch '@sha256:[a-f0-9]{64}$' -or $release.diffusionImage -notmatch '@sha256:[a-f0-9]{64}$') { throw 'Images must be pinned by digest' }
if ($release.updateProtocol -ne 2) { throw 'Update protocol missing from the release manifest.' }
if ((Get-Content payload/compose.yaml -Raw) -notmatch 'OLLAMA_MAX_LOADED_MODELS: "1"') { throw 'Local model limit missing' }
if ($release.cloudModel -ne 'glm-5.3:cloud' -or $release.visionModel -ne 'glm-5.3-flash:cloud') { throw 'Hybrid model defaults missing' }
$composeText = Get-Content payload/compose.yaml -Raw
foreach ($binding in @('OLLAMA_MODEL: ${CLOUD_MODEL:-glm-5.3:cloud}', 'OLLAMA_VISION_MODEL: ${VISION_MODEL:-glm-5.3-flash:cloud}', 'VISION_AUTO: ${VISION_AUTO:-true}', 'VISION_FOLLOWUP_LIMIT: ${VISION_FOLLOWUP_LIMIT:-2}', 'OLLAMA_NUM_PARALLEL: "1"')) {
    if (-not $composeText.Contains($binding)) { throw "Missing Compose binding: $binding" }
}
foreach ($binding in @('STABLE_DIFFUSION_URL: http://stable-diffusion:8770', 'image: ${DIFFUSION_IMAGE:?Required pinned diffusion image}', 'profiles: ["images"]', 'stable-diffusion-models:/models')) {
    if (-not $composeText.Contains($binding)) { throw "Missing Stable Diffusion binding: $binding" }
}
$installScript = Get-Content payload/Install-VEKTOR.ps1 -Raw
if (-not $installScript.Contains('VISION_MODEL=$($release.visionModel)')) { throw 'Vision model not written to install environment' }
if (-not $installScript.Contains('DIFFUSION_IMAGE=$($release.diffusionImage)')) { throw 'Stable Diffusion image not written to install environment' }
$projectXml = [xml](Get-Content src/VEKTOR.Setup.csproj -Raw)
if ($projectXml.Project.PropertyGroup.Version -ne $release.version) { throw 'Installer and payload versions differ' }
$result = Invoke-Checked (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') @('-NoProfile', '-Command', 'exit 7') -AllowFailure
if ($result.ExitCode -ne 7) { throw 'Child exit code lost' }
Write-Host 'PASS: parser, 5 hardware profiles, low RAM, occupied port, pinned images, local limits, hybrid defaults, version consistency, process exit code.'
$privateTest = Join-Path ([IO.Path]::GetTempPath()) ('vektor-acl-' + [guid]::NewGuid().ToString('N') + '.txt')
try {
    Write-PrivateFile $privateTest 'test-not-a-secret'
    Write-PrivateFile $privateTest 'updated'
    if (-not (Get-Acl -LiteralPath $privateTest).AreAccessRulesProtected) { throw 'Private file ACL is inherited' }
    if ((Get-Content -LiteralPath $privateTest) -ne 'updated') { throw 'Private file update failed' }
} finally { if (Test-Path -LiteralPath $privateTest) { Remove-Item -LiteralPath $privateTest } }
Write-Host 'PASS: private ACL create and update without administrator privileges.'
$pinTest = Join-Path ([IO.Path]::GetTempPath()) ('vektor-pin-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $pinTest | Out-Null
$pinFile = Join-Path $pinTest 'compose.update.yaml'
$oldImage = 'gartom91/local-ai-agent:1.5.4@sha256:' + ('a' * 64)
$newImage = 'gartom91/local-ai-agent:1.6.0@sha256:' + ('b' * 64)
$newDiffusion = 'gartom91/vektor-diffusion:1.6.0@sha256:' + ('c' * 64)
$header = "# Managed by VEKTOR updater. Data and other services are unchanged.`nservices:`n  agent:`n    image: "
if (Get-ManagedUpdatePin $pinTest) { throw 'Missing pin should return null.' }
Write-PrivateFile $pinFile ($header + $oldImage + "`n")
if ((Get-ManagedUpdatePin $pinTest) -ne $oldImage) { throw 'Managed pin was not parsed.' }
Set-InstallerUpdatePin $pinTest $newImage $newDiffusion
if ((Get-ManagedUpdatePin $pinTest) -ne $newImage) { throw 'Installer did not override the old automatic image pin.' }
if ((Read-ManagedUpdatePins $pinTest).Diffusion -ne $newDiffusion) { throw 'Installer did not pin the matching Stable Diffusion image.' }
$savedPins = @(Get-ChildItem -LiteralPath $pinTest -Filter 'compose.update.before-installer-*.yaml')
if ($savedPins.Count -ne 1 -or -not (Get-Content -LiteralPath $savedPins[0].FullName -Raw).Contains($oldImage)) { throw 'Previous pin backup missing.' }
Write-PrivateFile $pinFile "services:`n  agent:`n    image: custom`n"
try { Set-InstallerUpdatePin $pinTest $newImage $newDiffusion; throw 'Custom pin was overwritten.' } catch { if ($_.Exception.Message -notlike '*Niestandardowy*') { throw } }
Write-Host "PASS: automatic image pin survives startup, newer installer preserves/replaces managed pin, custom overrides rejected. Fixture retained: $pinTest"
