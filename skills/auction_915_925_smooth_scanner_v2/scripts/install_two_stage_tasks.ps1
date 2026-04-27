param()

$ErrorActionPreference = 'Stop'

$skillRoot = 'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner_v2'
$python = 'python'
$captureRunner = Join-Path $skillRoot 'scripts\run_capture_0915.py'
$judgeRunner = Join-Path $skillRoot 'scripts\run_judgement_092430.py'
$taskCapture = '沈万三_集合竞价狙击手V2_0915_Capture'
$taskJudge = '沈万三_集合竞价狙击手V2_092430_Judgement'

function New-TaskXml([string]$taskName, [string]$startBoundary, [string]$command, [string]$arguments, [string]$workingDirectory) {
@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>$(Get-Date -Format s)</Date>
    <Author>$env:COMPUTERNAME\$env:USERNAME</Author>
    <URI>\$taskName</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$startBoundary</StartBoundary>
      <ScheduleByWeek>
        <WeeksInterval>1</WeeksInterval>
        <DaysOfWeek>
          <Monday />
          <Tuesday />
          <Wednesday />
          <Thursday />
          <Friday />
        </DaysOfWeek>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>$command</Command>
      <Arguments>$arguments</Arguments>
      <WorkingDirectory>$workingDirectory</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
}

$tmpCapture = Join-Path $env:TEMP 'auction_sniper_v2_0915_capture.xml'
$tmpJudge = Join-Path $env:TEMP 'auction_sniper_v2_092430_judgement.xml'
Set-Content -Path $tmpCapture -Value (New-TaskXml $taskCapture '2026-04-28T09:15:00' $python ('"' + $captureRunner + '" --limit 0 --rounds 115 --interval-seconds 5') $skillRoot) -Encoding Unicode
Set-Content -Path $tmpJudge -Value (New-TaskXml $taskJudge '2026-04-28T09:24:30' $python ('"' + $judgeRunner + '" --top-n 30') $skillRoot) -Encoding Unicode
schtasks.exe /Create /TN $taskCapture /XML $tmpCapture /F | Out-Host
schtasks.exe /Create /TN $taskJudge /XML $tmpJudge /F | Out-Host
Write-Host 'TASKS_INSTALLED_OK'
