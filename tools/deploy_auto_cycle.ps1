# deploy_auto_cycle.ps1 — watchdog that keeps the Amphoreus style auto-cycle
# deployed: restarts Ollama if it dies, relaunches the auto-cycle if it stops
# (unless it just completed), restarts the model runner on dangerously low RAM
# (hardens against the long-run OOM / 502 failure), and logs everything.
#
# Launch hidden:
#   Start-Process powershell -WindowStyle Hidden -ArgumentList '-ExecutionPolicy','Bypass','-File','D:\Workspace\Amphoreus\world_runtime\deploy_auto_cycle.ps1'
# Log: D:\Workspace\Amphoreus\world_runtime\watchdog.log

$ErrorActionPreference = 'SilentlyContinue'
$log = 'D:\Workspace\Amphoreus\world_runtime\watchdog.log'
$cycleCmd = 'D:\Workspace\Amphoreus\world_runtime\run_auto_cycle.cmd'
$cycleLog = 'D:\Workspace\Amphoreus\docs\AUTO-CYCLE-LOG.md'

function Log([string]$m) {
    try { Add-Content -Path $log -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) } catch {}
}
function OllamaUp {
    try { $null = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 6; return $true } catch { return $false }
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
    # 1. Ollama server up? (restart if down — fixes the 502 case)
    if (-not (OllamaUp)) {
        Log 'Ollama DOWN -> restarting server'
        Get-Process ollama,ollama_app,llama-server -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        & 'D:\Workspace\Amphoreus\tools\start_ollama.ps1' | Out-Null
        Start-Sleep -Seconds 12
        if (OllamaUp) { Log 'Ollama restarted OK' } else { Log 'Ollama restart FAILED (retrying next pass)' }
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
        $justFinished = $false
        if (Test-Path $cycleLog) {
            $ageMin = (New-TimeSpan -Start (Get-Item $cycleLog).LastWriteTime -End (Get-Date)).TotalMinutes
            $justFinished = $ageMin -lt 40
        }
        if ($justFinished) {
            Log 'auto-cycle finished recently — holding (not relaunching)'
        } else {
            Log 'auto-cycle NOT running -> relaunching'
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
