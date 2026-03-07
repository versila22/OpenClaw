#!/bin/bash
# Backup OpenClaw context
DATE=$(date +"%Y-%m-%d")

echo "[Backup] Starting daily backup for $DATE..."

cd /data/.openclaw/workspace || exit 1

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "[Backup] Git repo not found. Skipping."
    exit 1
fi

# Add changes
git add .

# Commit only if changes exist
if ! git diff-index --quiet HEAD --; then
    git commit -m "chore: auto-backup $DATE"
    echo "[Backup] Committed changes."
    
    # Try to push (requires ssh/https auth setup)
    if git remote get-url origin > /dev/null 2>&1; then
        git push origin main
        echo "[Backup] Pushed to remote."
    else
        echo "[Backup] No remote 'origin' configured. Skipping push."
    fi
else
    echo "[Backup] No changes to commit."
fi
