# attach_mmproj.ps1 — attach a projector (mmproj) to an Ollama model.
#
# This Ollama build does NOT auto-bundle `mmproj-*.gguf` when creating from a
# GGUF, so the model ends up without a projector layer ("audio/vision input is
# not supported ... provide the mmproj"). This script copies the projector into
# the model store and adds it as a layer in the manifest (written WITHOUT a
# UTF-8 BOM — a BOM breaks the server's JSON parser).
#
# Usage:
#   powershell -File tools\attach_mmproj.ps1 -ModelName qwen2.5vl:7b `
#       -MmprojPath models\gguf\vl\mmproj-model-f16.gguf
param(
    [Parameter(Mandatory = $true)][string]$ModelName,
    [Parameter(Mandatory = $true)][string]$MmprojPath
)
$ErrorActionPreference = 'Stop'
$env:OLLAMA_MODELS = 'D:\Workspace\Amphoreus\models\ollama'
$modelsRoot = 'D:\Workspace\Amphoreus\models\ollama'

$nameParts = $ModelName.Split(':')
$repo = $nameParts[0]
$tag = if ($nameParts.Count -gt 1) { $nameParts[1] } else { 'latest' }
$manifestPath = Join-Path $modelsRoot "manifests\registry.ollama.ai\library\$repo\$tag"
if (-not (Test-Path $manifestPath)) { Write-Error "manifest not found: $manifestPath" }

$hash = (Get-FileHash $MmprojPath -Algorithm SHA256).Hash.ToLower()
$blobPath = Join-Path $modelsRoot "blobs\sha256-$hash"
$size = (Get-Item $MmprojPath).Length

if (-not (Test-Path $blobPath)) {
    Copy-Item $MmprojPath $blobPath
    Write-Host "copied mmproj -> blobs\sha256-$hash ($size bytes)"
} else {
    Write-Host "blob already exists: sha256-$hash"
}

$j = Get-Content $manifestPath -Raw | ConvertFrom-Json
$j.layers = @($j.layers | Where-Object { $_.mediaType -ne 'application/vnd.ollama.image.projector' })
$projLayer = [ordered]@{
    mediaType = 'application/vnd.ollama.image.projector'
    digest    = "sha256:$hash"
    size      = $size
}
$j.layers += [pscustomobject]$projLayer
$json = $j | ConvertTo-Json -Depth 10 -Compress
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, $json, $utf8NoBom)
Write-Host "manifest updated for $ModelName with projector sha256:$hash"
(Get-Content $manifestPath -Raw | ConvertFrom-Json).layers |
    ForEach-Object { Write-Host "  $($_.mediaType) $($_.digest) $($_.size)" }
