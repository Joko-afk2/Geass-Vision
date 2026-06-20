@echo off
title Installation WSL2 + Docker Desktop
echo.
echo === Installation WSL2 + Docker Desktop (admin requis) ===
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-docker-et-lancer.ps1"
echo.
pause
