param(
  [Parameter(Position = 0)]
  [string]$Text = '收到。回调文本链路验证成功。',

  [string]$Url = 'http://127.0.0.1:57881/callback/text',

  [string]$Source = 'demo-callback',

  [string]$SessionId = ''
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

if (-not $SessionId -or [string]::IsNullOrWhiteSpace($SessionId)) {
  $SessionId = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss')
}

$body = @{
  query = $Text
  source = $Source
  session_id = $SessionId
  payload = @{
    query = $Text
  }
} | ConvertTo-Json -Depth 5 -Compress

$response = Invoke-RestMethod -Uri $Url -Method Post -ContentType 'application/json; charset=utf-8' -Body $body
$response | ConvertTo-Json -Depth 10