$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageDir = Join-Path $ProjectRoot "dist\MaterialRAG"
$ReleaseDir = Join-Path $ProjectRoot "release"
$Version = (Get-Content (Join-Path $ProjectRoot "package.json") | ConvertFrom-Json).version
$Archive = Join-Path $ReleaseDir "MaterialRAG-$Version-windows-x64.zip"

& (Join-Path $ProjectRoot "build_windows.ps1")
Copy-Item (Join-Path $ProjectRoot "PACKAGE_README.txt") (Join-Path $PackageDir "README.txt") -Force
New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
if (Test-Path $Archive) {
    Remove-Item -LiteralPath $Archive -Force
}
Compress-Archive -Path $PackageDir -DestinationPath $Archive -CompressionLevel Optimal
Write-Host "Release archive: $Archive"
