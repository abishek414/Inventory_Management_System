cd $PSScriptRoot

Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force
Write-Host "Removed all __pycache__ folders."

if (Test-Path "static\.gitkeep") {
    Remove-Item "static\.gitkeep"
    Write-Host "Removed static\.gitkeep (no longer needed - static\css\custom.css already exists)."
}

git rm -r --cached --ignore-unmatch accounts/__pycache__ accounts/migrations/__pycache__ config/__pycache__ inventory/__pycache__ inventory/migrations/__pycache__ organizations/__pycache__ organizations/migrations/__pycache__ | Out-Null
git rm --cached --ignore-unmatch static/.gitkeep | Out-Null
Write-Host "Untracked any of the above from git, if they were ever committed (safe no-op otherwise)."

Write-Host ""
Write-Host "Done. Run 'git status' to see what changed before committing."
