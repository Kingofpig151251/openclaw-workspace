#!/usr/bin/env python3
"""
push_metrics.py — 推送 OpenClaw 自定義指標到 Prometheus Pushgateway

數據源：
1. OpenClaw sessions.json — token 用量、compaction 次數
2. 訊飛 API 探測 — 可用性、響應時間
3. Docker 容器狀態
4. Redis 狀態
5. PostgreSQL 狀態
6. 郵件同步狀態

已移除：
- Wiki Benchmark（命中率已穩定 100%，不再收集）
- Grafana 告警（從未觸發過，webhook 也沒自啟）
"""

import json
import time
import sys
import os
import subprocess
import redis
import requests
from datetime import datetime

PUSHGATEWAY_URL = "http://127.0.0.1:9091"
JOB = "openclaw_custom"

SESSIONS_JSON = "/vol1/@apphome/trim.openclaw/data/home/.openclaw/agents/main/sessions/sessions.json"
REDIS_URL = "redis://127.0.0.1:6379/1"


def push_metrics(metrics, dry_run=False):
    """推送指標到 Pushgateway"""
    lines = []
    for m in metrics:
        labels_str = ""
        if m.get("labels"):
            label_parts = [f'{k}="{v}"' for k, v in m["labels"].items()]
            labels_str = "{" + ",".join(label_parts) + "}"
        lines.append(f'{m["name"]}{labels_str} {m["value"]}')

    text = "\n".join(lines) + "\n"

    if dry_run:
        print("=== DRY RUN ===")
        print(text)
        return

    url = f"{PUSHGATEWAY_URL}/metrics/job/{JOB}"
    resp = requests.post(url, data=text, headers={"Content-Type": "text/plain"}, timeout=10)
    if resp.status_code not in (200, 202):
        print(f"❌ Push failed: {resp.status_code} {resp.text}")
    else:
        print(f"✅ Pushed {len(metrics)} metrics at {datetime.now().isoformat()}")


def collect_openclaw_sessions():
    """從 sessions.json 收集 token 用量指標"""
    metrics = []
    try:
        with open(SESSIONS_JSON, "r") as f:
            sessions = json.load(f)
    except Exception as e:
        print(f"⚠️ Cannot read sessions.json: {e}")
        return metrics

    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    total_compaction = 0
    session_count = 0

    for sid, s in sessions.items():
        if s.get("totalTokens") is None:
            continue

        session_count += 1
        total_input += s.get("inputTokens", 0) or 0
        total_output += s.get("outputTokens", 0) or 0
        total_cache_read += s.get("cacheRead", 0) or 0
        total_cache_write += s.get("cacheWrite", 0) or 0
        comp = s.get("compactionCount", 0)
        if isinstance(comp, int):
            total_compaction += comp

        parts = sid.split(':')
        account_id = parts[3] if len(parts) > 3 else "unknown"
        sid_short = parts[-1][:8] if len(parts) > 1 else sid[:8]
        session_type = "main" if ":main:main" in sid else "weixin" if "openclaw-weixin" in sid else "cron" if "cron" in sid else "other"
        session_label = f"{session_type}_{account_id[:8]}_{sid_short}"

        metrics.extend([
            {"name": "openclaw_session_total_tokens", "labels": {"session": session_label, "type": session_type}, "value": s.get("totalTokens", 0) or 0},
            {"name": "openclaw_session_input_tokens", "labels": {"session": session_label, "type": session_type}, "value": s.get("inputTokens", 0) or 0},
            {"name": "openclaw_session_output_tokens", "labels": {"session": session_label, "type": session_type}, "value": s.get("outputTokens", 0) or 0},
            {"name": "openclaw_session_cache_read_tokens", "labels": {"session": session_label, "type": session_type}, "value": s.get("cacheRead", 0) or 0},
            {"name": "openclaw_session_compaction_count", "labels": {"session": session_label, "type": session_type}, "value": comp if isinstance(comp, int) else 0},
            {"name": "openclaw_session_runtime_seconds", "labels": {"session": session_label, "type": session_type}, "value": round((s.get("runtimeMs", 0) or 0) / 1000, 1)},
            {"name": "openclaw_session_context_tokens", "labels": {"session": session_label, "type": session_type}, "value": s.get("contextTokens", 0) or 0},
        ])

    metrics.extend([
        {"name": "openclaw_sessions_total", "labels": {}, "value": session_count},
        {"name": "openclaw_tokens_input_total", "labels": {}, "value": total_input},
        {"name": "openclaw_tokens_output_total", "labels": {}, "value": total_output},
        {"name": "openclaw_tokens_cache_read_total", "labels": {}, "value": total_cache_read},
        {"name": "openclaw_tokens_cache_write_total", "labels": {}, "value": total_cache_write},
        {"name": "openclaw_compaction_total", "labels": {}, "value": total_compaction},
    ])

    return metrics


def collect_xfyun_probe():
    """訊飛 API 探測 — 只保留可達性和響應時間"""
    metrics = []
    try:
        start = time.time()
        try:
            resp = requests.post(
                "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
                json={"model": "auto", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                headers={"Authorization": "Bearer test", "Content-Type": "application/json"},
                timeout=10
            )
            elapsed = time.time() - start
            reachable = 1 if resp.status_code in [200, 401, 422] else 0
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            reachable = 0
        except Exception:
            elapsed = time.time() - start
            reachable = 0

        metrics.append({"name": "openclaw_xfyun_api_reachable", "labels": {}, "value": reachable})
        metrics.append({"name": "openclaw_xfyun_api_response_seconds", "labels": {}, "value": round(elapsed, 3)})
    except Exception as e:
        print(f"⚠️ Xfyun probe error: {e}")

    return metrics


def collect_docker_status():
    """Docker 容器狀態"""
    metrics = []
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            name = parts[0]
            status = parts[1]
            running = 1 if status.startswith("Up") else 0
            metrics.append({"name": "openclaw_docker_container_running", "labels": {"container": name}, "value": running})
    except Exception as e:
        print(f"⚠️ Docker status error: {e}")

    return metrics


def collect_redis_status():
    """Redis 狀態"""
    metrics = []
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, db=1, decode_responses=True)
        info = r.info()
        metrics.extend([
            {"name": "openclaw_redis_used_memory_bytes", "labels": {"db": "1"}, "value": info.get("used_memory", 0)},
            {"name": "openclaw_redis_maxmemory_bytes", "labels": {"db": "1"}, "value": info.get("maxmemory", 0)},
            {"name": "openclaw_redis_keys_total", "labels": {"db": "1"}, "value": r.dbsize()},
        ])
        # 訊飛記錄數量
        xfyun_count = r.zcard('xfyun:timeline')
        metrics.append({"name": "openclaw_xfyun_records_total", "labels": {}, "value": xfyun_count})
    except Exception as e:
        print(f"⚠️ Redis status error: {e}")

    return metrics


def collect_postgres_status():
    """PostgreSQL 狀態（通過 docker exec）"""
    metrics = []
    try:
        queries = [
            ("openclaw_postgres_discord_members", "SELECT count(*) FROM discord_members;"),
            ("openclaw_postgres_mail_classifications", "SELECT count(*) FROM mail_classifications;"),
            ("openclaw_postgres_connections", "SELECT count(*) FROM pg_stat_activity;"),
        ]
        for metric_name, query in queries:
            result = subprocess.run(
                ["docker", "exec", "thoth-postgres", "psql", "-U", "thoth", "-d", "thoth", "-t", "-c", query],
                capture_output=True, text=True, timeout=10
            )
            count = int(result.stdout.strip() or 0)
            metrics.append({"name": metric_name, "labels": {}, "value": count})
    except Exception as e:
        print(f"⚠️ PostgreSQL status error: {e}")

    return metrics


def collect_mail_status():
    """郵件同步狀態"""
    metrics = []
    try:
        # Maildir 郵件數量
        result = subprocess.run(
            ["find", "/vol1/@apphome/mail-archive/maildir", "-type", "f", "-name", "*.Thoth-NAS*"],
            capture_output=True, text=True, timeout=10
        )
        mail_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        metrics.append({"name": "openclaw_mail_archived_total", "labels": {}, "value": mail_count})
        
        # 最後同步時間
        sync_log = "/vol1/@apphome/mail-archive/sync.log"
        if os.path.exists(sync_log):
            stat = os.stat(sync_log)
            metrics.append({"name": "openclaw_mail_last_sync_timestamp", "labels": {}, "value": stat.st_mtime})
    except Exception as e:
        print(f"⚠️ Mail status error: {e}")

    return metrics


def main():
    dry_run = "--dry-run" in sys.argv

    all_metrics = []

    print("📊 Collecting OpenClaw session metrics...")
    all_metrics.extend(collect_openclaw_sessions())

    print("📊 Collecting Xfyun API probe...")
    all_metrics.extend(collect_xfyun_probe())

    print("📊 Collecting Docker container status...")
    all_metrics.extend(collect_docker_status())

    print("📊 Collecting Redis status...")
    all_metrics.extend(collect_redis_status())

    print("📊 Collecting PostgreSQL status...")
    all_metrics.extend(collect_postgres_status())

    print("📊 Collecting mail archive status...")
    all_metrics.extend(collect_mail_status())

    # 推送時間戳
    all_metrics.append({"name": "openclaw_push_timestamp", "value": time.time(), "labels": {}})

    print(f"\n📊 Total: {len(all_metrics)} metrics")
    push_metrics(all_metrics, dry_run=dry_run)


if __name__ == "__main__":
    main()
