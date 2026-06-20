# Lance l'app locale (sans Docker) sur http://localhost:8080
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "Build frontend..." -ForegroundColor Yellow
Set-Location "$Root\web\frontend"
if (-not (Test-Path "node_modules")) { npm install }
npm run build

Write-Host "Copie vers web/backend/static..." -ForegroundColor Yellow
$static = "$Root\web\backend\static"
Get-ChildItem $static -Exclude ".gitkeep" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "$Root\web\frontend\dist\*" $static -Recurse -Force

Write-Host "Demarrage serveur sur http://localhost:8080" -ForegroundColor Green
Set-Location $Root
python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8080 --reload
