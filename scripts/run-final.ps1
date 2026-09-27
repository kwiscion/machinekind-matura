[CmdletBinding(DefaultParameterSetName='Start')]
param(
  [Parameter(Mandatory=$true,ParameterSetName='Start')][string]$ExamPath,
  [Parameter(Mandatory=$true,ParameterSetName='Resume')][string]$Resume,
  [Parameter(ParameterSetName='Start')][switch]$Smoke,
  [Parameter(ParameterSetName='Start')][ValidateRange(15,55)][int]$RemoteMinutes=55
)
$ErrorActionPreference='Stop'
$StartedUtc=[DateTimeOffset]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.ffffffzzz')
$RepoRoot=Split-Path -Parent $PSScriptRoot
$Launcher=Join-Path $RepoRoot 'agentsLog/kwiscion/manual-final-prep/launcher.py'
$Python=Join-Path $env:APPDATA 'uv/python/cpython-3.11.11-windows-x86_64-none/python.exe'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Qualified Python is missing: $Python" }
if ($PSCmdlet.ParameterSetName -eq 'Resume') {
  & $Python -B -X utf8 $Launcher --resume $Resume
} else {
  if (-not $Smoke -and $RemoteMinutes -ne 55) { throw 'Final runs use exactly the frozen55-minute remote bound.' }
  $LaunchArgs=@('-B','-X','utf8',$Launcher,'--exam',$ExamPath,'--started-utc',$StartedUtc,'--remote-minutes',[string]$RemoteMinutes)
  if ($Smoke) { $LaunchArgs+='--smoke' }
  & $Python @LaunchArgs
}
exit $LASTEXITCODE
