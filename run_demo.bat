@echo off
REM Run from this file's folder so relative paths work after double-clicking.
cd /d "%~dp0"
REM Reset demo data, start FastAPI and Streamlit, then open the browser.
python scripts\run_demo.py --reset-db --open
pause
