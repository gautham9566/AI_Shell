@echo off
echo Installing AI Shell...

rem Check if Python is installed - try multiple commands
set PYTHON_CMD=
for %%C in (py python python3) do (
    %%C --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=%%C
        echo Found Python command: %%C
        goto python_found
    )
)

:python_not_found
echo Python is not installed or not in your PATH.
echo Please install Python from https://www.python.org/downloads/
exit /b 1

:python_found
rem Create requirements.txt if it doesn't exist
if not exist requirements.txt (
    echo Creating minimal requirements.txt...
    echo requests > requirements.txt
)

rem Install Python dependencies
echo Installing Python dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt

rem Create the batch file launcher
echo Creating launcher script...
mkdir bin 2>nul
echo @echo off > bin\ai-shell.bat
echo %PYTHON_CMD% "%%~dp0\..\aishell\ai_shell.py" %%* >> bin\ai-shell.bat

rem Add to PATH if requested
echo.
echo AI Shell has been installed successfully!
echo.
echo To run AI Shell, you can:
echo 1. Type 'bin\ai-shell' from this directory
echo 2. Add this directory's bin folder to your PATH to run 'ai-shell' from anywhere
echo.
echo Would you like to add AI Shell to your PATH? (y/n)
set /p choice=
if /i "%choice%"=="y" (
    echo Adding to PATH...
    for /f "tokens=2*" %%a in ('reg query HKCU\Environment /v PATH') do set CURRENT_PATH=%%b
    if defined CURRENT_PATH (
        setx PATH "%CURRENT_PATH%;%CD%\bin"
    ) else (
        setx PATH "%CD%\bin"
    )
    echo AI Shell has been added to your PATH. You may need to restart your terminal.
)

echo.
echo Installation complete! Type 'ai-shell' to start (may require reopening your terminal).
