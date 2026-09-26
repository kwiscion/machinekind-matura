# Keep this project's HF login/cache separate from other account sessions.
$ErrorActionPreference = 'Stop'
$hfExitCode = 1
$previousHfHome = $env:HF_HOME
$projectRoot = Split-Path -Parent $PSScriptRoot
try {
    $env:HF_HOME = Join-Path $projectRoot '.hf-home'
    Push-Location -LiteralPath $projectRoot
    try {
        & uv run hf @args
        $hfExitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
} finally {
    $env:HF_HOME = $previousHfHome
}
exit $hfExitCode
