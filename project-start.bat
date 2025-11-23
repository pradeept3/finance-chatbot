@echo off
REM Set the directories for frontend and backend (update these paths)
REM If you didn't customize the absolute paths, default to "frontend" and "backend" subfolders next to this script.
set "SCRIPT_DIR=%~dp0"
if "%FRONTEND_DIR%"=="" set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
REM Do not auto-relaunch under cmd: running the batch from PowerShell (including VSCode integrated terminal)
REM is supported and automatic relaunch can cause recursion or unexpected behavior.
REM If you specifically want to run under cmd.exe, launch this script from a cmd prompt.
  exit /b
)

REM Determine run mode:
REM  - pass "vscode" as the first argument to force integrated-terminal behavior
REM  - pass "external" to force new console windows (default)
set "MODE="
if /I "%~1"=="vscode" set "MODE=vscode"
if /I "%~1"=="external" set "MODE=external"
if "%MODE%"=="" (
  if defined VSCODE_PID (
	set "MODE=vscode"
  ) else (
	set "MODE=external"
  )
)

REM Validate directories
if not exist "%BACKEND_DIR%" (
  echo Backend directory "%BACKEND_DIR%" does not exist.
  pause
  exit /b 1
)
if not exist "%FRONTEND_DIR%" (
  echo Frontend directory "%FRONTEND_DIR%" does not exist.
  pause
  exit /b 1
)

REM Launch based on detected mode
if /I "%MODE%"=="external" (
  REM Start the backend Python application in a new terminal (external window)
  start "Backend" cmd /k "pushd \"%BACKEND_DIR%\" && python app.py"

  REM Start the frontend (Streamlit) app in a new terminal (external window)
  start "Frontend" cmd /k "pushd \"%FRONTEND_DIR%\" && streamlit run streamlit_app.py"
) else (
  REM VSCode integrated terminal or other terminal: start processes without creating new windows
  REM They will run in the same console (use /B to avoid new window); output will mix in the terminal.
  start "" /B cmd /k "pushd \"%BACKEND_DIR%\" && python app.py"
  start "" /B cmd /k "pushd \"%FRONTEND_DIR%\" && streamlit run streamlit_app.py"
)

REM Wait a few seconds for the servers to start, then open the frontend in the default browser
timeout /t 5 /nobreak >nul
start "" "http://localhost:8501"

exit /b