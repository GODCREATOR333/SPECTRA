@echo off
TITLE Laser Steering HIL Simulation
CLS

echo ===============================================================================
echo  LASER TRACKING SIMULATION - AUTO SETUP
echo ===============================================================================

REM 1. CHECK FOR PYTHON
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.10 or newer.
    echo Quickest way: Open Microsoft Store and search for "Python 3.10"
    echo.
    PAUSE
    EXIT /B
)

REM 2. SETUP VIRTUAL ENVIRONMENT (Keeps things clean)
IF NOT EXIST "venv" (
    echo [INFO] Creating Virtual Environment (First run only)...
    python -m venv venv
    
    echo [INFO] Upgrading pip...
    call venv\Scripts\python -m pip install --upgrade pip
    
    echo [INFO] Installing Dependencies (This may take a few minutes)...
    call venv\Scripts\pip install -r requirements.txt
    
    echo [SUCCESS] Installation Complete.
) ELSE (
    echo [INFO] Virtual Environment found. Skipping install.
)

REM 3. CHECK FOR PS3 EYE DRIVER
echo.
echo [IMPORTANT] Ensure "CL-Eye Platform Driver" is installed!
echo If the camera is black, install the .exe inside the 'drivers' folder.
echo.

REM 4. RUN THE SIMULATION
echo [INFO] Launching Simulation...
echo.
call venv\Scripts\python src/Scanner_Sim_py/Run_Simulation/run_simulation.py

PAUSE
