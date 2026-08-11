@echo off
REM JobIntel - daily pipeline. Runs fetch -> dedup -> extract -> normalize.
cd /d "C:\Users\Arifi\Desktop\jobHunter\backend"
set PYTHONUTF8=1
C:\Users\Arifi\.local\bin\uv.exe run python -m scripts.run_pipeline --step all --source all >> "C:\Users\Arifi\Desktop\jobHunter\backend\data\pipeline_daily.log" 2>&1
