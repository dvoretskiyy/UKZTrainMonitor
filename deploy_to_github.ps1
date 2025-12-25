# Переконайтеся що конфіденційні файли не будуть закомічені
Write-Host "Checking for sensitive files..." -ForegroundColor Yellow

# Перевірка .gitignore
if (-not (Test-Path ".gitignore")) {
    Write-Host "ERROR: .gitignore not found!" -ForegroundColor Red
    exit 1
}

# Перевірка що .env не буде закомічений
$gitStatus = git status --porcelain
if ($gitStatus -match "\.env$") {
    Write-Host "ERROR: .env file is staged! It should be ignored." -ForegroundColor Red
    exit 1
}

# Перевірка session файлів
if ($gitStatus -match "\.session") {
    Write-Host "ERROR: Session files are staged! They should be ignored." -ForegroundColor Red
    exit 1
}

# Перевірка що .env.example існує
if (-not (Test-Path ".env.example")) {
    Write-Host "ERROR: .env.example not found! Create it first." -ForegroundColor Red
    exit 1
}

Write-Host "✓ All checks passed!" -ForegroundColor Green
Write-Host ""

# Git команди
Write-Host "Initializing git repository..." -ForegroundColor Cyan
git init

Write-Host "Adding remote..." -ForegroundColor Cyan
git remote add origin https://github.com/dvoretskiyy/UKZTrainMonitor.git

Write-Host "Adding files..." -ForegroundColor Cyan
git add .

Write-Host "Creating commit..." -ForegroundColor Cyan
git commit -m "Initial commit: UKZ Train Monitor Bot with Pyrogram voice calls"

Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

Write-Host ""
Write-Host "✓ Successfully pushed to GitHub!" -ForegroundColor Green
Write-Host "Repository: https://github.com/dvoretskiyy/UKZTrainMonitor" -ForegroundColor Cyan
