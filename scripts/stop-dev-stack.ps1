param(
  [switch]$IncludeMySql,
  [switch]$IncludeNginx = $true,
  [string]$MySqlServiceName = 'MySQL80'
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root '.runtime'
$logDir = Join-Path $runtimeDir 'logs'
$pidDir = Join-Path $runtimeDir 'pids'
$nginxServiceName = 'nginx'
$nginxRoot = Join-Path $root 'nginx-1.19.3'
$nginxExe = Join-Path $nginxRoot 'nginx.exe'
$nginxConf = Join-Path $nginxRoot 'conf\nginx.conf'
$backendPort = 8081
$frontendPort = 5173
$detectorPort = 19090

function Write-Step {
  param([string]$Message)
  Write-Host "[iot-stack] $Message"
}

function Get-LocalNginxProcesses {
  if (-not (Test-Path $nginxExe)) {
    return @()
  }

  return @(Get-Process nginx -ErrorAction SilentlyContinue | Where-Object {
    $_.Path -and $_.Path -ieq $nginxExe
  })
}

function Stop-LocalNginx {
  $localNginx = Get-LocalNginxProcesses
  if ($localNginx.Count -eq 0) {
    Write-Step 'Local Nginx is already stopped.'
    return
  }

  try {
    & $nginxExe -p $nginxRoot -c conf/nginx.conf -s quit | Out-Null
    Write-Step 'Local Nginx stop signal sent.'
  } catch {
    Write-Step 'Local Nginx quit signal failed, forcing shutdown.'
  }

  $deadline = (Get-Date).AddSeconds(10)
  do {
    Start-Sleep -Milliseconds 500
    $localNginx = Get-LocalNginxProcesses
  } while ($localNginx.Count -gt 0 -and (Get-Date) -lt $deadline)

  if ($localNginx.Count -gt 0) {
    $localNginx | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Step 'Forced shutdown of local Nginx processes.'
  }
}

function Stop-ManagedProcess {
  param(
    [string]$Name,
    [string]$PidFileName
  )

  $pidFile = Join-Path $pidDir $PidFileName
  if (-not (Test-Path $pidFile)) {
    Write-Step "$Name PID file not found, skipping."
    return
  }

  $rawPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
  if (-not $rawPid) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Step "$Name PID file was empty, removed."
    return
  }

  $process = Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue
  if ($null -eq $process) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    Write-Step "$Name process $rawPid is already stopped."
    return
  }

  Stop-ProcessTree -ProcessId $process.Id -Name $Name
  Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ProcessTree {
  param(
    [int]$ProcessId,
    [string]$Name
  )

  $allProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
  $idsToStop = New-Object System.Collections.Generic.List[int]

  function Add-ChildProcessIds {
    param([int]$ParentId)

    foreach ($child in $allProcesses | Where-Object { $_.ParentProcessId -eq $ParentId }) {
      Add-ChildProcessIds -ParentId ([int]$child.ProcessId)
      $idsToStop.Add([int]$child.ProcessId)
    }
  }

  Add-ChildProcessIds -ParentId $ProcessId
  $idsToStop.Add($ProcessId)

  foreach ($id in ($idsToStop | Select-Object -Unique)) {
    try {
      Stop-Process -Id $id -Force -ErrorAction Stop
      Write-Step "$Name stopped process PID $id."
    } catch {
      Write-Step "$Name process PID $id was already stopped or could not be stopped."
    }
  }
}

function Stop-ProcessOnPort {
  param(
    [string]$Name,
    [int]$Port
  )

  $connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
  if ($connections.Count -eq 0) {
    Write-Step "$Name port $Port is clear."
    return
  }

  foreach ($connection in $connections) {
    $ownerPid = [int]$connection.OwningProcess
    if ($ownerPid -le 0) {
      continue
    }
    Stop-ProcessTree -ProcessId $ownerPid -Name "$Name port $Port owner"
  }
}

function Stop-OrphanedProjectProcesses {
  $escapedRoot = [regex]::Escape($root)
  $patterns = @(
    "$escapedRoot.*end_part.*spring-boot:run",
    "$escapedRoot.*end_part.*EndPartApplication",
    "$escapedRoot.*frontend.*vite",
    "$escapedRoot.*video_stream.*yolo_inference_windows.py"
  )

  $currentPid = $PID
  $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $commandLine = [string]$_.CommandLine
    $_.ProcessId -ne $currentPid -and ($patterns | Where-Object { $commandLine -match $_ })
  })

  if ($processes.Count -eq 0) {
    Write-Step 'No orphaned project processes found by command line.'
    return
  }

  foreach ($process in $processes) {
    Stop-ProcessTree -ProcessId ([int]$process.ProcessId) -Name 'orphaned project process'
  }
}

Write-Step 'Stopping frontend and backend processes...'
Stop-ManagedProcess -Name 'frontend' -PidFileName 'frontend.pid'
Stop-ManagedProcess -Name 'backend' -PidFileName 'backend.pid'
Stop-ManagedProcess -Name 'detector-supervisor' -PidFileName 'detector-supervisor.pid'

Write-Step 'Checking ports for orphaned project processes...'
Stop-ProcessOnPort -Name 'Backend' -Port $backendPort
Stop-ProcessOnPort -Name 'Frontend' -Port $frontendPort
Stop-ProcessOnPort -Name 'Detector supervisor' -Port $detectorPort
Stop-OrphanedProjectProcesses

if ($IncludeNginx) {
  $service = Get-Service -Name $nginxServiceName -ErrorAction SilentlyContinue
  if ($null -ne $service) {
    if ($service.Status -eq 'Running') {
      try {
        Stop-Service -Name $nginxServiceName -ErrorAction Stop
        Write-Step "Nginx service $nginxServiceName stopped."
      } catch {
        Write-Step "Nginx service $nginxServiceName could not be stopped from this shell. Try an elevated terminal if you need to stop it."
      }
    } else {
      Write-Step "Nginx service $nginxServiceName is already stopped."
    }
  } elseif (-not ((Test-Path $nginxExe) -and (Test-Path $nginxConf))) {
    Write-Step 'Local Nginx binary not found, skipping.'
  }

  if ((Test-Path $nginxExe) -and (Test-Path $nginxConf)) {
    Stop-LocalNginx
  }
} else {
  Write-Step 'Local Nginx left running.'
}

if ($IncludeMySql) {
  $service = Get-Service -Name $MySqlServiceName -ErrorAction SilentlyContinue
  if ($null -eq $service) {
    Write-Step "MySQL service $MySqlServiceName was not found."
  } elseif ($service.Status -eq 'Running') {
    Stop-Service -Name $MySqlServiceName
    Write-Step "MySQL service $MySqlServiceName stopped."
  } else {
    Write-Step "MySQL service $MySqlServiceName is already stopped."
  }
} else {
  Write-Step 'MySQL service left running.'
}

if (Test-Path $logDir) {
  Write-Step "Logs remain available at $logDir"
}
