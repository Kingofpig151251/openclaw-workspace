#!/bin/bash
# SonarCloud 自動修復腳本
# 每天凌晨 3 點由 cron 觸發
# 按 severity 從高到低修復，修完一批就 commit + push

set -euo pipefail

export PATH=/vol1/@appcenter/nodejs_v24/bin:/usr/local/bin:/usr/bin:/bin
export HOME=/vol1/@apphome/trim.openclaw/data/home

PROJECT_DIR="/vol1/1000/projects/fitness-coach-app"
SONAR_TOKEN="9de88a070ea552b6b5ded5efeaaac89cd7f77027"
SONAR_API="https://sonarcloud.io/api"

cd "$PROJECT_DIR"

# 確保權限
sudo chmod -R go+rwX "$PROJECT_DIR" 2>/dev/null || true

# 拉最新代碼
git fetch origin
git checkout dev
git pull origin dev

# 查詢未解決的 issues
echo "[SonarBot] Fetching open issues..."
ISSUES=$(curl -s -u "$SONAR_TOKEN:" "$SONAR_API/issues/search?componentKeys=Section-Nexus_fitness-coach-app&ps=500&resolved=false&facets=severities,types")

# 統計
TOTAL=$(echo "$ISSUES" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total',0))")
echo "[SonarBot] Total open issues: $TOTAL"

# 輸出摘要到文件供 OpenClaw session 讀取
echo "$ISSUES" | python3 -c "
import sys, json
data = json.load(sys.stdin)
issues = data.get('issues', [])
by_sev = {}
for i in issues:
    sev = i.get('severity', '?')
    by_sev.setdefault(sev, []).append(i)
for sev in ['BLOCKER', 'CRITICAL', 'MAJOR', 'MINOR', 'INFO']:
    items = by_sev.get(sev, [])
    if items:
        print(f'{sev}: {len(items)}')
        for i in items[:5]:
            comp = i.get('component', '').split(':')[-1]
            line = i.get('line', '?')
            rule = i.get('rule', '?')
            msg = i.get('message', '')[:100]
            print(f'  {comp}:{line} [{rule}] {msg}')
        if len(items) > 5:
            print(f'  ... and {len(items)-5} more')
" > /tmp/sonar-summary.txt

cat /tmp/sonar-summary.txt

echo "[SonarBot] Done. OpenClaw will process these issues."
