# Start the little Amphoreus and keep it running.
#   powershell -ExecutionPolicy Bypass -File tools\start_world.ps1
# The in-world calendar follows GMT+8 (src/world/sanctuary_clock.py); a day takes
# 900 s of real time. --catch-up first generates the days the world missed while
# it rested, so the lore has no hole in it, then the daemon keeps running.
#   --stop     ask it to stop (marks the rest so the next start can catch up)
#   --status   print the clock, chronicle size and visitor state
param([switch]$Stop, [switch]$Status, [int]$Interval = 900)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$py = 'D:\Workspace\.venv\Scripts\python.exe'
if ($Stop)   { & $py -m src.world.world_engine --stop;   exit $LASTEXITCODE }
if ($Status) { & $py -m src.world.world_engine --status; exit $LASTEXITCODE }
New-Item -ItemType Directory -Force -Path world_runtime | Out-Null
$log = 'world_runtime\engine_run.log'
"=== engine start $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (GMT+8) ===" | Out-File $log -Append -Encoding UTF8
& $py -m src.world.world_engine --interval $Interval --catch-up 2>&1 | Tee-Object -FilePath $log -Append
