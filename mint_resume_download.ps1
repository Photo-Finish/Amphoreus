# mint_resume_download.ps1 — downloader for CDNs that hand out expiring signed
# URLs. Each attempt:
#   1. mints a FRESH signed URL for Range: bytes=<current>- by asking the resolve
#      URL (github.com/hf-mirror) for the file at that range,
#   2. downloads with `curl -C -` (which sends the matching Range header and
#      appends), accumulating progress across attempts.
#
# Usage:
#   powershell -File mint_resume_download.ps1 -ResolveUrl <url> -OutFile <path> [-ExpectedBytes <n>]

param(
    [Parameter(Mandatory = $true)][string]$ResolveUrl,
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

    # 1. Mint a fresh signed URL for Range: bytes=$size-
    $range = "$size-"
    $u = curl.exe -s -o NUL -w "%{url_effective}" -L --max-redirs 5 -r $range --http1.1 --connect-timeout 20 --max-time 90 $ResolveUrl 2>$null
    if (-not $u) {
        Start-Sleep -Seconds 10
        continue
    }

    # 2. Download (resume) from the minted URL. -C - sends Range: bytes=$size-
    #    and appends to the file.
    curl.exe -C - --http1.1 --connect-timeout 20 --max-time 200 --retry 5 --retry-all-errors --retry-delay 3 -o $OutFile $u 2>&1 | Out-Null

    Start-Sleep -Seconds 8
}
