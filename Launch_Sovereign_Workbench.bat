@echo off
title Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)
color 0A
echo ====================================================================
echo   Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)
echo   Local Open-Weight LLM (100%% Air-Gapped Sovereign AI)
echo   Instant Cookie Session Vault (Zero OTP Delay)
echo ====================================================================
echo.

:: Check if user requested direct launch flag or if wizard should run
if "%1"=="--direct" goto DIRECT_LAUNCH

echo [1/3] Launching Sovereign Automated Setup & Permissions Panel...
python setup_wizard.py
if %errorlevel% equ 0 (
    exit /b 0
)

:DIRECT_LAUNCH
echo [2/3] Checking Local Ollama AI Engine...
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo       Ollama service not running. Starting Ollama in background...
    start /b "" ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
)
curl.exe -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo       [OK] Local AI Engine active on http://127.0.0.1:11434
) else (
    echo       [NOTE] Standby mode. Local fallback synthesizer ready.
)
echo.
if "%NETWORK_MODE%"=="LAN" (
    echo [3/3] Starting FastAPI Server in LAN Access Mode (0.0.0.0:8001)...
    echo       mDNS Discovery: http://ai-workbench.local:8001
) else (
    echo [3/3] Starting FastAPI Server in LOCAL_ONLY Mode (127.0.0.1:8001)...
)
echo Opening Sovereign Workbench in default browser...
start "" "http://127.0.0.1:8001"
echo.
python server.py
pause

