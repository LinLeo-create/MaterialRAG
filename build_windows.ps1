param(
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = if ($PythonPath) { $PythonPath } else { Join-Path $env:CONDA_PREFIX "python.exe" }

if ((-not $PythonPath -and -not $env:CONDA_PREFIX) -or -not (Test-Path $Python)) {
    throw "Please activate the materialrag Conda environment first."
}

Push-Location $ProjectRoot
try {
    $env:PYTHONNOUSERSITE = "1"
    & $Python -c "import PyInstaller"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller is not installed in the active Conda environment."
    }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed."
    }
    & $Python -m PyInstaller --noconfirm --clean MaterialRAG.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }
} finally {
    Pop-Location
}
