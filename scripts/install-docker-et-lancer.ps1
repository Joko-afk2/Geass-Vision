# Installation WSL2 + Docker Desktop + lancement du moteur d'échecs
# Exécuter en PowerShell administrateur (ou via élévation UAC)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== Projet : $ProjectRoot ===" -ForegroundColor Cyan

# --- 1. WSL2 ---
Write-Host "`n[1/4] WSL2..." -ForegroundColor Yellow
$wslOk = $false
try {
    $status = wsl --status 2>&1 | Out-String
    if ($status -match "version par d.faut.*2|Default Version.*2|WSL version.*2") {
        $wslOk = $true
        Write-Host "WSL2 deja installe."
    }
} catch {}

if (-not $wslOk) {
    Write-Host "Installation de WSL2 (Ubuntu)..."
    wsl --install --no-launch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tentative avec wsl --install sans options..."
        wsl --install
    }
    Write-Host "WSL installe. REDEMARRAGE REQUIS." -ForegroundColor Red
    shutdown /r /t 60 /c "Installation WSL2 - redemarrage dans 60 s"
    Write-Host "Redemarrage dans 60 secondes. Relance scripts\INSTALLER-DOCKER-ADMIN.bat apres le reboot."
    exit 0
}

# --- 2. Docker Desktop ---
Write-Host "`n[2/4] Docker Desktop..." -ForegroundColor Yellow
$dockerPath = "${env:ProgramFiles}\Docker\Docker\resources\bin\docker.exe"
if (-not (Test-Path $dockerPath)) {
    Write-Host "Installation via winget..."
    winget install Docker.DockerDesktop `
        --accept-package-agreements `
        --accept-source-agreements `
        --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Echec installation Docker. Installe manuellement : https://docs.docker.com/desktop/setup/install/windows-install/"
    }
    Write-Host "Docker Desktop installe. Lance-le depuis le menu Demarrer, puis relance ce script."
    Start-Process "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    Write-Host "Attente demarrage Docker (jusqu'a 3 min)..."
    $deadline = (Get-Date).AddMinutes(3)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        if (Get-Command docker -ErrorAction SilentlyContinue) {
            docker info 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { break }
        }
    }
}

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker non disponible. Ouvre Docker Desktop manuellement puis relance ce script."
}

Write-Host "Docker : $(docker --version)"

# --- 3. Arreter uvicorn local sur 8000 si present ---
Write-Host "`n[3/4] Liberation du port 8000..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# --- 4. Build et lancement ---
Write-Host "`n[4/4] docker compose up --build..." -ForegroundColor Yellow
Set-Location $ProjectRoot
docker compose down 2>$null
docker compose up --build -d

Start-Sleep -Seconds 8
$health = $null
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 30
} catch {}

if ($health -and $health.StatusCode -eq 200) {
    Write-Host "`n=== SUCCES ===" -ForegroundColor Green
    Write-Host "App disponible : http://localhost:8080"
    Write-Host "Arreter : docker compose down"
} else {
    Write-Host "`nConteneur demarre. Verifie dans quelques secondes : http://localhost:8080/health"
    docker compose ps
    docker compose logs --tail 30
}
