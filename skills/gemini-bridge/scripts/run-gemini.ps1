param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$ApiKey = "",
    [string]$Model = "gemini-2.5-flash",
    [string]$BaseUrl = "https://generativelanguage.googleapis.com/v1beta",
    [string]$OutputFile = "",
    [switch]$Json,
    [switch]$OpenAICompat,
    [int]$MaxRetries = 2,
    [int]$RetryDelaySeconds = 2
)

$ErrorActionPreference = 'Stop'

function Get-StatusCodeFromException {
    param([Parameter(Mandatory=$true)]$Exception)

    if ($null -ne $Exception.Response -and $null -ne $Exception.Response.StatusCode) {
        return [int]$Exception.Response.StatusCode
    }

    if ($Exception.Exception -and $Exception.Exception.Response -and $Exception.Exception.Response.StatusCode) {
        return [int]$Exception.Exception.Response.StatusCode
    }

    return $null
}

function Get-ErrorCategory {
    param([int]$StatusCode)

    switch ($StatusCode) {
        400 { return 'bad_request' }
        401 { return 'unauthorized' }
        403 { return 'forbidden' }
        404 { return 'not_found' }
        408 { return 'timeout' }
        429 { return 'rate_limited' }
        500 { return 'server_error' }
        502 { return 'bad_gateway' }
        503 { return 'service_unavailable' }
        504 { return 'gateway_timeout' }
        default {
            if ($StatusCode -ge 500) { return 'server_error' }
            if ($StatusCode -ge 400) { return 'http_error' }
            return 'unknown_error'
        }
    }
}

function Get-ErrorDetail {
    param([Parameter(Mandatory=$true)]$Exception)

    if ($Exception.ErrorDetails -and $Exception.ErrorDetails.Message) {
        return $Exception.ErrorDetails.Message
    }

    if ($Exception.Exception -and $Exception.Exception.Message) {
        return $Exception.Exception.Message
    }

    return ($Exception | Out-String).Trim()
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $ApiKey = [Environment]::GetEnvironmentVariable('GOOGLE_API_KEY', 'Process')
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $ApiKey = [Environment]::GetEnvironmentVariable('GOOGLE_API_KEY', 'User')
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw 'GOOGLE_API_KEY is not set and -ApiKey was not provided.'
}

if ($OpenAICompat) {
    $trimmedBaseUrl = $BaseUrl.TrimEnd('/')
    if ($trimmedBaseUrl.EndsWith('/openai')) {
        $uri = "$trimmedBaseUrl/chat/completions"
    } else {
        $uri = "$trimmedBaseUrl/openai/chat/completions"
    }
    $headers = @{ Authorization = "Bearer $ApiKey" }
    $bodyObj = @{
        model = $Model
        messages = @(
            @{ role = 'user'; content = $Prompt }
        )
    }
} else {
    $normalizedModel = $Model
    if ($normalizedModel.StartsWith('models/')) {
        $normalizedModel = $normalizedModel.Substring(7)
    }
    $uri = "$($BaseUrl.TrimEnd('/'))/models/$normalizedModel`:generateContent"
    $headers = @{ 'x-goog-api-key' = $ApiKey }
    $bodyObj = @{
        contents = @(
            @{
                parts = @(
                    @{ text = $Prompt }
                )
            }
        )
    }
}

$body = $bodyObj | ConvertTo-Json -Depth 10
$attempt = 0

while ($true) {
    try {
        $attempt++
        $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -ContentType 'application/json' -Body $body
        break
    } catch {
        $statusCode = Get-StatusCodeFromException -Exception $_
        $category = Get-ErrorCategory -StatusCode $statusCode
        $detail = Get-ErrorDetail -Exception $_
        $canRetry = ($attempt -le $MaxRetries) -and ($statusCode -in @(408, 429, 500, 502, 503, 504))

        if ($canRetry) {
            Start-Sleep -Seconds $RetryDelaySeconds
            continue
        }

        if ($Json) {
            [pscustomobject]@{
                ok = $false
                model = $Model
                baseUrl = $BaseUrl
                openAICompat = [bool]$OpenAICompat
                outputFile = $OutputFile
                error = [pscustomobject]@{
                    statusCode = $statusCode
                    category = $category
                    attempt = $attempt
                    message = $detail
                }
            } | ConvertTo-Json -Depth 8
            exit 1
        } else {
            $statusText = if ($null -ne $statusCode) { "HTTP $statusCode" } else { 'HTTP unknown' }
            throw "$statusText [$category] $detail"
        }
    }
}

if ($OpenAICompat) {
    $text = $response.choices[0].message.content
} else {
    $text = $response.candidates[0].content.parts[0].text
}

if (-not [string]::IsNullOrWhiteSpace($OutputFile)) {
    $parent = Split-Path -Parent $OutputFile
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $OutputFile -Value $text -Encoding UTF8
}

if ($Json) {
    [pscustomobject]@{
        ok = $true
        model = $Model
        baseUrl = $BaseUrl
        openAICompat = [bool]$OpenAICompat
        outputFile = $OutputFile
        text = $text
    } | ConvertTo-Json -Depth 6
} else {
    Write-Output $text
}
