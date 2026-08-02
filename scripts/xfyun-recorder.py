#!/usr/bin/env python3
"""
訊飛星火適配數據記錄器（Redis 版）
掃描 sessions.json，每次 session 結束就記一筆到 Redis DB1。

Redis 結構：
  HASH  xfyun:records:{session_id}:{updated_at}  → 完整記錄
  ZSET  xfyun:timeline                          → timestamp → record_key（按時間排序）
  SET   xfyun:recorded                          → 已記錄的 record_key（去重）
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
import redis

TZ = timezone(timedelta(hours=8))

SESSIONS_FILE = "/vol1/@apphome/trim.openclaw/data/home/.openclaw/agents/main/sessions/sessions.json"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_DB = 1
MAX_RECORDS = 1000  # 保留最近 1000 條

def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def classify_session_key(key):
    if ':cron:' in key:
        return 'cron'
    elif ':discord:' in key:
        return 'discord'
    elif ':openclaw-weixin:' in key:
        return 'weixin-dm' if ':direct:' in key else 'weixin'
    elif key == 'agent:main:main':
        return 'main'
    elif ':heartbeat:' in key:
        return 'heartbeat'
    elif ':subagent:' in key:
        return 'subagent'
    else:
        return 'other'

def extract_record(key, session):
    pending_text = session.get('pendingFinalDeliveryText', '') or ''
    rate_limited = '429' in pending_text or 'rate limit' in pending_text.lower()
    
    aborted = session.get('abortedLastRun', False)
    runtime_ms = session.get('runtimeMs', 0)
    timeout = aborted or (runtime_ms > 550000 and session.get('status') == 'done')

    model = session.get('model', '')
    fallback_triggered = 'qwen' in model.lower() or 'ollama' in model.lower()

    return {
        'timestamp': datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S'),
        'ts_epoch': int(time.time()),
        'session_key': key,
        'session_type': classify_session_key(key),
        'model': session.get('model', 'unknown'),
        'provider': session.get('modelProvider', 'unknown'),
        'input_tokens': session.get('inputTokens', 0),
        'output_tokens': session.get('outputTokens', 0),
        'cache_read': session.get('cacheRead', 0),
        'cache_write': session.get('cacheWrite', 0),
        'total_tokens': session.get('totalTokens', 0),
        'compaction_count': session.get('compactionCount', 0),
        'runtime_ms': runtime_ms,
        'runtime_seconds': round(runtime_ms / 1000, 1) if runtime_ms else 0,
        'context_tokens': session.get('contextTokens', 0),
        'aborted': aborted,
        'timeout': timeout,
        'rate_limited': rate_limited,
        'fallback_triggered': fallback_triggered,
        'status': session.get('status', 'unknown'),
    }

def main():
    sessions = load_json(SESSIONS_FILE, {})
    if not sessions:
        print("sessions.json 讀不到，跳過")
        return

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    new_records = []

    for key, session in sessions.items():
        if not isinstance(session, dict):
            continue

        session_id = session.get('sessionId', '')
        status = session.get('status', '')
        updated_at = session.get('updatedAt', 0)

        if status not in ('done', 'error', 'aborted'):
            continue

        record_key = f"{session_id}:{updated_at}"

        # Redis SET 去重
        if r.sismember('xfyun:recorded', record_key):
            continue

        provider = session.get('modelProvider', '')
        if provider and '訊飛' not in provider and 'xfyun' not in provider.lower():
            continue

        record = extract_record(key, session)
        ts = record['ts_epoch']

        # 存到 Redis
        # HASH 存完整記錄
        r.hset(f"xfyun:records:{record_key}", mapping={k: str(v) for k, v in record.items()})
        # ZSET 按時間排序
        r.zadd('xfyun:timeline', {record_key: ts})
        # SET 標記已記錄
        r.sadd('xfyun:recorded', record_key)

        new_records.append(record)

    if not new_records:
        print("無新記錄")
        return

    # 清理過舊記錄（保留最近 MAX_RECORDS 條）
    total = r.zcard('xfyun:timeline')
    if total > MAX_RECORDS:
        # 獲取最舊的記錄
        old_keys = r.zrange('xfyun:timeline', 0, total - MAX_RECORDS - 1)
        for old_key in old_keys:
            r.delete(f"xfyun:records:{old_key}")
            r.srem('xfyun:recorded', old_key)
            r.zrem('xfyun:timeline', old_key)
        print(f"清理了 {len(old_keys)} 條舊記錄")

    print(f"✅ 記錄了 {len(new_records)} 筆新 session 數據到 Redis DB1")
    for r2 in new_records:
        print(f"  {r2['timestamp']} | {r2['session_type']:10s} | in={r2['input_tokens']:6d} out={r2['output_tokens']:5d} | {r2['runtime_seconds']}s | compaction={r2['compaction_count']} | rate_limited={r2['rate_limited']} timeout={r2['timeout']}")

if __name__ == '__main__':
    main()
