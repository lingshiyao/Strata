@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

title OpenCode x Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)

set "CTX=262144"
set "PORT=8080"
set "BASE_URL=http://127.0.0.1:%PORT%/v1"
set "MODEL_ID=strata-coder/qwen3.8-flash-next-coder-iq1_m"
set "SERVER_BAT=D:\Strata\run-coder-iq1_m-ultra.bat"
set "OPENCODE_EXE=C:\Users\Admin\AppData\Local\Programs\@opencode-aidesktop\OpenCode.exe"

echo ============================================================
echo   OpenCode x Strata Qwen3.8 Coder IQ1_M [256K Ultra]
echo   Profile        = Ultra (Spec 5, Res 380, PCIe 0.35, ShortRead 256)
echo   Context        = %CTX% (262K Tokens)
echo   Vision         = Native Multimodal (Strata mmproj)
echo   Spec Coupled   = STRATA_SPEC_COUPLED=1 (Target-aligned Sampling)
echo   Model ID       = %MODEL_ID%
echo   API Endpoint   = %BASE_URL%
echo ============================================================
echo.

REM 1. Check or launch Strata service
echo [1/3] Checking Strata engine status on port %PORT%...
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 (
    echo        Strata service is ALREADY running on port %PORT%. Reusing active instance!
    goto :check_opencode
)

echo        Starting Strata 256K Ultra server in a separate window...
start "Strata Coder 256K Ultra (Server)" cmd /c call "%SERVER_BAT%"

set /a TRIES=0
:waitloop
set /a TRIES+=1
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 goto :check_opencode
if %TRIES% GEQ 60 goto :noready
ping 127.0.0.1 -n 3 >nul
goto :waitloop

:noready
echo [!] Waited 120s. Please check the Strata server console window for loading progress.
goto :check_opencode

:check_opencode
echo.
echo [2/3] Checking OpenCode Desktop client...
tasklist /FI "IMAGENAME eq OpenCode.exe" 2>nul | find /I /N "OpenCode.exe" >nul
if not errorlevel 1 (
    echo        OpenCode Desktop is ALREADY running!
) else (
    if exist "%OPENCODE_EXE%" (
        echo        Launching OpenCode Desktop (%OPENCODE_EXE%)...
        start "" "%OPENCODE_EXE%"
    ) else (
        echo        OpenCode Desktop executable not found at %OPENCODE_EXE%.
        echo        You can start it manually or run 'opencode' in terminal.
    )
)

echo.
echo [3/3] ============================================================
echo   Strata 256K Ultra Engine is READY for OpenCode!
echo   Model: Strata Qwen3.8 Coder 125B (MoE) -> 256K Ultra
echo   Endpoint: %BASE_URL%
echo.
echo   In OpenCode GUI:
echo     1. Click the model dropdown (or press Ctrl+/ or type /models)
echo     2. Select 'Strata Coder 125B 256K Ultra (MoE)'
echo   In CLI:
echo     Run: opencode -m strata-coder/qwen3.8-flash-next-coder-iq1_m
echo ============================================================
echo.
echo Press any key to stop Strata engine and exit...
pause >nul

echo Stopping Strata...
taskkill /F /IM strata.exe >nul 2>&1
taskkill /F /IM strata-vision.exe >nul 2>&1
echo Done.
endlocal
