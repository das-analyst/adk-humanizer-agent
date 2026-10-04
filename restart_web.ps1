# PowerShell script to cleanly restart ADK Playground Web UI
param(
    [int]$Port = 8000
)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Restarting Google ADK Web UI for AI Text Humanizer..." -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Cyan

# Terminate any process currently occupying the port
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($connections) {
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -gt 0) {
            Write-Host "Stopping existing process (PID $procId) on port $Port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

Write-Host "Launching ADK Web UI on http://127.0.0.1:$Port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host "=====================================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot
& "$PSScriptRoot\.venv\Scripts\adk.exe" web --port $Port .
