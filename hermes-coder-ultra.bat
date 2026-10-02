@echo off
setlocal EnableExtensions

title Hermes x Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)

set "CTX=262144"
set "OUTPUT_RESERVE=65536"
set "COMPRESS_THRESHOLD=147456"
set "PROACTIVE_PRUNE=48000"
set "PORT=8080"
set "BASE_URL=http://127.0.0.1:%PORT%/v1"
set "MODEL_ID=qwen3.8-flash-next-coder-iq1_m"
set "EFFORT=medium"
set "SERVER_BAT=D:\Strata\run-coder-iq1_m-ultra.bat"

echo ============================================================
echo   Hermes x Strata Qwen3.8 Coder IQ1_M [256K Ultra]
echo   Profile        = Ultra (Spec 5, Res 380, PCIe 0.35, ShortRead 256)
echo   Context        = %CTX% (262K Tokens)
echo   Compression    = Threshold %COMPRESS_THRESHOLD%, Prune %PROACTIVE_PRUNE%
echo   Vision         = Native Multimodal (Strata mmproj)
echo   Spec Coupled   = STRATA_SPEC_COUPLED=1 (Target-aligned Sampling)
echo   API Endpoint   = %BASE_URL%
echo ============================================================
echo.

REM 1. Sync Hermes configuration
echo [1/3] Syncing Hermes configuration (Context: 256K, Threshold: 147456)...

call hermes config set providers.local-qwen.name "Local Strata Qwen3.8 Coder 256K Ultra" >nul 2>&1
call hermes config set providers.local-qwen.default_model "%MODEL_ID%" >nul 2>&1
call hermes config set model.default "%MODEL_ID%" >nul 2>&1
call hermes config set providers.local-qwen.context_length %CTX% >nul 2>&1
call hermes config set providers.local-qwen.base_url "%BASE_URL%" >nul 2>&1
call hermes config set model.base_url "%BASE_URL%" >nul 2>&1
call hermes config set model.context_length %CTX% >nul 2>&1
call hermes config set compression.max_attempts 10 >nul 2>&1
call hermes config set compression.threshold_tokens %COMPRESS_THRESHOLD% >nul 2>&1
call hermes config set compression.proactive_prune_tokens %PROACTIVE_PRUNE% >nul 2>&1
call hermes config set agent.reasoning_effort %EFFORT% --force >nul 2>&1
call hermes config unset agent.system_prompt >nul 2>&1
call hermes config set agent.image_input_mode native >nul 2>&1
call hermes config set model.supports_vision true >nul 2>&1
call hermes config set auxiliary.title_generation.model_upgrade_enabled false >nul 2>&1
call hermes config set moa.enabled false >nul 2>&1

echo [1/3] Hermes configuration synced successfully!

REM 2. Check or launch Strata service
echo.
echo [2/3] Checking Strata engine status on port %PORT%...
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 (
    echo        Strata service is ALREADY running on port %PORT%. Reusing active instance!
    goto :ready
)

echo        Starting Strata 256K Ultra server in a separate window...
start "Strata Coder 256K Ultra (Server)" cmd /c call "%SERVER_BAT%"

set /a TRIES=0
:waitloop
set /a TRIES+=1
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 goto :ready
if %TRIES% GEQ 60 goto :noready
ping 127.0.0.1 -n 3 >nul
goto :waitloop

:noready
echo [!] Waited 120s. Please check the Strata server console window for loading progress.
goto :ready

:ready
echo.
echo [3/3] ============================================================
echo   Strata 256K Ultra Engine is READY! Hermes points to %BASE_URL%.
echo   You can now launch Hermes Desktop or run 'hermes' in terminal!
echo ============================================================
echo.
echo Press any key to stop Strata engine and exit...
pause >nul

echo Stopping Strata...
taskkill /F /IM strata.exe >nul 2>&1
taskkill /F /IM strata-vision.exe >nul 2>&1
echo Done.
endlocal
