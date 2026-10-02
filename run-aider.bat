@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"

title Aider x Strata Qwen3.8 Coder IQ1_M [256K Ultra]

set "PORT=8080"
set "BASE_URL=http://127.0.0.1:%PORT%/v1"
set "MODEL_NAME=openai/qwen3.8-flash-next-coder-iq1_m"
set "NO_PROXY=localhost,127.0.0.1,::1"
set "no_proxy=localhost,127.0.0.1,::1"
set "SERVER_BAT=D:\Strata\run-coder-iq1_m-ultra.bat"

echo ============================================================
echo   Aider x Strata Qwen3.8 Coder [256K Ultra Diff Engine]
echo   Endpoint       = %BASE_URL%
echo   Model          = %MODEL_NAME%
echo   Edit Format    = diff (Search/Replace Minimal Patching)
echo   Repo Map       = 1024 Tokens AST Tree-Sitter
echo ============================================================
echo.

REM 1. Check or launch Strata service
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 (
    echo [1/2] Strata 256K Ultra Engine is ALREADY running on port %PORT%.
    goto :run_aider
)

echo [1/2] Strata engine is not running. Launching in separate window...
start "Strata Coder 256K Ultra (Server)" cmd /c call "%SERVER_BAT%"

set /a TRIES=0
:waitloop
set /a TRIES+=1
curl -s -m 2 "http://127.0.0.1:%PORT%/health" >nul 2>&1
if not errorlevel 1 goto :run_aider
if %TRIES% GEQ 60 (
    echo [!] Server wait timed out. Continuing anyway...
    goto :run_aider
)
ping 127.0.0.1 -n 3 >nul
goto :waitloop

:run_aider
echo [2/2] Launching Aider CLI (Pair Programming Assistant)...
echo       Tip: Type /help for commands, /undo to revert changes, /architect for dual-agent.
echo.

aider --openai-api-base %BASE_URL% ^
      --openai-api-key dummy ^
      --model %MODEL_NAME% ^
      --model-settings-file "D:\Strata\.aider.model.settings.yml" ^
      --edit-format diff ^
      --map-tokens 1024 ^
      --no-show-model-warnings ^
      --no-check-update ^
      --no-gitignore ^
      --encoding utf-8 %*

endlocal
