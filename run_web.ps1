# PowerShell launcher for ADK AI Text Humanizer Agent
param(
    [int]$Port = 8000
)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Starting Google ADK Web UI for AI Text Humanizer Agent..." -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

# Terminate any process currently occupying the port to prevent Errno 10048
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -gt 0) {
            Write-Host "Clearing previous process (PID $procId) on port $Port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "Access in your browser at: http://127.0.0.1:$Port" -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\adk.exe" web --port $Port .
