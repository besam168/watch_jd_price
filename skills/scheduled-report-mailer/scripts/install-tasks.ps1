param()

$ErrorActionPreference = 'Stop'

$skillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$configPath = Join-Path $skillRoot 'config\report-config.json'
$config = Get-Content $configPath -Raw | ConvertFrom-Json
$python = $config.python
$runner = Join-Path $skillRoot 'scripts\run-job.py'

$jobs = @(
  @{ Task='SRM_Collect_0800'; Time='08:00'; Args="--job comprehensive-morning --collect-only" },
  @{ Task='SRM_Send_0830'; Time='08:30'; Args="--job comprehensive-morning" },
  @{ Task='SRM_Collect_2030'; Time='20:30'; Args="--job comprehensive-evening --collect-only" },
  @{ Task='SRM_Send_2100'; Time='21:00'; Args="--job comprehensive-evening" }
)

foreach ($job in $jobs) {
  $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>$(Get-Date -Format s)</Date>
    <Author>$env:COMPUTERNAME\$env:USERNAME</Author>
    <URI>\$($job.Task)</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>$env:USERDOMAIN\$env:USERNAME</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>true</StopIfGoingOnBatteries>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-04-06T$($job.Time):00</StartBoundary>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>$python</Command>
      <Arguments>"$runner" $($job.Args)</Arguments>
      <WorkingDirectory>$skillRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
  $tmp = Join-Path $env:TEMP ($job.Task + '.xml')
  Set-Content -Path $tmp -Value $xml -Encoding Unicode
  schtasks.exe /Create /TN $job.Task /XML $tmp /F | Out-Host
}

Write-Host 'INSTALL_OK'
