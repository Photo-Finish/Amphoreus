# deploy_auto_cycle.ps1 — watchdog that keeps the Amphoreus style auto-cycle
# deployed: restarts Ollama if it dies, relaunches the auto-cycle if it stops
# (unless it just completed), restarts the model runner on dangerously low RAM
# (hardens against the long-run OOM / 502 failure), and logs everything.
#
# Launch hidden:
#   Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy','Bypass','-File','tools\deploy_auto_cycle.ps1'
# Log: <repo>\world_runtime\watchdog.log

$ErrorActionPreference = 'SilentlyContinue'
# Portable paths — derived from this script's location so the watchdog works
# from any checkout of the repo.
$root = Split-Path $PSScriptRoot -Parent
$log = Join-Path $root 'world_runtime\watchdog.log'
$cycleCmd = Join-Path $root 'world_runtime\run_auto_cycle.cmd'
$cycleLog = Join-Path $root 'docs\AUTO-CYCLE-LOG.md'

function Log([string]$m) {
    try { Add-Content -Path $log -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) } catch {}
}
function OllamaHealthy {
    # Port answering AND the Heir model actually visible. A bare `ollama serve`
    # started without OLLAMA_MODELS answers /api/version but serves NO models
    # -> every call 404s while the port looks fine (the 2026-08-12 trap).
    try {
        $null = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 6
        $tags = (Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 8).Content
        if ($tags -match 'gemma3:27b') { return $true }
        Log 'server up but gemma3:27b NOT visible (wrong/empty models dir) -> will restart'
        return $false
    } catch { return $false }
}
# WMI (Get-CimInstance) can HANG on this machine (it did on 2026-08-13 — the
# watchdog stalled for ~50 min and never noticed the dead server). Run every
# machine-state read in a throwaway job with a hard timeout so a hang can
# never freeze the watchdog again; on timeout treat as 'unknown/not running'.
function Invoke-StateCheck([scriptblock]$sb, [int]$timeoutSec = 20) {
    $job = Start-Job -ScriptBlock $sb -ErrorAction SilentlyContinue
    if ($null -eq $job) { return $null }
    if (-not (Wait-Job -Job $job -Timeout $timeoutSec)) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        return $null
    }
    $res = Receive-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    return $res
}

Log '=== watchdog started ==='
while ($true) {
    # 1. Ollama truly healthy? (port + gemma3:27b visible; restart if broken)
    if (-not (OllamaHealthy)) {
        Log 'Ollama DOWN/broken -> restarting server'
        Get-Process ollama,ollama_app,llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        & (Join-Path $root 'tools\start_ollama.ps1') | Out-Null
        Start-Sleep -Seconds 12
        if (OllamaHealthy) { Log 'Ollama restarted OK' } else { Log 'Ollama restart FAILED (retrying next pass)' }
    }

    # 2. Auto-cycle alive? (relaunch unless it just completed). Runs in a
    #    timed job so a hung WMI call cannot stall the loop.
    $state = Invoke-StateCheck {
        $ac = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
               Where-Object { $_.CommandLine -match 'auto_cycle' }).Count
        $ram = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
        return @{ ac = $ac; ram = $ram }
    } 25
    if ($null -eq $state) { $state = @{ ac = 0; ram = 99 } }  # timed out: assume not running, skip RAM action

    if ($state.ac -eq 0) {
        # RESUME POLICY: hold only when the run just SUCCEEDED; a FAILED or
        # crashed run resumes after a short 5-min settle so the loop keeps
        # cycling until everyone passes.
        $resume = $true
        if (Test-Path $cycleLog) {
            $ageMin = (New-TimeSpan -Start (Get-Item $cycleLog).LastWriteTime -End (Get-Date)).TotalMinutes
            $txt = Get-Content $cycleLog -Raw -ErrorAction SilentlyContinue
            $success = ($txt -match 'FINAL OUTCOME: SUCCESS')
            if ($success -and $ageMin -lt 40) {
                $resume = $false
                Log 'auto-cycle SUCCEEDED recently — holding (not relaunching)'
            } elseif ($ageMin -lt 5) {
                $resume = $false   # just ended/wrote — give it a moment to settle
            }
        }
        if ($resume) {
            Log 'auto-cycle not running -> relaunching'
            Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $cycleCmd
            Start-Sleep -Seconds 5
        }
    }

    # 3. Dangerously low RAM? (restart the model runner to reclaim memory)
    if ($state.ram -lt 1.5) {
        Log ("LOW RAM {0:N1} GB -> restarting llama runner" -f $state.ram)
        Get-Process llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 8
    }

    Start-Sleep -Seconds 45
}
