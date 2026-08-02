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
