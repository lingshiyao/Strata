@echo off
title Strata Qwen3.8 Coder IQ1_M - 256K Ultra (High Performance Multimodal)
cd /d "D:\Strata"

REM 1. Enable Coupled Stochastic Speculative Drafting (Syncs MTP RNG & distribution with Hermes temperature sampling)
set STRATA_SPEC_COUPLED=1

REM 2. Activate Windows High Performance Power Scheme (Prevents Arrow Lake Ring Bus / DDR5 downclocking)
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1

REM 3. Launch Strata Engine with Ultra Configuration
"D:\Strata\.venv\Scripts\python.exe" "D:\Strata\serve\server.py" "--engine" "strata" "--config" "D:\Strata\strata-coder-iq1_m-ultra.json" "--port" "8080" "--open"
if errorlevel 1 pause
