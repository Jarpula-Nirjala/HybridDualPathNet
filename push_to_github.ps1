# Push HybridDualNetPath to GitHub as Jarpula-Nirjala
#
# TOKEN REQUIREMENTS (fine-grained PAT):
#   Repository access: HybridDualNetPath (or All repositories)
#   Permissions -> Repository permissions -> Contents: Read and write
#   Permissions -> Metadata: Read-only (auto)
#
# OR use Classic PAT with scope: repo
#
# Create token: https://github.com/settings/tokens
#
# Usage:
#   $env:GITHUB_TOKEN = "github_pat_xxxx"   # or ghp_xxxx for classic
#   .\push_to_github.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $env:GITHUB_TOKEN) {
    Write-Host "Set token first: `$env:GITHUB_TOKEN = 'your_token'" -ForegroundColor Yellow
    exit 1
}

$env:GH_TOKEN = $env:GITHUB_TOKEN
$remote = "https://x-access-token:$($env:GITHUB_TOKEN)@github.com/Jarpula-Nirjala/HybridDualNetPath.git"

Write-Host "Testing Contents write permission..." -ForegroundColor Cyan
$test = gh api repos/Jarpula-Nirjala/HybridDualNetPath 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Token invalid." -ForegroundColor Red; exit 1 }

git -c credential.helper= push $remote main
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: https://github.com/Jarpula-Nirjala/HybridDualNetPath" -ForegroundColor Green
    git log -1 --format="Author: %an <%ae>"
} else {
    Write-Host "Push failed. Token needs Contents: Read and write on HybridDualNetPath." -ForegroundColor Red
    Write-Host "https://github.com/settings/tokens -> edit token -> Repository permissions -> Contents" -ForegroundColor Yellow
    exit 1
}
