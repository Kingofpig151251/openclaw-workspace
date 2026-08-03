# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## MCP Servers（已安裝）
- **GitHub MCP** (`github`): 9 工具 — create_issue, create_pull_request, get_file_contents, get_issue, list_commits, list_issues, list_pull_requests, merge_pull_request, search_repositories
- **Filesystem MCP** (`filesystem`): 8 工具 — read_file, write_file, list_directory, search_files, get_file_info, create_directory, move_file, directory_tree
  - 掛載目錄：/vol1/1000/projects/fitness-coach-app, /vol1/@apphome/trim.openclaw/data/workspace
- **SonarCloud MCP** (`sonarcloud`): 12 工具 — search_issues, get_quality_gate_status, get_measures, get_pull_requests, change_issue_status, show_rule, list_projects, list_quality_gates, search_metrics, list_languages, list_rule_repositories, get_raw_source
  - Env: SONARCLOUD_TOKEN, SONARCLOUD_ORGANIZATION=section-nexus
- ⚠️ 優先使用 MCP 工具，不要手動 curl 拼 API！MCP 更快更安全
- ⚠️ SonarCloud env 變量名：SONARCLOUD_TOKEN（不是 API_KEY），SONARCLOUD_ORGANIZATION（不是 ORG）
- ⚠️ Filesystem MCP 的 search_files 和 directory_tree 是原生 tool 沒有的功能，不要因為習慣原生 read/write 就不用 MCP
- ⚠️ 每次操作前先想：這個有 MCP 工具嗎？有的話用 MCP，不要 curl
- ⚠️ 說「記得了」不算數，必須寫在 TOOLS.md 或 MEMORY.md 裡才算
- ⚠️ 搜索代碼用 Filesystem MCP 的 search_files / directory_tree，不建手動索引（維護成本高、易過時）

## GitHub
- PAT: `ghp_2rF9...lo6m`（Kingofpig151251, repo scope）— ⚠️ 完整 token 不應提交，見本地備忘
- gh CLI: `/usr/local/bin/gh`（需 `echo TOKEN | gh auth login --with-token`，缺 read:org scope 但 API 可用）
- Repo: `Section-Nexus/fitness-coach-app`（SSH: git@github.com:...）
- SonarCloud API key: `027a00bd...c004`（用 `-u KEY:` 認證）— ⚠️ 完整 key 不應提交
- SonarCloud project: `Section-Nexus_fitness-coach-app` / org: `section-nexus`

## Ollama
- Path: `/vol1/@appcenter/ai_installer/ollama/bin/ollama`
- API: `http://localhost:11434`
- Models: qwen2.5:3b (fallback only, 1.9GB), nomic-embed-text (embedding, 274MB)
- ⚠️ 7B 已刪除，省 4.7GB

## Python venv
- Path: `/vol1/@apphome/trim.openclaw/data/workspace/.venv`
- Whisper: `openai-whisper v20250625`（语音转文字，用 tiny/base 模型）
- Pillow: `v12.3.0`（图片处理）
- redis: `8.0.1`（Task Guard）
- Usage: `.venv/bin/python` or `.venv/bin/pip`

## ffmpeg
- 已有二进制，视频/音频处理

## SearXNG
- `http://localhost:8080`（本地搜索引擎，host 網路模式）
- 引擎：Google, Bing, DDG, Wikipedia, Wikidata, GitHub, StackOverflow, Reddit, arxiv, DDG Images, Wikimedia Commons
- 語言：auto，分類：general,news,science
- Redis 快取：DB0，已啟用
- Docker compose：`/vol1/docker/searxng/docker-compose.yml`
- Settings：`/vol1/docker/searxng/settings.yml`（bind mount，只讀）

## PostgreSQL 16 (Thoth 自用)
- Docker 容器：thoth-postgres
- Port：5433（避開飛牛系統 PG 的 5432）
- 配置：`/vol1/@apphome/trim.openclaw/docker/postgres/docker-compose.yml`
- 數據：`/vol1/@apphome/trim.openclaw/docker/postgres/data/`
- 用戶：thoth / Thoth@963852
- Database：thoth
- 表：discord_members, discord_projects, discord_project_members, mail_classifications
- 用途：結構化持久數據（Discord 成員/項目、郵件分類記錄）
- Python：`psycopg2-binary` 已安裝在 .venv

## Redis 8.2.1
- `localhost:6379`，maxmemory 256MB + allkeys-lru
- DB0：SearXNG 快取
- DB1：Task Guard（去重/限流/狀態追蹤）

## Task Guard
- `scripts/redis_task_guard.py`：去重、限流、狀態追蹤、計數器
- `scripts/heartbeat_guard.py`：心跳任務守衛（benchmark 去重+快取）
- 用法：`.venv/bin/python scripts/heartbeat_guard.py benchmark|status|limits|state|list`

## Chromium
- Port 16002（浏览器自动化）

---

Add whatever helps you do your job. This is your cheat sheet.
