# TrustLens Deployment Script - Fixed
# Token should be passed via environment variable, not stored here
$username = "AUSTIN-JR"
$email = "austin@trustlens.dev"
$repoName = "trustlens"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TrustLens Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Configure Git
Write-Host "Step 1: Configuring Git..." -ForegroundColor Yellow
git config --global user.name $username
git config --global user.email $email
Write-Host "OK - Git configured" -ForegroundColor Green

# Step 2: Initialize Git repo if not already done
Write-Host "Step 2: Initializing Git repository..." -ForegroundColor Yellow
if (-not (Test-Path .git)) {
    git init
    Write-Host "OK - Git repository initialized" -ForegroundColor Green
}
else {
    Write-Host "OK - Git repository already exists" -ForegroundColor Green
}

# Step 3: Add all files
Write-Host "Step 3: Staging files..." -ForegroundColor Yellow
git add .
Write-Host "OK - Files staged" -ForegroundColor Green

# Step 4: Create initial commit if needed
Write-Host "Step 4: Creating commit..." -ForegroundColor Yellow
git commit -m "TrustLens: Tamper-detection system for CV pipelines - Ready for deployment"
Write-Host "OK - Commit created" -ForegroundColor Green

# Step 5: Set branch to main
Write-Host "Step 5: Setting branch to main..." -ForegroundColor Yellow
git branch -M main
Write-Host "OK - Branch set to main" -ForegroundColor Green

# Step 6: Add remote with token
Write-Host "Step 6: Adding GitHub remote..." -ForegroundColor Yellow
$remoteUrl = "https://$($token)@github.com/$($username)/$($repoName).git"
git remote remove origin 2>$null
git remote add origin $remoteUrl
Write-Host "OK - Remote added" -ForegroundColor Green

# Step 7: Push to GitHub
Write-Host "Step 7: Pushing to GitHub..." -ForegroundColor Yellow
git push -u origin main --force
Write-Host "OK - Code pushed to GitHub!" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your repository is at:" -ForegroundColor Cyan
Write-Host "https://github.com/$username/$repoName" -ForegroundColor White
Write-Host ""
