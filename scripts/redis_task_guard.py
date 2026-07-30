#!/usr/bin/env python3
"""
Redis Task Guard - 任務去重/限流/狀態追蹤
用於 OpenClaw cron 任務和心跳，防止重複執行、控制頻率

用法:
  from redis_task_guard import TaskGuard
  
  guard = TaskGuard()
  
  # 去重：同一任務 5 分鐘內不重複執行
  if guard.should_run("wiki-benchmark", dedup_minutes=5):
      result = run_benchmark()
      guard.mark_done("wiki-benchmark", result_summary=result)
  
  # 限流：API 調用頻率控制
  if guard.rate_limit_ok("xfyun-api", max_calls=10, window_seconds=60):
      call_api()
  
  # 狀態追蹤
  guard.set_state("mail-sync", {"last_sync": "2026-07-29", "count": 42})
  state = guard.get_state("mail-sync")
"""

import json
import time
import redis
import hashlib
from datetime import datetime

REDIS_URL = "redis://127.0.0.1:6379/1"  # DB 1 for task guard (DB 0 = SearXNG)
KEY_PREFIX = "tg:"


class TaskGuard:
    def __init__(self, redis_url=REDIS_URL):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.prefix = KEY_PREFIX

    def _key(self, name, suffix=""):
        return f"{self.prefix}{name}:{suffix}" if suffix else f"{self.prefix}{name}"

    # ── 去重 ──
    def should_run(self, task_name, dedup_minutes=5):
        """檢查任務是否應該執行（去重視窗內不重複）"""
        key = self._key(task_name, "last")
        last = self.r.get(key)
        if last:
            elapsed = time.time() - float(last)
            if elapsed < dedup_minutes * 60:
                return False
        return True

    def mark_done(self, task_name, result_summary=None, ttl_hours=24):
        """標記任務完成，可附帶結果摘要"""
        key_last = self._key(task_name, "last")
        key_result = self._key(task_name, "result")
        now = time.time()
        self.r.set(key_last, str(now), ex=ttl_hours * 3600)
        if result_summary is not None:
            data = {
                "ts": datetime.now().isoformat(),
                "summary": result_summary
            }
            self.r.set(key_result, json.dumps(data, ensure_ascii=False), ex=ttl_hours * 3600)

    def last_result(self, task_name):
        """獲取上次執行結果"""
        key = self._key(task_name, "result")
        raw = self.r.get(key)
        if raw:
            return json.loads(raw)
        return None

    # ── 限流 ──
    def rate_limit_ok(self, action_name, max_calls=10, window_seconds=60):
        """滑動視窗限流：window_seconds 內最多 max_calls 次"""
        key = self._key(action_name, "rl")
        now = time.time()
        window_start = now - window_seconds

        pipe = self.r.pipeline()
        # 移除過期記錄
        pipe.zremrangebyscore(key, 0, window_start)
        # 計數
        pipe.zcard(key)
        # 加入當前請求
        pipe.zadd(key, {str(now): now})
        # 設 TTL
        pipe.expire(key, window_seconds + 10)
        results = pipe.execute()

        count = results[1]
        if count >= max_calls:
            # 超限，移除剛加的記錄
            self.r.zrem(key, str(now))
            return False
        return True

    def rate_limit_status(self, action_name, window_seconds=60):
        """查看限流狀態"""
        key = self._key(action_name, "rl")
        now = time.time()
        self.r.zremrangebyscore(key, 0, now - window_seconds)
        count = self.r.zcard(key)
        return {"count": count, "window": window_seconds}

    # ── 狀態追蹤 ──
    def set_state(self, task_name, state_data, ttl_hours=72):
        """存儲任務狀態（JSON）"""
        key = self._key(task_name, "state")
        data = {
            "updated": datetime.now().isoformat(),
            "data": state_data
        }
        self.r.set(key, json.dumps(data, ensure_ascii=False), ex=ttl_hours * 3600)

    def get_state(self, task_name):
        """讀取任務狀態"""
        key = self._key(task_name, "state")
        raw = self.r.get(key)
        if raw:
            return json.loads(raw)
        return None

    # ── 計數器 ──
    def increment(self, counter_name, ttl_hours=24):
        """簡單計數器"""
        key = self._key(counter_name, "cnt")
        val = self.r.incr(key)
        if val == 1:
            self.r.expire(key, ttl_hours * 3600)
        return val

    def get_count(self, counter_name):
        """讀取計數器"""
        key = self._key(counter_name, "cnt")
        val = self.r.get(key)
        return int(val) if val else 0

    # ── 工具 ──
    def list_tasks(self):
        """列出所有追蹤中的任務"""
        keys = self.r.keys(f"{self.prefix}*:last")
        tasks = []
        for k in keys:
            name = k.replace(f"{self.prefix}", "").replace(":last", "")
            last_ts = self.r.get(k)
            result = self.last_result(name)
            tasks.append({
                "name": name,
                "last_run": float(last_ts) if last_ts else None,
                "last_result": result
            })
        return tasks

    def cleanup(self, task_name):
        """清除任務所有記錄"""
        pattern = self._key(task_name, "*")
        keys = self.r.keys(pattern)
        if keys:
            self.r.delete(*keys)
        return len(keys)


if __name__ == "__main__":
    guard = TaskGuard()
    
    # Smoke test
    print("=== Redis Task Guard Smoke Test ===")
    
    # 去重測試
    print(f"should_run('test-task'): {guard.should_run('test-task', dedup_minutes=1)}")
    guard.mark_done('test-task', result_summary='測試完成')
    print(f"should_run('test-task') again: {guard.should_run('test-task', dedup_minutes=1)}")
    print(f"last_result: {guard.last_result('test-task')}")
    
    # 限流測試
    for i in range(12):
        ok = guard.rate_limit_ok('test-api', max_calls=5, window_seconds=10)
        if not ok:
            print(f"rate_limit blocked at call {i+1}")
            break
    print(f"rate_limit_status: {guard.rate_limit_status('test-api', window_seconds=10)}")
    
    # 狀態測試
    guard.set_state('test-state', {'status': 'running', 'progress': 50})
    print(f"get_state: {guard.get_state('test-state')}")
    
    # 計數器測試
    for _ in range(3):
        guard.increment('test-counter')
    print(f"counter: {guard.get_count('test-counter')}")
    
    # 清理
    for name in ['test-task', 'test-api', 'test-state', 'test-counter']:
        cleaned = guard.cleanup(name)
        print(f"cleaned {name}: {cleaned} keys")
    
    print("\n✅ All tests passed!")
