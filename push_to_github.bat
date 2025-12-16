@echo off
REM Push ProjectX to GitHub
REM Repository: https://github.com/hy461283-sudo/ProjectX.git

echo ========================================
echo ProjectX - Push to GitHub
echo ========================================
echo.

REM Check if git is installed
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo After installation, restart this script.
    pause
    exit /b 1
)

echo Git found! Proceeding with push...
echo.

REM Initialize git if needed
if not exist .git (
    echo Initializing git repository...
    git init
    git remote add origin https://github.com/hy461283-sudo/ProjectX.git
) else (
    echo Repository already initialized.
    REM Update remote URL to make sure it's correct
    git remote set-url origin https://github.com/hy461283-sudo/ProjectX.git 2>nul
    if %ERRORLEVEL% NEQ 0 (
        git remote add origin https://github.com/hy461283-sudo/ProjectX.git
    )
)

echo.
echo Staging all changes...
git add .

echo.
echo Committing changes...
git commit -m "Implement non-destructive resource management - Replace kill/restart actions with throttling and logging - Add CPU priority throttling instead of killing processes - Add memory/service/updates logging with recommendations - Add recommendations table and API endpoints - Fix Chrome whitelist (chrome.exe) - Add comprehensive README.md"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Pushing to GitHub...
    git branch -M main
    git push -u origin main
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo ========================================
        echo SUCCESS! Code pushed to GitHub
        echo Repository: https://github.com/hy461283-sudo/ProjectX
        echo ========================================
    ) else (
        echo.
        echo ERROR: Push failed!
        echo This might be due to:
        echo 1. Authentication required - you may need to enter credentials
        echo 2. Network issues
        echo 3. Repository permissions
        echo.
        echo Try running manually:
        echo   git push -u origin main
    )
) else (
    echo.
    echo No changes to commit or commit failed.
    echo Trying to push anyway...
    git branch -M main
    git push -u origin main
)

echo.
pause
