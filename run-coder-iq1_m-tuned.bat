@echo off
title Strata Qwen3.8 Coder IQ1_M - 256K Tuned (High Performance)
cd /d "D:\Strata"
"D:\Strata\.venv\Scripts\python.exe" "D:\Strata\serve\server.py" "--engine" "strata" "--config" "D:\Strata\strata-coder-iq1_m-tuned.json" "--port" "8080" "--open"
if errorlevel 1 pause
