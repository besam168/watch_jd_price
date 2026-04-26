param(
  [Parameter(Mandatory=$true)][ValidateSet('create','analyze')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Input,
  [string]$Output
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir 'bridge.py'

if ($Action -eq 'create') {
  if (-not $Output) { throw 'Output is required for create' }
  & python $py create --input $Input --output $Output
} else {
  & python $py analyze --input $Input
}
