@echo off
echo Checking virtual environment...

:: Check if venv exists, create it if missing
if not exist venv (
    echo [INFO] Virtual environment 'venv' not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

:: Activate venv
echo Activating virtual environment...
call venv\Scripts\activate

if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)

echo Virtual environment activated!

:: Install dependencies if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        exit /b 1
    )
)

:: Run the Streamlit app
echo Starting Streamlit application...
streamlit run dashboard.py

:: Pause to keep terminal open
pause
