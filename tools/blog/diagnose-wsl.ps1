#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $env:TEMP 'codex-optee-wsl-diagnostic.json')
)

$ErrorActionPreference = 'Stop'
$features = foreach ($name in @('VirtualMachinePlatform', 'Microsoft-Windows-Subsystem-Linux', 'Microsoft-Hyper-V-Hypervisor')) {
    try {
        $feature = Get-WindowsOptionalFeature -Online -FeatureName $name
        [pscustomobject]@{ Name = $name; State = [string]$feature.State }
    } catch {
        [pscustomobject]@{ Name = $name; Error = $_.Exception.Message }
    }
}
$boot = & "$env:SystemRoot\System32\bcdedit.exe" /enum 2>&1
$bootExitCode = $LASTEXITCODE
$report = [ordered]@{
    Timestamp = (Get-Date).ToString('o')
    Purpose = 'Read-only WSL diagnosis; no Windows feature, boot setting, or distribution is changed.'
    Features = @($features)
    HypervisorPresent = (Get-CimInstance Win32_ComputerSystem).HypervisorPresent
    Processors = @(Get-CimInstance Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled, VMMonitorModeExtensions, SecondLevelAddressTranslationExtensions)
    Services = @(Get-Service vmcompute,WslService -ErrorAction SilentlyContinue | Select-Object Name,@{Name='Status';Expression={[string]$_.Status}},@{Name='StartType';Expression={[string]$_.StartType}})
    BootConfiguration = ($boot | Out-String)
    BootExitCode = $bootExitCode
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output "Diagnostic saved to $OutputPath"
Write-Output 'No changes were made. Return to Codex and say the diagnostic is ready.'
