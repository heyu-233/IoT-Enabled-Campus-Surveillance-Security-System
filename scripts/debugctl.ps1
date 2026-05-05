param(
  [ValidateSet('status')]
  [string]$Command = 'status',
  [string]$VmHost = '192.168.1.100',
  [string]$BoardHost = 'board',
  [string]$BoardIp = '192.168.1.2',
  [string]$HostBoardIp = '192.168.1.10',
  [int]$BackendPort = 8081,
  [int]$FrontendPort = 5173,
  [int]$NginxHttpPort = 8080,
  [int]$NginxRtmpPort = 1935,
  [int]$MqttPort = 1883
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $root '.runtime'
$logDir = Join-Path $runtimeDir 'logs'
$pidDir = Join-Path $runtimeDir 'pids'

function Write-Section {
  param([string]$Title)
  Write-Host ''
  Write-Host "== $Title =="
}

function Write-Check {
  param(
    [string]$Name,
    [bool]$Ok,
    [string]$Detail = ''
  )

  $mark = if ($Ok) { '[OK]' } else { '[FAIL]' }
  if ($Detail) {
    Write-Host ("{0} {1} - {2}" -f $mark, $Name, $Detail)
  } else {
    Write-Host ("{0} {1}" -f $mark, $Name)
  }
}

function Test-PortOpen {
  param(
    [string]$TargetHost = '127.0.0.1',
    [int]$Port,
    [int]$TimeoutMs = 1000
  )

  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect($TargetHost, $Port, $null, $null)
    $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
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

function Invoke-CheckedSsh {
  param(
    [string]$Target,
    [string]$RemoteCommand,
    [int]$TimeoutSeconds = 8
  )

  $args = @(
    '-o', 'BatchMode=yes',
    '-o', "ConnectTimeout=$TimeoutSeconds",
    $Target,
    $RemoteCommand
  )

  try {
    $output = & ssh @args 2>&1
    $exitCode = $LASTEXITCODE
  } catch {
    $output = $_.Exception.Message
    $exitCode = 1
  }

  return [pscustomobject]@{
    Ok = ($exitCode -eq 0)
    Output = (($output | Out-String).Trim())
  }
}

function Test-HttpStatus {
  param(
    [string]$Url,
    [int[]]$AcceptedStatusCodes = @(200)
  )

  try {
    $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 3 -UseBasicParsing
    return [pscustomobject]@{
      Ok = ($AcceptedStatusCodes -contains [int]$response.StatusCode)
      StatusCode = [int]$response.StatusCode
    }
  } catch {
    $statusCode = 0
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
      $statusCode = [int]$_.Exception.Response.StatusCode
    }
    return [pscustomobject]@{
      Ok = ($AcceptedStatusCodes -contains $statusCode)
      StatusCode = $statusCode
    }
  }
}

function Test-PidFile {
  param(
    [string]$Name,
    [string]$PidFileName
  )

  $pidFile = Join-Path $pidDir $PidFileName
  if (-not (Test-Path $pidFile)) {
    Write-Check $Name $false "PID file not found: $pidFile"
    return
  }

  $rawPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
  if (-not $rawPid) {
    Write-Check $Name $false "PID file is empty: $pidFile"
    return
  }

  $process = Get-Process -Id ([int]$rawPid) -ErrorAction SilentlyContinue
  Write-Check $Name ($null -ne $process) "PID $rawPid"
}

function Show-RecentLogSignal {
  param(
    [string]$Name,
    [string]$Path,
    [int]$Tail = 5
  )

  if (-not (Test-Path $Path)) {
    Write-Check $Name $false "log not found: $Path"
    return
  }

  $length = (Get-Item $Path).Length
  Write-Check $Name $true "$length bytes"
  if ($length -gt 0) {
    Get-Content -Path $Path -Tail $Tail
  }
}

function Show-Status {
  Write-Host "[debugctl] full-link status check"
  Write-Host "Project: $root"

  Write-Section 'Local services'
  Write-Check 'Backend port' (Test-PortOpen -Port $BackendPort) "127.0.0.1:$BackendPort"
  Write-Check 'Frontend port' (Test-PortOpen -Port $FrontendPort) "127.0.0.1:$FrontendPort"
  Write-Check 'Nginx HTTP port' (Test-PortOpen -Port $NginxHttpPort) "127.0.0.1:$NginxHttpPort"
  Write-Check 'Nginx RTMP port' (Test-PortOpen -Port $NginxRtmpPort) "127.0.0.1:$NginxRtmpPort"
  Write-Check 'MQTT port' (Test-PortOpen -Port $MqttPort) "127.0.0.1:$MqttPort"

  $backendHealth = Test-HttpStatus -Url "http://127.0.0.1:$BackendPort/api/actuator/health" -AcceptedStatusCodes @(200, 401, 403)
  Write-Check 'Backend health endpoint' $backendHealth.Ok "HTTP $($backendHealth.StatusCode)"

  $frontendHealth = Test-HttpStatus -Url "http://127.0.0.1:$FrontendPort" -AcceptedStatusCodes @(200)
  Write-Check 'Frontend HTTP' $frontendHealth.Ok "HTTP $($frontendHealth.StatusCode)"

  Write-Section 'Managed local processes'
  Test-PidFile 'Backend process' 'backend.pid'
  Test-PidFile 'Frontend process' 'frontend.pid'
  Test-PidFile 'Detector supervisor process' 'detector-supervisor.pid'

  Write-Section 'Remote SSH'
  $vm = Invoke-CheckedSsh -Target $VmHost -RemoteCommand 'echo vm-ok'
  Write-Check 'Ubuntu VM SSH' $vm.Ok $vm.Output

  $board = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand 'echo board-ok'
  Write-Check 'i.MX6ULL board SSH' $board.Ok $board.Output

  Write-Section 'Board runtime'
  if ($board.Ok) {
    $processes = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand "ps | grep -E 'edge|v4l2|mosquitto' | grep -v grep"
    Write-Check 'Board edge processes' $processes.Ok $processes.Output

    $video = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand 'ls /dev/video* 2>/dev/null'
    Write-Check 'Board video devices' $video.Ok $video.Output

    $mqtt = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand "/root/mosquitto_pub -h $HostBoardIp -p $MqttPort -t test/debugctl -m ping"
    Write-Check 'Board to host MQTT publish' $mqtt.Ok $mqtt.Output

    $bootLog = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand 'tail -20 /root/edge_agent_boot.log 2>/dev/null'
    Write-Check 'Board boot log tail' $bootLog.Ok $bootLog.Output

    $agentLog = Invoke-CheckedSsh -Target $BoardHost -RemoteCommand 'tail -20 /tmp/edge_agent.log 2>/dev/null'
    Write-Check 'Board agent log tail' $agentLog.Ok $agentLog.Output
  } else {
    Write-Check 'Board runtime checks' $false 'skipped because board SSH failed'
  }

  Write-Section 'Local logs'
  Show-RecentLogSignal 'Backend stdout log' (Join-Path $logDir 'backend.out.log') 5
  Show-RecentLogSignal 'Backend stderr log' (Join-Path $logDir 'backend.err.log') 5
  Show-RecentLogSignal 'Frontend stdout log' (Join-Path $logDir 'frontend.out.log') 5
  Show-RecentLogSignal 'Detector stderr log' (Join-Path $logDir 'detector-supervisor.err.log') 5
}

switch ($Command) {
  'status' { Show-Status }
}
