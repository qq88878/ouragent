@echo off
echo ============================================
echo   MIMO API Proxy (host TLS bridge)
echo ============================================
cd /d "%~dp0"
start "MIMO-Proxy" /MIN python mimo-proxy.py 18080
echo Proxy started on port 18080
echo.
