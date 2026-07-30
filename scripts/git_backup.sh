#!/bin/bash
# Thoth workspace auto-backup to GitHub
cd /vol1/@apphome/trim.openclaw/data/workspace || exit 1

# Add all changes
git add -A

# Check if there's anything to commit
if git diff --cached --quiet; then
    echo "No changes to backup"
    exit 0
fi

# Commit with timestamp
git commit -m "🏛️ auto-backup $(date '+%Y-%m-%d %H:%M')"

# Push
git push origin main 2>&1
echo "✅ Backup done"
