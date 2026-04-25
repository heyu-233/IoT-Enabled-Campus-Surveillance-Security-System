param(
  [string]$ServiceName = 'MySQL80',
  [int]$Port = 3306,
  [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'

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

$service = Get-Service -Name $ServiceName -ErrorAction Stop

if ($service.Status -ne 'Running') {
  Write-Host "Starting MySQL service: $ServiceName"
  Start-Service -Name $ServiceName
} else {
  Write-Host "MySQL service already running: $ServiceName"
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
  if (Test-PortOpen -Port $Port) {
    Write-Host "MySQL is ready on port $Port"
    exit 0
  }

  Start-Sleep -Milliseconds 500
}

Write-Error "MySQL did not become ready on port $Port within $TimeoutSeconds seconds."
exit 1
