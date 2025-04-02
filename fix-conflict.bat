@echo off
echo Fixing Python package conflicts and installation paths...

REM Check if the aishell directory exists
if not exist aishell (
    echo ERROR: The aishell directory was not found.
    echo Make sure you're running this from the AI Shell installation directory.
    echo The correct directory structure should have an 'aishell' subfolder containing 'ai_shell.py'.
    pause
    exit /b 1
)

REM Check if the Python script exists
if not exist aishell\ai_shell.py (
    echo ERROR: ai_shell.py not found in the aishell subdirectory.
    echo Make sure you have the complete project with all required files.
    pause
    exit /b 1
)

REM Try to uninstall the conflicting Python package
for %%C in (py python python3) do (
    echo Checking Python command: %%C
    %%C --version >nul 2>&1
    if not errorlevel 1 (
        echo Using Python command: %%C to uninstall conflicts
        %%C -m pip uninstall -y aishell 2>nul
    )
)

echo Removing any global npm installations...
call npm uninstall -g aishell 2>nul
call npm uninstall -g ai-shell 2>nul

echo Installing AI Shell with the correct name and path...
call npm install -g .

echo.
echo Installation complete!
echo You should now be able to use the 'ai-shell' command (with hyphen).
echo.
echo If you still have issues, try the direct-run.bat script.
pause
