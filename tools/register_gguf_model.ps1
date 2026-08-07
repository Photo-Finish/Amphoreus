# Manually register the qwen2.5:14b-instruct model (config blob + manifest),
# bypassing `ollama create` (which needs ~18GB peak for its quantize temp).
$ErrorActionPreference = 'Stop'
$env:OLLAMA_MODELS = 'D:\Workspace\Amphoreus\models\ollama'
$modelsRoot = 'D:\Workspace\Amphoreus\models\ollama'

$modelDigest = 'sha256:6b53d1833376cb4b6bf31e1c6ac4ca59bb153569decbbf1f205701046b5b9a38'
$modelSize = 8988110272

# 1. Config blob
$configObj = [ordered]@{
    model_format     = 'gguf'
    model_family     = 'qwen2.5'
    model_families   = @('qwen2.5')
    model_type       = '14.8B'
    file_type        = 'Q4_K_M'
    architecture     = 'amd64'
    os               = 'linux'
    rootfs           = [ordered]@{
        type      = 'layers'
        diff_ids  = @($modelDigest)
    }
}
$configJson = $configObj | ConvertTo-Json -Depth 10 -Compress
$sha = [System.Security.Cryptography.SHA256]::Create()
$configHash = [System.BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($configJson))).Replace('-','').ToLower()
$configBlob = Join-Path $modelsRoot "blobs\sha256-$configHash"
if (-not (Test-Path $configBlob)) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($configBlob, $configJson, $utf8NoBom)
}
Write-Host "config blob: sha256-$configHash ($($configJson.Length) bytes)"

# 2. Manifest
$manifest = [ordered]@{
    schemaVersion = 2
    mediaType     = 'application/vnd.docker.distribution.manifest.v2+json'
    config        = [ordered]@{
        mediaType = 'application/vnd.docker.container.image.v1+json'
        digest    = "sha256:$configHash"
        size      = $configJson.Length
    }
    layers        = @([ordered]@{
        mediaType = 'application/vnd.ollama.image.model'
        digest    = $modelDigest
        size      = $modelSize
    })
}
$manifestJson = $manifest | ConvertTo-Json -Depth 10 -Compress
$manifestPath = Join-Path $modelsRoot 'manifests\registry.ollama.ai\library\qwen2.5\14b-instruct'
New-Item -ItemType Directory -Path (Split-Path $manifestPath) -Force | Out-Null
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, $utf8NoBom)
Write-Host "manifest written: $manifestPath"
Write-Host "--- manifest ---"
Get-Content $manifestPath -Raw
