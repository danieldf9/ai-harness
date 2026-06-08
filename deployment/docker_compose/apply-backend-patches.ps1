# Apply local backend source code patches to running API server container.
# Run this script after `docker compose up -d` whenever the container is recreated.
#
# Usage: .\apply-backend-patches.ps1

param(
    [string]$ContainerName = "onyx-api_server-1",
    [switch]$Restart = $true
)

$ErrorActionPreference = "Stop"

$patches = @(
    @{
        HostPath = "..\..\backend\onyx\server\query_and_chat\chat_backend.py"
        ContainerPath = "/app/onyx/server/query_and_chat/chat_backend.py"
        Description = "Chat backend - removes <thought> tags from chat session names"
    }
)

Write-Host "Applying backend patches to $ContainerName..." -ForegroundColor Cyan

foreach ($patch in $patches) {
    $hostFull = Join-Path $PSScriptRoot $patch.HostPath
    Write-Host "  Patching: $($patch.Description)"
    docker cp $hostFull "${ContainerName}:$($patch.ContainerPath)"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to copy $($patch.HostPath)"
    }
}

if ($Restart) {
    Write-Host "Restarting $ContainerName to apply changes..." -ForegroundColor Yellow
    docker restart $ContainerName
    Write-Host "Waiting for container to become healthy..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}

Write-Host "Done! Backend patches applied successfully." -ForegroundColor Green
