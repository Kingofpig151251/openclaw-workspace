#!/usr/bin/env python3
"""
heartbeat_guard.py — 心跳任務守衛
整合 Redis Task Guard 到 OpenClaw 心跳流程

功能：
1. Benchmark 去重：5分鐘內不重複跑
2. 結果快取：存 Redis，下次心跳直接讀
3. 限流：API/搜尋頻率控制
4. 狀態追蹤：記錄各任務最後狀態
"""

import sys
import os
import json
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from redis_task_guard import TaskGuard

WIKI_ROOT = '/vol1/1000/projects/king-wiki-js'
BENCHMARK_SCRIPT = os.path.join(WIKI_ROOT, '_internal', 'wiki-benchmark.sh')

guard = TaskGuard()


def run_benchmark_if_needed():
    """跑 wiki benchmark，5分鐘去重，結果存 Redis"""
    task = "wiki-benchmark"
    
    if not guard.should_run(task, dedup_minutes=5):
        cached = guard.last_result(task)
        if cached:
            print(f"📊 Benchmark cached ({cached['ts']})")
            return cached.get("summary", {})
        return None
    
    print("📊 Running wiki benchmark...")
    try:
        result = subprocess.run(
            ["bash", BENCHMARK_SCRIPT],
            capture_output=True, text=True, timeout=120,
            cwd=WIKI_ROOT
        )
        output = result.stdout
        
        # 提取關鍵指標
        summary = {}
        for line in output.split('\n'):
            if '搜尋命中率' in line:
                summary['hit_rate'] = line.strip()
            elif '交叉引用密度' in line:
                summary['density'] = line.strip()
            elif '孤立頁面' in line:
                summary['orphans'] = line.strip()
            elif 'Frontmatter 合規率' in line:
                summary['compliance'] = line.strip()
            elif '過時頁面' in line:
                summary['stale'] = line.strip()
            elif '全庫 token' in line:
                summary['tokens'] = line.strip()
        
        guard.mark_done(task, result_summary=summary, ttl_hours=24)
        print(f"✅ Benchmark done, cached for 24h")
        return summary
        
    except Exception as e:
        guard.mark_done(task, result_summary={"error": str(e)}, ttl_hours=1)
        print(f"❌ Benchmark failed: {e}")
        return None


def check_rate_limits():
    """檢查各服務限流狀態"""
    services = {
        "xfyun-api": {"max": 10, "window": 60},
        "searxng-search": {"max": 30, "window": 60},
        "ollama-embed": {"max": 20, "window": 60},
    }
    
    status = {}
    for name, cfg in services.items():
        ok = guard.rate_limit_ok(name, max_calls=cfg["max"], window_seconds=cfg["window"])
        st = guard.rate_limit_status(name, window_seconds=cfg["window"])
        status[name] = {"allowed": ok, "usage": f"{st['count']}/{cfg['max']}"}
    
    return status


def get_heartbeat_state():
    """獲取完整心跳狀態"""
    state = guard.get_state("heartbeat")
    if not state:
        state = {"data": {"lastChecks": {}}}
    return state.get("data", {"lastChecks": {}})


def update_heartbeat_check(check_name):
    """更新心跳檢查時間戳"""
    state = get_heartbeat_state()
    state["lastChecks"][check_name] = int(datetime.now().timestamp())
    guard.set_state("heartbeat", state, ttl_hours=72)


def should_check(check_name, interval_minutes=30):
    """判斷是否該執行某項檢查"""
    state = get_heartbeat_state()
    last = state.get("lastChecks", {}).get(check_name, 0)
    elapsed = (int(datetime.now().timestamp()) - last) / 60
    return elapsed >= interval_minutes


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Heartbeat Task Guard")
    parser.add_argument("action", choices=["benchmark", "status", "limits", "state", "list"])
    args = parser.parse_args()
    
    if args.action == "benchmark":
        result = run_benchmark_if_needed()
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.action == "status":
        tasks = guard.list_tasks()
        for t in tasks:
            ts = datetime.fromtimestamp(t["last_run"]).isoformat() if t["last_run"] else "never"
            print(f"  {t['name']}: last={ts}")
    
    elif args.action == "limits":
        status = check_rate_limits()
        print(json.dumps(status, ensure_ascii=False, indent=2))
    
    elif args.action == "state":
        state = get_heartbeat_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
    
    elif args.action == "list":
        tasks = guard.list_tasks()
        print(f"Tracked tasks: {len(tasks)}")
        for t in tasks:
            print(f"  - {t['name']}")
