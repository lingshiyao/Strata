@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)
cd /d "D:\Strata"

:: 0. Clean up any lingering engine processes and release VRAM/RAM
tasklist /FI "IMAGENAME eq strata.exe" 2>nul | find /I /N "strata.exe" >nul
if not errorlevel 1 (
    echo Cleaning up lingering engine instance to release VRAM...
    taskkill /F /IM strata.exe >nul 2>&1
    taskkill /F /IM strata-vision.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: 1. Enable Coupled Stochastic Speculative Drafting
set "STRATA_SPEC_COUPLED=1"

:: 2. Activate Windows High Performance Power Scheme
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1

:: 3. Select Reasoning Prompt Mode (Default to Mode 2 if timeout or auto)
echo ============================================================
echo   Select Strata Reasoning System Prompt Mode:
echo   [1] Original High (阿里原生无约束深思 - 极限版本)
echo   [2] Optimized High (防草稿纸影子编码 - 甜蜜点完全体)
echo ============================================================
choice /c 12 /n /t 3 /d 2 /m "Select mode [1, 2] (Default 2 in 3s): "
if errorlevel 2 goto :mode2
if errorlevel 1 goto :mode1

:mode1
echo Activating Mode 1: Original Raw Prompt...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.raw" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
goto :start_server

:mode2
echo Activating Mode 2: Optimized Battle-Tested Prompt...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.opt" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
goto :start_server

:start_server
echo Launching Strata Engine...
"D:\Strata\.venv\Scripts\python.exe" "D:\Strata\serve\server.py" --engine strata --config "D:\Strata\strata-coder-iq1_m-ultra.json" --port 8080 --open
taskkill /F /IM strata.exe >nul 2>&1
taskkill /F /IM strata-vision.exe >nul 2>&1
if errorlevel 1 pause
