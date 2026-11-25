@echo off
echo ===================================================================
echo     Fortive AI - Autonomous AI Sales Voice Agent MVP
echo ===================================================================
echo.
echo [1/3] Checking Python and dependencies...
python -m pip install -r backend\requirements.txt --quiet
echo.
echo [2/3] Seeding MongoDB with initial pipeline data...
python scripts\seed_data.py
echo.
echo [3/3] Starting Unified Voice Agent Server on http://localhost:8000 ...
echo.
echo Opening browser cockpit at http://localhost:8000
start http://localhost:8000
echo.
python backend\run.py
pause
