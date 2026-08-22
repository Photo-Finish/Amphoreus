# Build AmphoreusSanctuary.exe — thin desktop window over Streamlit.
# Does NOT replace launch_sanctuary.cmd (browser tab remains the original UI).
#
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File tools\build_desktop_exe.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $Root "src\ui_app.py"))) {
    $Root = $PSScriptRoot
}
Set-Location $Root

$PyCandidates = @(
    (Join-Path $Root ".venv\Scripts\python.exe"),
    (Join-Path $Root "..\.venv\Scripts\python.exe"),
    "D:\Workspace\.venv\Scripts\python.exe"
)
$Python = $null
foreach ($c in $PyCandidates) {
    if (Test-Path $c) { $Python = $c; break }
}
if (-not $Python) {
    Write-Error "No venv python found. Create .venv and install requirements + pywebview + pyinstaller."
}

Write-Host "Python: $Python"
Write-Host "Root:   $Root"

& $Python -m pip install -q --upgrade pywebview pyinstaller | Out-Host

$OutDir = Join-Path $Root "dist"
$WorkDir = Join-Path $Root "world_runtime\pyinstaller_desktop"
New-Item -ItemType Directory -Force -Path $OutDir, $WorkDir | Out-Null

$Icon = ""
$IcoCand = @(
    (Join-Path $Root "assets\amphoreus.ico"),
    (Join-Path $Root "assets\heirs\phainon.png")
)
# Optional: bake a simple .ico from an heir portrait if Pillow is present.
$GenIco = Join-Path $WorkDir "amphoreus_desktop.ico"
try {
    & $Python -c @"
from pathlib import Path
from PIL import Image
root = Path(r'$Root')
src = root / 'assets' / 'heirs' / 'phainon.png'
if not src.exists():
    src = next((root / 'assets' / 'heirs').glob('*.png'), None)
out = Path(r'$GenIco')
if src and Path(src).exists():
    im = Image.open(src).convert('RGBA')
    im.thumbnail((256, 256))
    im.save(out, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print('ico', out)
else:
    print('no-icon')
"@
    if (Test-Path $GenIco) { $Icon = $GenIco }
} catch {
    Write-Host "Icon generation skipped: $_"
}

$Script = Join-Path $Root "tools\desktop_sanctuary.py"
$Args = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "AmphoreusSanctuary",
    "--distpath", $OutDir,
    "--workpath", $WorkDir,
    "--specpath", $WorkDir
)
if ($Icon -and (Test-Path $Icon)) {
    $Args += @("--icon", $Icon)
}
# pywebview needs its platforms collected on Windows.
$Args += @(
    "--collect-all", "webview",
    "--hidden-import", "webview",
    "--hidden-import", "webview.platforms.edgechromium",
    $Script
)

Write-Host "Building AmphoreusSanctuary.exe ..."
& $Python @Args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Exe = Join-Path $OutDir "AmphoreusSanctuary.exe"
if (-not (Test-Path $Exe)) {
    Write-Error "Build finished but exe missing: $Exe"
}

# Convenience copy at repo root (easy double-click next to launch_sanctuary.cmd).
Copy-Item -Force $Exe (Join-Path $Root "AmphoreusSanctuary.exe")
Write-Host ""
Write-Host "OK:"
Write-Host "  $Exe"
Write-Host "  $(Join-Path $Root 'AmphoreusSanctuary.exe')"
Write-Host ""
Write-Host "Browser UI unchanged: launch_sanctuary.cmd"
Write-Host "Desktop window:       AmphoreusSanctuary.exe"
