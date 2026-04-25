param(
  [string]$MySqlServiceName = 'MySQL80',
  [int]$MySqlPort = 3306,
  [switch]$EnableNginx = $true,
  [int]$NginxHttpPort = 8080,
  [int]$NginxRtmpPort = 1935,
  [int]$BackendPort = 8081,
  [int]$FrontendPort = 5173,
  [int]$TimeoutSeconds = 180
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
$detectorWorkdir = Join-Path $root 'end_part\video_stream'
$backendMvnw = Join-Path $root 'end_part\mvnw.cmd'
$frontendVite = Join-Path $root 'frontend\node_modules\.bin\vite.cmd'

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $pidDir | Out-Null

function Write-Step {
  param([string]$Message)
  Write-Host "[iot-stack] $Message"
}

function Test-PortOpen {
  param(
    [string]$TargetHost = '127.0.0.1',
    [int]$Port
  )

  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect($TargetHost, $Port, $null, $null)
    $ok = $async.AsyncWaitHandle.WaitOne(1000, $false)
    if (-not $ok) {
      $client.Close()
      return $false
    }

    $client.EndConnect($async)
    $client.Close()
    return $true
  } catch {
    return $false
  }
}

function Wait-PortOpen {
  param(
    [string]$Name,
    [int]$Port,
    [int]$Timeout = 60
  )

  $deadline = (Get-Date).AddSeconds($Timeout)
  while ((Get-Date) -lt $deadline) {
    if (Test-PortOpen -Port $Port) {
      Write-Step "$Name is listening on port $Port."
      return $true
    }
    Start-Sleep -Milliseconds 750
  }

  throw "$Name did not open port $Port within $Timeout seconds."
}

function Wait-HttpReady {
  param(
    [string]$Name,
    [string]$Url,
    [int[]]$AcceptedStatusCodes = @(200),
    [int]$Timeout = 60
  )

  $deadline = (Get-Date).AddSeconds($Timeout)
  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing
      if ($AcceptedStatusCodes -contains [int]$response.StatusCode) {
        Write-Step "$Name health check passed at $Url ($($response.StatusCode))."
        return $true
      }
    } catch {
      $statusCode = 0
      if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $statusCode = [int]$_.Exception.Response.StatusCode
      }
      if ($AcceptedStatusCodes -contains $statusCode) {
        Write-Step "$Name health check passed at $Url ($statusCode)."
        return $true
      }
    }

    Start-Sleep -Milliseconds 1000
  }

  throw "$Name did not become healthy at $Url within $Timeout seconds."
}

function Start-ManagedProcess {
  param(
    [string]$Name,
    [string]$FilePath,
    [string[]]$ArgumentList = @(),
    [string]$WorkingDirectory,
    [string]$PidFileName
  )

  $stdout = Join-Path $logDir "$Name.out.log"
  $stderr = Join-Path $logDir "$Name.err.log"
  $pidFile = Join-Path $pidDir $PidFileName
  Set-Content -Path $stdout -Value ''
  Set-Content -Path $stderr -Value ''

  Write-Step "Starting $Name..."
  $process = Start-Process -FilePath $FilePath `
    -ArgumentList $ArgumentList `
    -WorkingDirectory $WorkingDirectory `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden `
    -PassThru

  Set-Content -Path $pidFile -Value $process.Id
  Write-Step "$Name started with PID $($process.Id). Logs: $stdout"
}

function Get-DetectorPython {
  $candidates = @(
    (Join-Path $root 'end_part\.venv\Scripts\python.exe'),
    'python'
  )

  foreach ($candidate in $candidates) {
    $exists = $candidate -eq 'python' -or (Test-Path $candidate)
    if (-not $exists) {
      continue
    }

    try {
      & $candidate -c "import cv2; import paho.mqtt.client; from ultralytics import YOLO" *> $null
      return $candidate
    } catch {
      continue
    }
  }

  throw 'No suitable Python interpreter found for detector supervisor. Need cv2, paho-mqtt, ultralytics.'
}

function Start-LocalNginx {
  $service = Get-Service -Name $nginxServiceName -ErrorAction SilentlyContinue
  if ($null -ne $service) {
    if ($service.Status -ne 'Running') {
      Write-Step "Starting Nginx service: $nginxServiceName"
      try {
        Start-Service -Name $nginxServiceName -ErrorAction Stop
        return
      } catch {
        Write-Step 'Nginx service start failed, falling back to local nginx.exe.'
      }
    } else {
      Write-Step "Nginx service already running: $nginxServiceName"
      return
    }
  }

  if (-not (Test-Path $nginxExe) -or -not (Test-Path $nginxConf)) {
    Write-Step 'Local Nginx binary or config not found, skipping Nginx startup.'
    return
  }

  if ((Test-PortOpen -Port $NginxHttpPort) -and (Test-PortOpen -Port $NginxRtmpPort)) {
    Write-Step "Nginx already appears to be running on ports $NginxHttpPort/$NginxRtmpPort."
    return
  }

  Write-Step 'Starting local Nginx for RTMP/HTTP-FLV...'
  & $nginxExe -p $nginxRoot -c conf/nginx.conf
}

Write-Step 'Ensuring MySQL is running...'
& (Join-Path $PSScriptRoot 'ensure-mysql.ps1') -ServiceName $MySqlServiceName -Port $MySqlPort -TimeoutSeconds 30

if ($EnableNginx) {
  Start-LocalNginx
}

if (Test-PortOpen -Port $BackendPort) {
  Write-Step "Backend already appears to be running on port $BackendPort."
} else {
  Start-ManagedProcess `
    -Name 'backend' `
    -FilePath $backendMvnw `
    -ArgumentList @('-q', '-DskipTests', '-Dspring-boot.run.fork=false', 'spring-boot:run') `
    -WorkingDirectory (Join-Path $root 'end_part') `
    -PidFileName 'backend.pid'
}

if (Test-PortOpen -Port $FrontendPort) {
  Write-Step "Frontend already appears to be running on port $FrontendPort."
} else {
  Start-ManagedProcess `
    -Name 'frontend' `
    -FilePath $frontendVite `
    -ArgumentList @('--host', '127.0.0.1', '--port', '5173') `
    -WorkingDirectory (Join-Path $root 'frontend') `
    -PidFileName 'frontend.pid'
}

$detectorPidFile = Join-Path $pidDir 'detector-supervisor.pid'
$detectorRunning = $false
if (Test-Path $detectorPidFile) {
  $existingPid = (Get-Content $detectorPidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
  if ($existingPid) {
    $existingProcess = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
    if ($null -ne $existingProcess) {
      $detectorRunning = $true
      Write-Step "Detector supervisor already running with PID $existingPid."
    } else {
      Remove-Item $detectorPidFile -Force -ErrorAction SilentlyContinue
    }
  }
}

if (-not $detectorRunning) {
  $detectorPython = Get-DetectorPython
  Start-ManagedProcess `
    -Name 'detector-supervisor' `
    -FilePath $detectorPython `
    -ArgumentList @('.\yolo_inference_windows.py') `
    -WorkingDirectory $detectorWorkdir `
    -PidFileName 'detector-supervisor.pid'
}

try {
  if ($EnableNginx -and (Test-Path $nginxExe) -and (Test-Path $nginxConf)) {
    Wait-PortOpen -Name 'Nginx HTTP-FLV' -Port $NginxHttpPort -Timeout $TimeoutSeconds | Out-Null
    Wait-PortOpen -Name 'Nginx RTMP' -Port $NginxRtmpPort -Timeout $TimeoutSeconds | Out-Null
    Wait-HttpReady -Name 'Nginx stat' -Url "http://127.0.0.1:$NginxHttpPort/stat" -AcceptedStatusCodes @(200) -Timeout $TimeoutSeconds | Out-Null
  }
  Wait-PortOpen -Name 'Backend' -Port $BackendPort -Timeout $TimeoutSeconds | Out-Null
  Wait-HttpReady -Name 'Backend' -Url "http://127.0.0.1:$BackendPort/api/actuator/health" -AcceptedStatusCodes @(200, 401, 403) -Timeout $TimeoutSeconds | Out-Null
  Wait-PortOpen -Name 'Frontend' -Port $FrontendPort -Timeout $TimeoutSeconds | Out-Null
  Wait-HttpReady -Name 'Frontend' -Url "http://127.0.0.1:$FrontendPort" -AcceptedStatusCodes @(200) -Timeout $TimeoutSeconds | Out-Null
} catch {
  Write-Host ''
  Write-Step 'Startup health check failed. Recent backend log:'
  if (Test-Path (Join-Path $logDir 'backend.out.log')) {
    Get-Content (Join-Path $logDir 'backend.out.log') -Tail 30
  }
  Write-Host ''
  Write-Step 'Recent frontend log:'
  if (Test-Path (Join-Path $logDir 'frontend.out.log')) {
    Get-Content (Join-Path $logDir 'frontend.out.log') -Tail 20
  }
  throw
}

Write-Step 'Stack is ready.'
Write-Host ''
if ($EnableNginx -and (Test-Path $nginxExe)) {
  Write-Host "Nginx:    rtmp://127.0.0.1:$NginxRtmpPort / http://127.0.0.1:$NginxHttpPort"
}
Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
Write-Host "Backend:  http://127.0.0.1:$BackendPort/api"
Write-Host "Logs:     $logDir"
