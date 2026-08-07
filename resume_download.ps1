# resume_download.ps1 — robust resumable downloader for slow/throttled networks.
#
# Loops `curl -L -C -` against a stable "resolve" URL. Each attempt follows the
# redirect to a freshly-signed CDN URL (so expiry is never fatal) and resumes
# from the current file size, accumulating progress until the expected size is
# reached (or forever, if no expected size is given).
#
# Usage:
#   powershell -File D:\models\resume_download.ps1 -Url <resolve-url> -OutFile <path> [-ExpectedBytes <n>]
#
# NOTE: the output file is pre-created so curl -C - always sends a Range header
# (some CDNs reject requests without one).

param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [long]$ExpectedBytes = 0
)

$ErrorActionPreference = 'Continue'
if (-not (Test-Path $OutFile)) {
    New-Item -ItemType File -Path $OutFile -Force | Out-Null
}

$attempt = 0
while ($true) {
    $attempt++
    $size = (Get-Item $OutFile).Length
    $mb = [math]::Round($size / 1MB, 1)
    $log = "[$(Get-Date -Format 'HH:mm:ss')] attempt $attempt — $mb MB"
    Write-Host $log
    Add-Content -Path "D:\models\resume_log.txt" -Value $log -Encoding utf8

    if ($ExpectedBytes -gt 0 -and $size -ge $ExpectedBytes) {
        $done = "COMPLETE: $OutFile ($size bytes)"
        Write-Host $done
        Add-Content -Path "D:\models\resume_log.txt" -Value $done -Encoding utf8
        break
    }

    # -C - resumes; --max-time caps each attempt so a stalled transfer moves on;
    # --http1.1 avoids HTTP/2 reset issues seen on this network.
    curl.exe -L -C - --http1.1 --connect-timeout 20 --max-time 240 --retry 5 --retry-all-errors --retry-delay 3 -o $OutFile $Url 2>&1 | Out-Null

    Start-Sleep -Seconds 10
}
