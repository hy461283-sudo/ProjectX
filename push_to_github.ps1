# Push ProjectX to GitHub
# Repository: https://github.com/hy461283-sudo/ProjectX.git

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ProjectX - Push to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
$gitPath = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitPath) {
    Write-Host "ERROR: Git is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Git found! Proceeding with push..." -ForegroundColor Green
Write-Host ""

# Initialize git if needed
if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
    git remote add origin https://github.com/hy461283-sudo/ProjectX.git
} else {
    Write-Host "Repository already initialized." -ForegroundColor Green
    # Update remote URL to make sure it's correct
    git remote set-url origin https://github.com/hy461283-sudo/ProjectX.git 2>$null
    if ($LASTEXITCODE -ne 0) {
        git remote add origin https://github.com/hy461283-sudo/ProjectX.git
    }
}

Write-Host ""
Write-Host "Staging all changes..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "Committing changes..." -ForegroundColor Yellow
git commit -m "Implement non-destructive resource management

- Replace kill/restart actions with throttling and logging
- Add CPU priority throttling instead of killing processes
- Add memory/service/updates logging with recommendations
- Add recommendations table and API endpoints
- Fix Chrome whitelist (chrome.exe)
- Add comprehensive README.md"

if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git branch -M main
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "SUCCESS! Code pushed to GitHub" -ForegroundColor Green
        Write-Host "Repository: https://github.com/hy461283-sudo/ProjectX" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "ERROR: Push failed!" -ForegroundColor Red
        Write-Host "This might be due to:" -ForegroundColor Yellow
        Write-Host "1. Authentication required - you may need to enter credentials" -ForegroundColor Yellow
        Write-Host "2. Network issues" -ForegroundColor Yellow
        Write-Host "3. Repository permissions" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Try running manually:" -ForegroundColor Yellow
        Write-Host "  git push -u origin main" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "No changes to commit or commit failed." -ForegroundColor Yellow
    Write-Host "Trying to push anyway..." -ForegroundColor Yellow
    git branch -M main
    git push -u origin main
}

Write-Host ""
Read-Host "Press Enter to exit"
