# watch_refine.ps1 - live progress display for the Heir trait-refinement batch.
#
# The batch (tools/refine_personal_traits.py) buffers its stdout when redirected,
# so the log file stays empty while it runs. The real progress signal is the card
# modification time: a card is done when src/characters/<id>.json is written.
# This script polls the card mtimes + the backup count and repaints a progress
# table every N seconds.
#
# Usage:  powershell -File tools\watch_refine.ps1        (Ctrl+C to stop)

$cards   = 'D:\Workspace\Amphoreus\src\characters'
$backups = 'D:\Workspace\Amphoreus\.cache\refine-backups'
$log     = 'D:\Workspace\Amphoreus\.cache\refine-all.log'
$refresh = 10   # seconds between repaints
$staleHours = 6 # a card written within this window counts as refined

Write-Host "Watching the trait-refinement batch (Ctrl+C to stop)..." -ForegroundColor Gray
while ($true) {
    Clear-Host
    Write-Host "=== Amphoreus - Heir trait refinement progress ===" -ForegroundColor Cyan
    Write-Host ("Updated: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -ForegroundColor Gray
    Write-Host ""

    $now = Get-Date
    $all = @(Get-ChildItem $cards -Filter *.json | Sort-Object LastWriteTime -Descending)
    $done = @($all | Where-Object { $_.LastWriteTime -gt $now.AddHours(-$staleHours) })
    Write-Host ("Refined cards: {0}/{1}" -f $done.Count, $all.Count) -ForegroundColor Green

    Write-Host ""
    Write-Host "Cards (newest first):" -ForegroundColor Yellow
    $all | ForEach-Object {
        $mark = if ($_.LastWriteTime -gt $now.AddHours(-$staleHours)) { '[refined]' } else { '[     ]' }
        Write-Host ("  {0}  {1}  {2}" -f $mark, $_.LastWriteTime.ToString('MM-dd HH:mm'), $_.Name)
    }

    $nb = @(Get-ChildItem $backups -Filter *.json -ErrorAction SilentlyContinue).Count
    Write-Host ""
    Write-Host ("Backups in .cache\refine-backups: {0}/{1}" -f $nb, $all.Count) -ForegroundColor Yellow

    $ls = if (Test-Path $log) { (Get-Item $log).Length } else { 0 }
    Write-Host ("Log file bytes: {0}  (stdout is buffered — card mtimes above are the real signal)" -f $ls) -ForegroundColor DarkGray

    Start-Sleep -Seconds $refresh
}
