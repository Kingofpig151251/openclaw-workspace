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
- **PostgreSQL 16**（Docker, :5433）— Thoth 自用結構化數據
  - 配置：`/vol1/@apphome/trim.openclaw/docker/postgres/docker-compose.yml`
  - 數據：`/vol1/@apphome/trim.openclaw/docker/postgres/data/`
  - 用戶：thoth / Thoth@963852
  - 表：discord_members, discord_projects, discord_project_members, mail_classifications
- **Redis 8.2.1**：localhost:6379
  - DB0：SearXNG 快取
  - DB1：Task Guard（去重/限流/狀態追蹤）
  - maxmemory 256MB + allkeys-lru
- **Task Guard**：`scripts/redis_task_guard.py` + `scripts/heartbeat_guard.py`
  - 去重、限流、狀態追蹤、計數器
  - 心跳 benchmark 5分鐘去重 + 24h 快取
- **Python venv**：`.venv`（Whisper v20250625 + Pillow v12.3.0 + redis 8.0.1）
- **ffmpeg**：已有二進制

## 🏋️ fitness-coach-app
- 位置：`/vol1/1000/Github/fitness-coach-app/`
- Docker 部署：3 容器（PostgreSQL + Fastify :4000 + Nginx :18888）
- 訪問地址：`http://192.168.1.50:18888`
- 2026-07-31 大規模瘦身：22 commits，淨刪 ~6,623 行
- 2026-08-01~03 修復進展：
  - UI 規範修復：CSS 變數體系、硬編碼 #fff/rgba 替換、--surface 誤用修復
  - 後端審計修復：sid→studioId、CORS production、Admin Zod、ESM require→import、Auth 限流
  - 命名重構：sid/sname→studioId/studioName、recurringGroupId 完全移除、FormulaTemplate→Formula
  - SonarCloud 滿分衝刺：PR #22-26，45 個問題全部修復，Quality Gate OK
  - 瘦身+UI統一+代碼質量：PR #26（刪未用圖片、移除死依賴、硬編碼rgba→CSS變數、z.any()→類型化schema）
  - Docker 重新部署：Vite build 修復（孤兒代碼、import 缺失）、3 容器健康
  - 用戶引導 Guide 修復：dialog.showModal()、tooltip 定位
- dev 分支已刪，只剩 main 分支
- ⚠️ 部署用的 .env 含密鑰，不應提交
- ⚠️ Vite 打包不檢查跨模組 import 完整性，瘦身/重構後必須做完整功能測試
- ⚠️ sed 刪多行代碼很危險，Python 更可靠

## 📧 Agent Mail（新）
- agently-cli 已安裝，OAuth 已授權
- 郵箱：lam151251@agent.qq.com
- Skill：agently-mail（~/.agents/skills/agently-mail/）
- 用途：收發郵件、搜尋、回覆、轉發
- ⚠️ 寫操作需兩階段確認（ctk_xxx）

## 📧 IMAP 歸檔系統（mbsync + Dovecot + Roundcube）
- **mbsync (isync 1.4.4)**：同步 Gmail → 本地 Maildir
  - 配置：`/vol1/@apphome/mail-archive/.mbsyncrc`
  - Maildir：`/vol1/@apphome/mail-archive/maildir/`
  - Gmail App Password 已設定
  - 同步所有標籤（INBOX, Sent, Drafts, Trash, Spam, All Mail, Starred, Important）
  - 每 15 分鐘自動同步（OpenClaw cron）
  - 同步腳本：`/vol1/@apphome/mail-archive/sync.sh`
- **Dovecot 2.3.19**：本地 IMAP :143
  - 配置：`/etc/dovecot/dovecot.conf`
  - 用戶：lam151251 / Lam@963852
  - Maildir 後端
- **Roundcube**（Docker, :8680）
  - 連接 host.docker.internal:143 → Dovecot
  - Web 介面：http://192.168.1.50:8680
- 郵件統計：~658 封已同步

## 📧 郵件歸郵件歸檔系統（舊，已停用）
- agently-cli 舊版已被小king刪除（2026-07-31），現已重新安裝
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
- ⚠️ 安裝 skill 時必須嚴格按 skill-vetter 協議執行，不跳步

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
- 成員清單：PostgreSQL `thoth` DB → `discord_members` 表
- 項目清單：PostgreSQL `thoth` DB → `discord_projects` 表
- 審計日誌：`memory/discord-audit.log`
- Discord API 需用 `DiscordBot` User-Agent，Python urllib 會被 Cloudflare 1010
- 成員：小king（admin, UID 1000）+ zeronosu（member, UID 1002，2026-07-31 加入）+ 桃桃（2026-08-02 加入）
- ⚠️ Discord API members?limit=100 只返回 2 人（可能 bot 權限問題），與 discord-members.json 記錄 4 人有差異
- 項目頻道命名：直接用項目名，不加 project- 前綴
- 記憶隔離：目前靠自律，未來需技術隔離
- NAS 操作前必須先 trim-cli login，不假設 token 有效
- 密碼安全：隨機臨時密碼，只發私人頻道，不記錄明文
- Discord Bot 已有 Administrator 權限，頻道結構已建立（資訊/成員/公共/項目）

- GitHub 2FA：thoth151251-bot 帳號需在 2026-09-10 前啟用
- Wiki 超大頁面考慮拆分
- 飛牛瀏覽器從 UI 卸載
- 告警微信推送實際觸發測試
- Webhook @reboot 自啟機制
- ⚠️ Discord message plugin 在 openclaw-weixin channel 未載入，深夜檢查受限

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
- CSS class 命名衝突是隱蔽 bug，通用 class 名（`.empty`）容易意外匹配
- Vite content hash 基於文件內容，minified 結果 hash 一樣時 `--no-cache` 也沒用
- 移除不存在功能的代碼比修復它更正確
- OCR pre-commit hook 審查範圍是整個文件，不只 diff — 既有代碼問題會混進來
- `--primary-rgb` CSS 變數引入大量連鎖維護問題，硬編碼 rgba 更乾淨
- mbsync `Create Both` + `Flatten .` 會在 Gmail 端建出重複標籤，用 `Create Near` 更安全
- **MCP Servers 已安裝**（2026-08-03）：GitHub(9工具)、Filesystem(8工具)、SonarCloud(12工具)
  - ⚠️ 優先用 MCP，不要手動 curl 拼 API
  - ⚠️ Filesystem MCP 的 search_files / directory_tree 是原生 tool 沒有的功能
  - ⚠️ 搜索代碼用 MCP 即時搜索，不建手動索引（維護成本高、易過時）
- **SonarCloud 滿分衝刺教訓**：
  - SonarCloud noinspection 註釋無效（不像 SonarQube 本地版）
  - PR 新代碼陷阱：修舊問題時引入敏感字面量反而觸發新告警
  - 正確策略：讓舊問題留在 main 舊代碼中，只修真正需要修的
  - regex 批量替換 JS 文件容易搞壞語法
  - 閉包函數提取到 module scope 時需確保不丟失上下文
- **排查問題時一次加足所有關鍵節點的 log，不要每次只加一點讓用戶來回跑**
  - 正確做法：入口、分支、計算、最終結果一次 log 全覆蓋
  - log 用基本類型（數字/字串），不要用 Object（壓縮後看不到）
  - 先看數據再動手，不要猜
- **`<dialog>` 元素在 `showModal()` 前子元素不可見**，offsetWidth/offsetHeight 返回 0
  - 必須先 showModal() 再測量子元素尺寸
  - 修完一個問題後要驗證下游是否也正常，不要假設修好了就收工
- **嘴上說記得不算，要寫在文件裡才算**（小king 教訓）
- **Vite 打包不檢查跨模組 import 完整性**，瘦身/重構後必須做完整功能測試
- **sed 刪多行代碼很危險，Python 更可靠**

## 🔑 配置要點
- 訊飛星辰 MaaS 高效版 ¥199/月，額度：6,000次/5h、45,000次/週、90,000次/月
- 訊飛星火 timeoutSeconds: 1800，agent timeoutSeconds: 1800，compaction timeoutSeconds: 900
- 主力模型：`讯飞星火/xopglm51`（智譜 GLM-5.1，抵扣×4），fallback: `讯飞星火/auto`（×2）
- 2026-08-02 從 xopglm52 切換到 xopglm51（GLM-5.2 限流嚴重）
- 2026-08-03 模型配置大更新：
  - 19 個模型全部加入 allowlist（含 alias）
  - primary: xopglm51，fallback: auto → xopdeepseekv4flash
  - utilityModel: xopglmv47flash（標題等小事用最便宜的）
  - contextWindow: xopglm52=512K，其餘=128K（待深夜測試）
  - 深夜流水線測試腳本：scripts/xfyun-model-context-test.py
  - xopkimi27code API 報 Model Not Found（可能未上線）
  - Code Review：`xop3qwencodernext`（Qwen3-Coder-Next，抵扣×1）
- 訊飛高效版全部可用模型（19個）：
  - ×5: xopglm52(GLM-5.2), xopdeepseekv4pro(DS-V4-Pro), xopkimi27code(Kimi-K2.7-Code)
  - ×4: xopglm51(GLM-5.1), xopkimik26(Kimi-K2.6)
  - ×3: xopglm5(GLM-5), xopkimik25(KiMi-K2.5)
  - ×2: auto, xsparkx2agent(Spark X2 Agent), xsparkx2(Spark X2), xopdeepseekv4flash(DS-V4-Flash), xopdeepseekv32(DS-V3.2), xminimaxm25(MiniMax-M2.5), xopqwen35397b(Qwen3.5-397B)
  - ×1: xsparkx2flash(Spark-X2-Flash), xopqwen36v35b(Qwen3.6-35B), xopqwen35v35b(Qwen3.5-35B), xop3qwencodernext(Qwen3-Coder-Next), xopglmv47flash(GLM-4.7-Flash)
- contextWindow: 512000（已生效），reserveTokensFloor: 20000
- 訊飛星火 token 計數不可靠，API 回報值波動極大
- xopglm52 實測支持 560k context，1M 超時
- **訊飛適配計劃統一記錄：`xfyun-adaptation-plan.md`**
- 微信 streaming mode: block（不支援 edit message）
- 訊飛適配數據記錄：Redis DB1 `xfyun:records:*` + `xfyun:timeline`（每5分鐘自動記錄）
- 訊飛星火高效版 ¥199/月，額度充裕（月用量 <20%）
- 記憶搜索：Ollama nomic-embed-text
- messages.suppressToolErrors: true（頂層）
- auth.cooldowns: overloadedProfileRotations=3, overloadedBackoffMs=5000, rateLimitedProfileRotations=3
- SearXNG 端口：8080（host 網路模式，非 8888）
- Redis: DB0=SearXNG, DB1=TaskGuard, maxmemory 256MB+LRU
- Redis DB1 命名空間規範：
  - `tg:*` — Task Guard（去重/限流/快取）
  - `xfyun:*` — 訊飛適配數據（records/timeline/recorded）
  - `heartbeat:*` — 心跳狀態
  - `grafana:*` — Grafana 告警
  - 新增數據必須用 `前綴:子類:key` 格式，避免衝突
  - ⚠️ Redis 只存熱數據（高頻讀頻讀寫/臨時/快取），結構化持久數據用 JSON 文件

## 🗓️ 小king 的學業
- UWE 課程：Sem1 CGD / Sem2 Interaction Design / Sem3 Creative Tech Project / Sem4 3D Modelling
- 補底班：8月超密集（12堂 + Induction + CGD正式課4堂）
- Google Calendar 已整合課程時間表

## 🕐 Cron 排程
- 01:00 每天：深夜維護流水線（健康檢查→系統清理→記憶整理→Git Backup）
- 03:00 每天：SonarCloud 自動修復（fitness-coach-app，auto 模型，最多5-10個/次）⚠️ PR #22-26 已全部 merged，SonarCloud 問題已清零，此 cron 可能需調整
- 07:00 每天：早安報告（天氣+郵件）
- 深夜流水線 timeout: 1800s
- ⚠️ 同一時段不要多個任務同時跑，會搶配額
- ⚠️ cron 環境中 message tool 可能不可用（如 Discord plugin 未載入），健康檢查需注意
- ⚠️ Discord Bot 檢查用 curl 直接打 API（不依賴 message plugin），Guild ID: 1531560409499172865
