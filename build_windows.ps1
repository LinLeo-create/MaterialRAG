$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $env:CONDA_PREFIX "python.exe"

if (-not $env:CONDA_PREFIX -or -not (Test-Path $Python)) {
    throw "Please activate the materialrag Conda environment first."
}

Push-Location $ProjectRoot
try {
    $env:PYTHONNOUSERSITE = "1"
    npm.cmd run build
    & $Python -m PyInstaller --noconfirm --clean MaterialRAG.spec
} finally {
    Pop-Location
}
