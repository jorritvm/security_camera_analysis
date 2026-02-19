@echo off
REM Daily workflow batch file for Windows Task Scheduler
REM This script activates the UV virtual environment and runs the daily workflow

cd /d "%~dp0"
echo Project root: %CD%

REM Change to src_processing folder and run the workflow
cd src_processing
echo Working directory: %CD%

REM Activate UV virtual environment and run the workflow
uv run --directory .. python main_daily_workflow.py

echo.
echo Workflow completed at %date% %time%

