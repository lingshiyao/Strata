@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)
cd /d "D:\Strata"

REM 0. Clean up any lingering engine processes and release VRAM/RAM
tasklist /FI "IMAGENAME eq strata.exe" 2>nul | find /I /N "strata.exe" >nul
if not errorlevel 1 (
    echo Cleaning up lingering engine instance to release VRAM...
    taskkill /F /IM strata.exe >nul 2>&1
    taskkill /F /IM strata-vision.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

REM 1. Enable Coupled Stochastic Speculative Drafting
set "STRATA_SPEC_COUPLED=1"

REM 2. Activate Windows High Performance Power Scheme
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1

REM 3. Select Reasoning Prompt & Effort Mode (Manual choice, no timeout)
echo ============================================================
echo   [1/2] 请选择思考与系统提示词模式 (Prompt & Effort Mode):
echo   [1] Original High  (阿里原生无约束深思 - 极限版本)
echo   [2] Optimized High (防草稿纸影子编码 - 甜蜜点完全体) [推荐]
echo   [3] Medium 智力    (官方中等思考 - 无 System Prompt，纯净原生态)
echo   [4] Low 智力       (官方低思考 - 简短聚焦 System Prompt)
echo ============================================================
choice /c 1234 /m "请按键选择模式 [1, 2, 3, 4] (已关闭倒计时，推荐选 2): "
if errorlevel 4 goto :mode_low
if errorlevel 3 goto :mode_med
if errorlevel 2 goto :mode_opt
if errorlevel 1 goto :mode_raw

:mode_raw
echo Activating Mode 1: Original Raw High Prompt...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.raw" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
set "EFFORT=high"
goto :select_budget

:mode_opt
echo Activating Mode 2: Optimized Battle-Tested Prompt...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.opt" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
set "EFFORT=high"
goto :select_budget

:mode_med
echo Activating Mode 3: Medium Effort (No System Prompt)...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.raw" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
set "EFFORT=medium"
goto :select_budget

:mode_low
echo Activating Mode 4: Low Effort (Focused Minimal Prompt)...
copy /y "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja.raw" "E:\Strata-data\packs\coder-iq1_m\tokenizer\chat_template.jinja" >nul
set "EFFORT=low"
goto :select_budget

:select_budget
echo.
echo ============================================================
echo   [2/2] 请选择思考预算截断档位 (Thinking Budget - 1024 整数倍):
echo   [1] 0.5K (512 tokens)    - 极速微思考
echo   [2] 1K   (1,024 tokens)  - 极轻量思考
echo   [3] 2K   (2,048 tokens)  - 快速单点逻辑
echo   [4] 4K   (4,096 tokens)  - 标准敏捷编码
echo   [5] 6K   (6,144 tokens)  - 进阶敏捷设计
echo   [6] 8K   (8,192 tokens)  - 完整系统规划
echo   [7] 16K  (16,384 tokens) - 甜蜜点黄金推荐 [推荐]
echo   [8] 32K  (32,768 tokens) - 深度架构推演
echo   [9] 48K  (49,152 tokens) - 超大工程推演
echo   [A] 64K  (65,536 tokens) - 极限界限深度思考
echo   [C] Custom 自定义输入    (手动输入 K 数，自动乘 1024)
echo ============================================================
choice /c 123456789AC /m "请按键选择预算档位 [1-9, A, C] (已关闭倒计时): "
if errorlevel 11 goto :budget_custom
if errorlevel 10 goto :budget_64k
if errorlevel 9 goto :budget_48k
if errorlevel 8 goto :budget_32k
if errorlevel 7 goto :budget_16k
if errorlevel 6 goto :budget_8k
if errorlevel 5 goto :budget_6k
if errorlevel 4 goto :budget_4k
if errorlevel 3 goto :budget_2k
if errorlevel 2 goto :budget_1k
if errorlevel 1 goto :budget_05k

:budget_05k
set "BUDGET_TOKENS=512"
set "BUDGET_NAME=0.5K [512 tokens]"
goto :start_server

:budget_1k
set "BUDGET_TOKENS=1024"
set "BUDGET_NAME=1K [1,024 tokens]"
goto :start_server

:budget_2k
set "BUDGET_TOKENS=2048"
set "BUDGET_NAME=2K [2,048 tokens]"
goto :start_server

:budget_4k
set "BUDGET_TOKENS=4096"
set "BUDGET_NAME=4K [4,096 tokens]"
goto :start_server

:budget_6k
set "BUDGET_TOKENS=6144"
set "BUDGET_NAME=6K [6,144 tokens]"
goto :start_server

:budget_8k
set "BUDGET_TOKENS=8192"
set "BUDGET_NAME=8K [8,192 tokens]"
goto :start_server

:budget_16k
set "BUDGET_TOKENS=16384"
set "BUDGET_NAME=16K [16,384 tokens]"
goto :start_server

:budget_32k
set "BUDGET_TOKENS=32768"
set "BUDGET_NAME=32K [32,768 tokens]"
goto :start_server

:budget_48k
set "BUDGET_TOKENS=49152"
set "BUDGET_NAME=48K [49,152 tokens]"
goto :start_server

:budget_64k
set "BUDGET_TOKENS=65536"
set "BUDGET_NAME=64K [65,536 tokens]"
goto :start_server

:budget_custom
set /p USER_K="请输入思考预算 K 数 (例如输入 24 代表 24K, 80 代表 80K): "
set /a BUDGET_TOKENS=USER_K * 1024
if %BUDGET_TOKENS% LEQ 0 (
    echo 输入无效，自动回退到 16K [16,384 tokens]...
    set "BUDGET_TOKENS=16384"
    set "BUDGET_NAME=16K [16,384 tokens]"
) else (
    set "BUDGET_NAME=%USER_K%K [%BUDGET_TOKENS% tokens]"
)
goto :start_server

:start_server
echo.
echo ============================================================
echo   Reasoning Effort: %EFFORT%
echo   Thinking Budget : %BUDGET_NAME%
echo   Launching Strata Engine...
echo ============================================================
"D:\Strata\.venv\Scripts\python.exe" "D:\Strata\serve\server.py" --engine strata --config "D:\Strata\strata-coder-iq1_m-ultra.json" --reasoning-budget-tokens %BUDGET_TOKENS% --reasoning-effort %EFFORT% --port 8080 --open
taskkill /F /IM strata.exe >nul 2>&1
taskkill /F /IM strata-vision.exe >nul 2>&1
if errorlevel 1 pause
