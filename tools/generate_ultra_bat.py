import os

bat_content = """@echo off
chcp 65001 >nul
setlocal EnableExtensions
title Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)
cd /d "D:\\Strata"

rem 0. Clean up any lingering engine processes and release VRAM/RAM
tasklist /FI "IMAGENAME eq strata.exe" 2>nul | find /I /N "strata.exe" >nul
if not errorlevel 1 (
    echo Cleaning up lingering engine instance to release VRAM...
    taskkill /F /IM strata.exe >nul 2>&1
    taskkill /F /IM strata-vision.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

rem 1. Enable Coupled Stochastic Speculative Drafting
set "STRATA_SPEC_COUPLED=1"

rem 2. Activate Windows High Performance Power Scheme
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1

rem 3. Select Reasoning Prompt and Effort Mode (No timeout)
echo ===============================================================================
echo   [1/3] Select Reasoning Prompt and Effort Mode (选择推理模式与提示词): [Mode]
echo ===============================================================================
echo.
echo   [1] Original High - 阿里原生无约束深思 (极限版本) [Raw High]
echo       -------------------------------------------------------------------------
echo       [EN] "Reasoning effort is set to xhigh. Please think carefully through
echo             the task, validate key assumptions, consider plausible alternatives,
echo             and prioritize correctness, consistency, and clarity in the final answer."
echo       [CN] 官方原始提示词：提示模型深入思考与自我验证，但无格式约束，易在草稿区
echo            生成数百行完整代码（影子编码）导致 32K 触顶与语法截断。[Original]
echo       -------------------------------------------------------------------------
echo.
echo   [2] Optimized High - 防草稿纸影子编码 (甜蜜点完全体) [Recommended]
echo       -------------------------------------------------------------------------
echo       [EN] "Reasoning effort is set to xhigh. Focus cognitive depth on system
echo             architecture, mathematical derivations, algorithmic invariants, and
echo             edge-case contracts. Express your reasoning through concise symbolic
echo             scratchpads, state transitions, and logical proofs. Reserve full
echo             production code synthesis and large data assets exclusively for the
echo             final response."
echo       [CN] 生产优化提示词：强制将思考聚焦于架构、数学证明与状态机设计，严禁在
echo            思考区预先撰写正式生产代码与大数组，彻底消除影子编码浪费。[Optimized]
echo       -------------------------------------------------------------------------
echo.
echo   [3] Medium Effort - 官方原生中等思考 (纯净无提示词) [Native Medium]
echo       -------------------------------------------------------------------------
echo       [EN] (No extra system instructions. Model reasons naturally.)
echo       [CN] 官方中档纯净模式：不注入任何自定义提示词，依靠模型原生思考逻辑自发
echo            推演并收敛，适合标准敏捷任务。[Native Medium]
echo       -------------------------------------------------------------------------
echo.
echo   [4] Low Effort - 官方原生低思考 (极简聚焦提示词) [Focused Low]
echo       -------------------------------------------------------------------------
echo       [EN] "Reasoning effort is set to low. Keep your thinking brief and focused,
echo             moving directly to the conclusion without unnecessary elaboration."
echo       [CN] 官方低档聚焦模式：强制极简思考，直奔结论，适合轻量单点改动或极速问答。[Focused Low]
echo       -------------------------------------------------------------------------
echo.
echo   [5] Staged Nudge - 阶段思维敲打与自然收敛协议 (接力续思) [Paired with Wrap-up 3]
echo       -------------------------------------------------------------------------
echo       [EN] "Reasoning effort is set to xhigh. Staged Nudge ^& Natural Closure
echo             Protocol: To prevent attention drift during deep reasoning, a staged
echo             budget guard is active. When reasoning hits the stage limit, the system
echo             truncates the thought and injects '[Thinking Nudge]'. When you observe
echo             '[Thinking Nudge]', you MUST strictly follow these rules: (1) No premature
echo             action: Receiving this nudge means your thinking was externally
echo             interrupted by the limit, NOT naturally completed. Absolutely do not
echo             rush into outputting code or tool calls; provide only a brief milestone
echo             checkpoint of your current analysis. (2) Relay reasoning: You must
echo             preserve current progress and actively resume reasoning in the next step,
echo             continuing across multiple nudges if needed. (3) Natural Closure Rule: You
echo             are ONLY permitted to emit code or tool calls when your reasoning concludes
echo             NATURALLY on its own within budget, never because of an external cutoff.
echo             Every line of delivered code must be the product of a fully and naturally
echo             matured thought."
echo       [CN] 阶段敲打协议（配对闭合模式 3）：将思考拆为阶段预算。被敲打截断 = 没想完 =
echo            严禁动手写代码！在当前正文仅留进度快照，下轮主动接力续思，唯有当模型在
echo            预算内自然想透闭合时，才允许正式输出代码与调用工具。[Staged Nudge]
echo       -------------------------------------------------------------------------
echo ===============================================================================
choice /c 12345 /m "Select mode [1, 2, 3, 4, 5] (Recommended: 2, or 5 for Nudge): "
if errorlevel 5 goto :mode_nudge
if errorlevel 4 goto :mode_low
if errorlevel 3 goto :mode_med
if errorlevel 2 goto :mode_opt
if errorlevel 1 goto :mode_raw

:mode_raw
echo Activating Mode 1: Original Raw High Prompt...
copy /y "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja.raw" "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja" >nul
set "EFFORT=high"
goto :select_budget

:mode_opt
echo Activating Mode 2: Optimized Battle-Tested Prompt...
copy /y "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja.opt" "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja" >nul
set "EFFORT=high"
goto :select_budget

:mode_med
echo Activating Mode 3: Medium Effort (No System Prompt)...
copy /y "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja.raw" "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja" >nul
set "EFFORT=medium"
goto :select_budget

:mode_low
echo Activating Mode 4: Low Effort (Focused Minimal Prompt)...
copy /y "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja.raw" "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja" >nul
set "EFFORT=low"
goto :select_budget

:mode_nudge
echo Activating Mode 5: Staged Nudge and Natural Closure Protocol...
copy /y "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja.nudge" "E:\\Strata-data\\packs\\coder-iq1_m\\tokenizer\\chat_template.jinja" >nul
set "EFFORT=high"
goto :select_budget

:select_budget
echo.
echo ===============================================================================
echo   [2/3] Select Thinking Budget (1024 Multiples): [Budget]
echo   [1] 0.5K (512 tokens)   - 极速微思考 [Micro]
echo   [2] 1K   (1024 tokens)  - 极轻量思考 [Ultra Light]
echo   [3] 2K   (2048 tokens)  - 快速单点逻辑 [Fast Logic]
echo   [4] 4K   (4096 tokens)  - 标准敏捷编码 [Standard]
echo   [5] 6K   (6144 tokens)  - 进阶敏捷设计 [Advanced]
echo   [6] 8K   (8192 tokens)  - 完整系统规划 [Architecture]
echo   [7] 16K  (16384 tokens) - 甜蜜点黄金推荐 [Recommended]
echo   [8] 32K  (32768 tokens) - 深度架构推演 [Deep]
echo   [9] 48K  (49152 tokens) - 超大工程推演 [Large Project]
echo   [A] 64K  (65536 tokens) - 极限界限深度思考 [Extreme]
echo   [C] Custom Tokens       - 自定义输入 (手动输入 K 数 x 1024) [Custom]
echo ===============================================================================
choice /c 123456789AC /m "Select budget [1-9, A, C]: "
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
goto :select_wrapup

:budget_1k
set "BUDGET_TOKENS=1024"
set "BUDGET_NAME=1K [1024 tokens]"
goto :select_wrapup

:budget_2k
set "BUDGET_TOKENS=2048"
set "BUDGET_NAME=2K [2048 tokens]"
goto :select_wrapup

:budget_4k
set "BUDGET_TOKENS=4096"
set "BUDGET_NAME=4K [4096 tokens]"
goto :select_wrapup

:budget_6k
set "BUDGET_TOKENS=6144"
set "BUDGET_NAME=6K [6144 tokens]"
goto :select_wrapup

:budget_8k
set "BUDGET_TOKENS=8192"
set "BUDGET_NAME=8K [8192 tokens]"
goto :select_wrapup

:budget_16k
set "BUDGET_TOKENS=16384"
set "BUDGET_NAME=16K [16384 tokens]"
goto :select_wrapup

:budget_32k
set "BUDGET_TOKENS=32768"
set "BUDGET_NAME=32K [32768 tokens]"
goto :select_wrapup

:budget_48k
set "BUDGET_TOKENS=49152"
set "BUDGET_NAME=48K [49152 tokens]"
goto :select_wrapup

:budget_64k
set "BUDGET_TOKENS=65536"
set "BUDGET_NAME=64K [65536 tokens]"
goto :select_wrapup

:budget_custom
set /p USER_K="Enter thinking budget in K (e.g. 24 for 24K, 80 for 80K): "
set /a BUDGET_TOKENS=USER_K * 1024
if %BUDGET_TOKENS% LEQ 0 (
    echo Invalid input, fallback to 16K [16384 tokens]...
    set "BUDGET_TOKENS=16384"
    set "BUDGET_NAME=16K [16384 tokens]"
) else (
    set "BUDGET_NAME=%USER_K%K [%BUDGET_TOKENS% tokens]"
)
goto :select_wrapup

:select_wrapup
echo.
echo ===============================================================================
echo   [3/3] Select Thinking Wrap-up Style (截断闭合模式与注入信号): [Wrap-up]
echo ===============================================================================
echo.
echo   [1] Original Impersonation - 原汁原味第一人称伪装 [Original]
echo       -------------------------------------------------------------------------
echo       [EN] "\\n\\nI have thought about this long enough; time to give my answer.\\n^</think^>\\n\\n"
echo       [CN] 拟态第一人称催眠：假装模型自己说「我已经想得够久了，该给答案了」，促使
echo            模型结束思考并直接作答。[Original Impersonation]
echo       -------------------------------------------------------------------------
echo.
echo   [2] Objective System Notice - 客观系统提示闭合 [System Notice] [Recommended for 1-4]
echo       -------------------------------------------------------------------------
echo       [EN] "\\n\\n[System: Thinking budget reached. Conclude reasoning immediately
echo             and deliver the response based on current analysis.]\\n^</think^>\\n\\n"
echo       [CN] 客观系统通知：明确以第三方系统身份告知预算已达上限，指令模型立即收尾并
echo            基于当前分析输出最终代码与结果。[Objective Notice]
echo       -------------------------------------------------------------------------
echo.
echo   [3] Staged Thinking Nudge - 阶段思维敲打通知 (接力续思) [Paired with Mode 5]
echo       -------------------------------------------------------------------------
echo       [EN] "\\n\\n[Thinking Nudge: Stage budget reached. Resume reasoning until
echo             natural closure.]\\n^</think^>\\n\\n"
echo       [CN] 阶段思维敲打纯信号（配对 Mode 5）：告知阶段预算截断，严禁仓促交差代码，促使
echo            模型保存当前进度快照并在下一轮中接力继续深入推演，直到自然成熟收敛。[Staged Nudge]
echo       -------------------------------------------------------------------------
echo ===============================================================================
choice /c 123 /m "Select wrap-up style [1, 2, 3] (Recommended: 2 for Mode 1-4, 3 for Mode 5): "
if errorlevel 3 goto :wrapup_nudge
if errorlevel 2 goto :wrapup_system
if errorlevel 1 goto :wrapup_orig

:wrapup_orig
set "WRAP_UP_ARG=original"
set "WRAP_UP_NAME=Original Impersonation (I have thought long enough...)"
goto :start_server

:wrapup_system
set "WRAP_UP_ARG=system"
set "WRAP_UP_NAME=Objective System Notice ([System: Thinking budget reached...])"
goto :start_server

:wrapup_nudge
set "WRAP_UP_ARG=nudge"
set "WRAP_UP_NAME=Staged Thinking Nudge ([Thinking Nudge: Stage budget reached...])"
goto :start_server

:start_server
echo.
echo ===============================================================================
echo   Reasoning Effort: %EFFORT%
echo   Thinking Budget : %BUDGET_NAME%
echo   Wrap-up Style   : %WRAP_UP_NAME%
echo   Launching Strata Engine...
echo ===============================================================================
"D:\\Strata\\.venv\\Scripts\\python.exe" "D:\\Strata\\serve\\server.py" --engine strata --config "D:\\Strata\\strata-coder-iq1_m-ultra.json" --reasoning-budget-tokens %BUDGET_TOKENS% --reasoning-effort %EFFORT% --reasoning-wrap-up %WRAP_UP_ARG% --port 8080 --open
taskkill /F /IM strata.exe >nul 2>&1
taskkill /F /IM strata-vision.exe >nul 2>&1
if errorlevel 1 pause
"""

lines = bat_content.strip().splitlines()
processed = []
for line in lines:
    if line and ord(line[-1]) > 127:
        line += " "
    processed.append(line)

crlf_content = "\r\n".join(processed) + "\r\n"
with open("D:/Strata/run-coder-iq1_m-ultra.bat", "wb") as f:
    f.write(crlf_content.encode("utf-8"))
print("Successfully generated D:/Strata/run-coder-iq1_m-ultra.bat with CRLF and ASCII line-ending safeguards!")

