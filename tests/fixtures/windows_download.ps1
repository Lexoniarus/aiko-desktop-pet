param([string]$Python, [string]$Scenario)
$script:TestPythonExecutable = $Python
. "$PSScriptRoot\tools\install_windows.ps1" -NoShortcuts
$script:discoveryCount = 0
$script:installCount = 0
$script:downloadFile = $null
$script:protocolBefore = [Net.ServicePointManager]::SecurityProtocol
$env:PROCESSOR_ARCHITECTURE = 'x86'
$env:PROCESSOR_ARCHITEW6432 = 'AMD64'
function Find-CompatiblePython {
    $script:discoveryCount++
    if ($Scenario -eq 'unusable') { return $null }
    if ($Scenario -eq 'repair' -and $script:installCount -lt 2) { return $null }
    if ($script:installCount -gt 0) { return $script:TestPythonExecutable }
    return $null
}
function Get-Command {
    throw 'No launcher, PATH Python or WinGet available in this scenario'
}
function Invoke-WebRequest {
    param($Uri, $OutFile, [switch]$UseBasicParsing, $TimeoutSec)
    $script:downloadFile = $OutFile
    if (-not $UseBasicParsing) { throw 'Missing PS 5.1 compatibility' }
    if (-not (
        [Net.ServicePointManager]::SecurityProtocol -band
        [Net.SecurityProtocolType]::Tls12
    )) {
        throw 'TLS 1.2 not enabled'
    }
    $Uri | Set-Content "$PSScriptRoot\url.txt"
    if ($Scenario -eq 'offline') { throw 'Test: Netzwerk nicht erreichbar' }
    'Fake installer; never executed' | Set-Content -LiteralPath $OutFile
}
function Get-FileHash {
    param($LiteralPath, $Algorithm)
    if ($LiteralPath -ne $script:downloadFile -or $Algorithm -ne 'SHA256') {
        throw 'Unexpected checksum request'
    }
    $checksum = (Get-PythonDownload 'AMD64').Sha256
    if ($Scenario -eq 'bad-hash') { $checksum = '0000' }
    return [pscustomobject]@{ Hash = $checksum }
}
function Start-Process {
    param($FilePath, $ArgumentList, $WindowStyle, [switch]$Wait, [switch]$PassThru)
    if (
        $FilePath -ne $script:downloadFile -or -not $Wait -or
        -not $PassThru -or $WindowStyle -ne 'Hidden'
    ) {
        throw 'Unexpected process parameters'
    }
    $script:installCount++
    ConvertTo-Json -InputObject @($ArgumentList) |
        Set-Content "$PSScriptRoot\install-$script:installCount.json"
    $code = 0
    if ($Scenario -eq 'failed') { $code = 42 }
    if ($Scenario -eq 'reboot') { $code = 3010 }
    return [pscustomobject]@{ ExitCode = $code }
}
try {
    if ($Scenario -eq 'no-install') {
        $script:NoPythonInstall = $true
        Invoke-AikoSetup
    } elseif ($Scenario -eq 'success') {
        # One complete automatic-install path verifies the setup wiring.
        Invoke-AikoSetup
    } else {
        # Repair, reboot and failure cases exercise the real download helper.
        # Recreating venv/pip here repeats the complete setup integration above.
        $installed = Install-PythonWithTk
        if ($installed -ne $script:TestPythonExecutable) {
            throw 'Did not return the discovered Python runtime'
        }
    }
    exit 0
} catch {
    Write-Host $_.Exception.Message
    exit 1
} finally {
    if ([Net.ServicePointManager]::SecurityProtocol -ne $script:protocolBefore) {
        throw 'Network security protocol was not restored'
    }
    if (
        $script:downloadFile -and
        (Test-Path -LiteralPath (Split-Path -Parent $script:downloadFile))
    ) {
        throw 'Temporary download was not removed'
    }
}
