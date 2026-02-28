@echo off
echo Starting FidelioPro FastAPI Server...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
echo Checking dependencies...
pip install -r requirements.txt

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache

REM Start the application
echo.
echo Starting server...
echo Press Ctrl+C to stop the server
echo.
start "Fidelio.pro webserver" python run.py

pause