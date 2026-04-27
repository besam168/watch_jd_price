param()

$ErrorActionPreference = 'Stop'

$skillRoot = 'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner_v2'
$python = 'C:\Users\besam\AppData\Local\Programs\Python\Python312\python.exe'
$runner = Join-Path $skillRoot 'scripts\run_auto_092430.py'
$taskName = '沈万三_集合竞价狙击手V2_092430'

$xml = @"
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
      <StartBoundary>2026-04-28T09:24:30</StartBoundary>
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
      <Command>$python</Command>
      <Arguments>"$runner" --top-n 30</Arguments>
      <WorkingDirectory>$skillRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$tmp = Join-Path $env:TEMP 'auction_sniper_v2_092430_task.xml'
Set-Content -Path $tmp -Value $xml -Encoding Unicode
schtasks.exe /Create /TN $taskName /XML $tmp /F | Out-Host
Write-Host 'TASK_INSTALLED_OK'
