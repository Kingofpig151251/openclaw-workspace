# MEMORY.md - Thoth 長期記憶

## 👤 關於小king
- 準備上學（UWE），但仍會面試保持競爭力
- 不喜歡一口氣收到大量文字，偏好即時短回覆
- 天氣報告要報香港的
- 想知道任務進度，不想每次主動提我跑 lint
- 說「先放下」時是真的想暫停，不是客氣
- 明文密碼可以放在 Wiki.js，不需要去敏
- 不喜歡看到 exec 誤報訊息（`⚠️ 🛠️ Exec failed`），之後一律避免

## 🏛️ 我的身份
- 名字：Thoth（托特），埃及智慧之神
- 曾用名：小龍蝦 🦞（小king 賜名）
- 升級日期：2026-07-26


## 🏠 小king 的 Home 目錄
- `/vol1/1000/` = 小king 的 home directory
- GitHub repos 放 `/vol1/1000/Github/`

## 🖥️ NAS 環境（ITD-NAS）
- 系統：Debian 12 + 飛牛 fnOS
- CPU：i5-10505 @ 3.2GHz（6核12線程）
- 記憶體：16GB
- IP：192.168.1.50
- 管理員帳號：lam151251
- sudo root ✅（/etc/sudoers.d/trim-openclaw, NOPASSWD）
- trim-cli 管理員 ✅

## 📊 Grafana 監控系統
- **Grafana** (Docker, host網路, :3000) — 登入 lam151251 / Lam@963852
- **Prometheus** (:9090) — 180天保留，1355指標
- **Node Exporter** (:9100) — 系統指標，wrapper 加 --no-collector.thermal_zone
- **Loki** (:3100) — 日誌，30天保留（compactor 自動清理）
- **Alloy** (:12345) — 日誌收集→Loki
- **Pushgateway** (Docker, :9091) — OpenClaw自定義指標推送
- **Webhook接收器** (:15010) — Grafana告警→Redis→微信推送
- Dashboard 結構：📁 Infrastructure（Node Exporter Full + NAS 日誌）、📁 OpenClaw（OpenClaw 監控）
- 告警規則：OpenClawDataStale(>10min)、XfyunAPIDown、WikiHitRateLow(<70%)
- 告警鏈路：Grafana→Webhook:15010→Redis DB1→push_metrics.py→心跳檢查→微信
- Cron: push_metrics.py 每5分鐘，webhook @reboot 自啟
- 數據源UID: Loki=`P8E80F9AEF21F6940`，Prometheus=`cftjkd0m8y29sa`
- ⚠️ Loki 查詢用 `hostname`/`filename` 標籤，不是 `job`

## 🔧 工具與服務
- **Ollama**：`/vol1/@appcenter/ai_installer/ollama/bin/ollama`，端口 11434
  - nomic-embed-text（記憶搜索 embedding）
  - qwen2.5:3b（fallback only，1.9GB）
  - ⚠️ 7B 已刪除，省 4.7GB
- **SearXNG**：localhost:8080（Docker host 網路，接 Redis 快取）
  - 引擎：Google, Bing, DDG, Wikipedia, Wikidata, GitHub, StackOverflow, Reddit, arxiv, DDG Images, Wikimedia Commons
  - 語言：auto（自動偵測查詢語言）
  - 分類：general,news,science
- **Redis 8.2.1**：localhost:6379
  - DB0：SearXNG 快取
  - DB1：Task Guard（去重/限流/狀態追蹤）
  - maxmemory 256MB + allkeys-lru
- **Task Guard**：`scripts/redis_task_guard.py` + `scripts/heartbeat_guard.py`
  - 去重、限流、狀態追蹤、計數器
  - 心跳 benchmark 5分鐘去重 + 24h 快取
- **Python venv**：`.venv`（Whisper v20250625 + Pillow v12.3.0 + redis 8.0.1）
- **ffmpeg**：已有二進制

## 📧 郵件歸檔系統（已停用）
- agently-cli 已被小king 刪除（2026-07-31），不再使用
- 歷史架構：agent.qq.com → agently-cli → Maildir → Dovecot IMAP → Roundcube :8680
- 同步腳本：`/vol1/@apphome/mail-archive/mail-sync.py`（已停用）

## 📚 知識庫
- **king-wiki-js**（GitHub）= 小king 私人知識庫，我負責維護
- **Wiki.js**（Docker, :18181）= 公司 IT 知識庫，42頁已遷入
- ⚠️ 兩個 Wiki 別搞混！
- 搜尋命中率已達 100%，交叉引用密度 6.16，合規率 100%
- 維護規範：`_internal/WIKI-SCHEMA.md`，矛盾追蹤：`_internal/contradictions.md`

## 🔄 Git 自動備份
- Repo: `github.com/Kingofpig151251/openclaw-workspace`（私有）
- 備份腳本：`scripts/git_backup.sh`
- 排除：.venv、king-wiki-js（獨立 repo）、.openclaw 內部狀態
- 深夜流水線 Phase 3 自動執行

## 🧠 Self-Improving Agent
- 安裝 @pskoett/self-improving-agent v4.0.1
- .learnings/ 目錄：LEARNINGS.md / ERRORS.md / FEATURE_REQUESTS.md
- Hook 已啟用（🧠 self-improvement）

## 🎮 Discord 多用戶管理
- 伺服器 ID：1531560409499172865
- Bot ID：1528998891092181023
- Bot 已有 Administrator 權限（小king 已設定，2026-07-31）
- Member role ID：1532656209306587238（藍色，基本權限）
- @everyone role ID：1531560409499172865
- 小king Discord ID：501559258492698637
- 頻道 ID：
  - 📋 資訊 category: 1532645465076662286
  - 👤 成員頻道 category: 1532645559796760746
  - 💬 公共 category: 1532645561675813075
  - 📁 項目 category: 1532669169387044904
  - #資訊公告: 1532645497960005703（唯讀）
  - #小king: 1532647352832102532（私有）
  - #閒聊: 1532645563701395608
  - #求助: 1532645565668786277
  - #項目申請: 1532661512278249482
- 管理規範：`discord-management.md`
- 成員清單：`memory/discord-members.json`
- 項目清單：`memory/discord-projects.json`
- 審計日誌：`memory/discord-audit.log`
- Discord API 需用 `DiscordBot` User-Agent，Python urllib 會被 Cloudflare 1010
- 成員：小king（admin, UID 1000）+ zeronosu（member, UID 1002）
- 項目頻道命名：直接用項目名，不加 project- 前綴
- 記憶隔離：目前靠自律，未來需技術隔離
- NAS 操作前必須先 trim-cli login，不假設 token 有效
- 密碼安全：隨機臨時密碼，只發私人頻道，不記錄明文

- GitHub 2FA：thoth151251-bot 帳號需在 2026-09-10 前啟用
- Wiki 超大頁面：shenzhen-itinerary(129行)、sp-ambassadors-sharing(122行)、side-by-side(103行) 考慮拆分
- 重啟 Gateway 使 contextWindow 512k 生效
- 飛牛瀏覽器從 UI 卸載
- 告警微信推送實際觸發測試
- Webhook @reboot 自啟機制

## ⚠️ 重要教訓
- sudoers.d 文件名不能有 `.`，權限必須 440
- Docker volume 改密碼後必須刪除重建
- 新建 wiki 頁面必須同步更新導航頁
- cron 環境變量極度精簡，PATH 和 HOME 都要手動設
- 訊飛星火 token 計數不可靠
- sudo 寫入 openclaw.json 會改變文件權限，需 chown 992:992 修復
- ⚠️ 飛牛更新可能覆蓋 Node Exporter wrapper
- **不要 kill openclaw-gateway 進程！** 需重啟找小king
- shell 命令預期可能無結果時加 `|| true`，避免誤報
- 用戶群組變更不影響已運行進程，需 `sg` 或新 session
- `chown` 會覆蓋群組寫權限，需配套 `chmod -R g+w`

## 🔑 配置要點
- 訊飛星火 Coding Plan 免費，成本=0，不需追蹤 estimatedCostUsd
- 訊飛星火 timeoutSeconds: 900，agent timeoutSeconds: 900，compaction timeoutSeconds: 900
- 主力模型：`讯飞星火/xopglm52`（智譜 GLM-5.2），fallback: `讯飞星火/astron-code-latest`
- contextWindow: 512000（已生效），reserveTokensFloor: 20000
- 訊飛星火 token 計數不可靠，API 回報值波動極大
- xopglm52 實測支持 560k context，1M 超時
- **訊飛適配計劃統一記錄：`xfyun-adaptation-plan.md`**
- 微信 streaming mode: block（不支援 edit message）
- 記憶搜索：Ollama nomic-embed-text
- messages.suppressToolErrors: true（頂層）
- auth.cooldowns: overloadedProfileRotations=3, overloadedBackoffMs=5000, rateLimitedProfileRotations=3
- SearXNG 端口：8080（host 網路模式，非 8888）
- Redis: DB0=SearXNG, DB1=TaskGuard, maxmemory 256MB+LRU

## 🗓️ 小king 的學業
- UWE 課程：Sem1 CGD / Sem2 Interaction Design / Sem3 Creative Tech Project / Sem4 3D Modelling
- 補底班：8月超密集（12堂 + Induction + CGD正式課4堂）
- Google Calendar 已整合課程時間表

## 🕐 Cron 排程
- 01:00 每天：深夜維護流水線（Wiki審查→記憶整理→Git Backup）
- 07:00 每天：早安報告（天氣+郵件）
- 深夜流水線 timeout: 1800s，model: 訊飛星火/astron-code-latest
- ⚠️ 同一時段不要多個任務同時跑，會搶配額
