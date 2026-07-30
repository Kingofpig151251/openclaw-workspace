#!/usr/bin/env python3
"""
push_metrics.py — 推送 OpenClaw 自定義指標到 Prometheus Pushgateway

數據源：
1. OpenClaw sessions.json — token 用量、compaction 次數
2. Wiki Benchmark (Redis DB1) — 搜尋命中率、token 數
3. 訊飛 API 探測 — 可用性、響應時間

用法：
  python3 push_metrics.py              # 推送所有指標
  python3 push_metrics.py --dry-run    # 只打印，不推送
"""

import json
import time
import sys
import os
import redis
import requests
from datetime import datetime

PUSHGATEWAY_URL = "http://127.0.0.1:9091"
JOB = "openclaw_custom"

# OpenClaw sessions 路径
SESSIONS_JSON = "/vol1/@apphome/trim.openclaw/data/home/.openclaw/agents/main/sessions/sessions.json"

# Redis
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
        # 跳过没有 token 数据的
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

        # 每个 session 的指标 — 用 accountId+sessionId 前8位确保唯一
        # 从 sid 提取 accountId: agent:main:openclaw-weixin:{accountId}:direct:...
        parts = sid.split(':')
        account_id = parts[3] if len(parts) > 3 else "unknown"
        sid_short = parts[-1][:8] if len(parts) > 1 else sid[:8]
        session_type = "main" if ":main:main" in sid else "weixin" if "openclaw-weixin" in sid else "cron" if "cron" in sid else "other"
        session_label = f"{session_type}_{account_id[:8]}_{sid_short}"

        metrics.append({
            "name": "openclaw_session_total_tokens",
            "labels": {"session": session_label, "type": session_type},
            "value": s.get("totalTokens", 0) or 0
        })
        metrics.append({
            "name": "openclaw_session_input_tokens",
            "labels": {"session": session_label, "type": session_type},
            "value": s.get("inputTokens", 0) or 0
        })
        metrics.append({
            "name": "openclaw_session_output_tokens",
            "labels": {"session": session_label, "type": session_type},
            "value": s.get("outputTokens", 0) or 0
        })
        metrics.append({
            "name": "openclaw_session_cache_read_tokens",
            "labels": {"session": session_label, "type": session_type},
            "value": s.get("cacheRead", 0) or 0
        })
        metrics.append({
            "name": "openclaw_session_compaction_count",
            "labels": {"session": session_label, "type": session_type},
            "value": comp if isinstance(comp, int) else 0
        })
        metrics.append({
            "name": "openclaw_session_runtime_seconds",
            "labels": {"session": session_label, "type": session_type},
            "value": round((s.get("runtimeMs", 0) or 0) / 1000, 1)
        })
        metrics.append({
            "name": "openclaw_session_context_tokens",
            "labels": {"session": session_label, "type": session_type},
            "value": s.get("contextTokens", 0) or 0
        })

    # 汇总指标
    metrics.append({"name": "openclaw_sessions_total", "labels": {}, "value": session_count})
    metrics.append({"name": "openclaw_tokens_input_total", "labels": {}, "value": total_input})
    metrics.append({"name": "openclaw_tokens_output_total", "labels": {}, "value": total_output})
    metrics.append({"name": "openclaw_tokens_cache_read_total", "labels": {}, "value": total_cache_read})
    metrics.append({"name": "openclaw_tokens_cache_write_total", "labels": {}, "value": total_cache_write})
    metrics.append({"name": "openclaw_compaction_total", "labels": {}, "value": total_compaction})

    return metrics


def collect_wiki_benchmark():
    """從 Redis 收集 Wiki Benchmark 指標"""
    metrics = []
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        result = r.get("tg:wiki-benchmark:result")
        if not result:
            print("⚠️ No wiki benchmark result in Redis")
            return metrics

        data = json.loads(result)
        summary = data.get("summary", {})

        # 命中率（提取数字）
        hit_rate_str = summary.get("hit_rate", "0%")
        # 格式: "搜尋命中率                100% (20/20)"
        import re
        hit_match = re.search(r'(\d+)%', str(hit_rate_str))
        hit_rate = float(hit_match.group(1)) if hit_match else 0
        metrics.append({"name": "openclaw_wiki_hit_rate_percent", "labels": {"wiki": "king-wiki-js"}, "value": hit_rate})

        # 孤立頁面
        orphans_str = summary.get("orphans", "0")
        orphans_match = re.search(r'(\d+)', str(orphans_str))
        orphans = float(orphans_match.group(1)) if orphans_match else 0
        metrics.append({"name": "openclaw_wiki_orphan_pages", "labels": {"wiki": "king-wiki-js"}, "value": orphans})

        # 交叉引用密度
        density_str = summary.get("density", "0")
        density_match = re.search(r'([\d.]+)', str(density_str))
        density = float(density_match.group(1)) if density_match else 0
        metrics.append({"name": "openclaw_wiki_cross_ref_density", "labels": {"wiki": "king-wiki-js"}, "value": density})

        # 合規率
        compliance_str = summary.get("compliance", "0%")
        compliance_match = re.search(r'(\d+)%', str(compliance_str))
        compliance = float(compliance_match.group(1)) if compliance_match else 0
        metrics.append({"name": "openclaw_wiki_compliance_rate_percent", "labels": {"wiki": "king-wiki-js"}, "value": compliance})

        # 過時頁面
        stale_str = summary.get("stale", "0")
        stale_match = re.search(r'(\d+)', str(stale_str))
        stale = float(stale_match.group(1)) if stale_match else 0
        metrics.append({"name": "openclaw_wiki_stale_pages", "labels": {"wiki": "king-wiki-js"}, "value": stale})

        # Token 估算
        tokens_str = summary.get("tokens", "0")
        tokens_match = re.search(r'([\d,]+)', str(tokens_str))
        total_tokens = float(tokens_match.group(1).replace(",", "")) if tokens_match else 0
        metrics.append({"name": "openclaw_wiki_total_tokens", "labels": {"wiki": "king-wiki-js"}, "value": total_tokens})

        # 最后运行时间戳
        last_ts = data.get("ts")
        if last_ts:
            try:
                dt = datetime.fromisoformat(last_ts)
                metrics.append({"name": "openclaw_wiki_benchmark_last_run_timestamp", "labels": {"wiki": "king-wiki-js"}, "value": dt.timestamp()})
            except:
                pass

    except Exception as e:
        print(f"⚠️ Wiki benchmark collection error: {e}")

    return metrics


def collect_xfyun_probe():
    """訊飛 API 探測指標"""
    metrics = []
    try:
        # 简单探测：发一个极短请求，量响应时间
        start = time.time()
        try:
            resp = requests.post(
                "https://maas-coding-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
                json={"model": "astron-code-latest", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                headers={"Authorization": "Bearer test", "Content-Type": "application/json"},
                timeout=10
            )
            elapsed = time.time() - start
            # 401 = API 可达但认证失败（正常，我们没传真 key）
            # 200 = 完全正常
            reachable = 1 if resp.status_code in [200, 401, 422] else 0
            status_code = resp.status_code
        except requests.exceptions.Timeout:
            elapsed = time.time() - start
            reachable = 0
            status_code = 0
        except Exception as e:
            elapsed = time.time() - start
            reachable = 0
            status_code = -1

        metrics.append({"name": "openclaw_xfyun_api_reachable", "labels": {}, "value": reachable})
        metrics.append({"name": "openclaw_xfyun_api_response_seconds", "labels": {}, "value": round(elapsed, 3)})
        metrics.append({"name": "openclaw_xfyun_api_status_code", "labels": {}, "value": status_code})

    except Exception as e:
        print(f"⚠️ Xfyun probe error: {e}")

    return metrics


def collect_grafana_alerts():
    """从 Redis 读取 Grafana 告警，推送为指标"""
    metrics = []
    try:
        r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        alerts = r.hgetall('grafana:alerts')
        for alertname, data_str in alerts.items():
            data = json.loads(data_str)
            status = 1 if data.get('status') == 'firing' else 0
            metrics.append({
                'name': 'openclaw_grafana_alert',
                'value': status,
                'labels': {
                    'alertname': alertname,
                    'severity': data.get('severity', 'info')
                }
            })
    except Exception as e:
        print(f"⚠️ Failed to collect Grafana alerts: {e}")
    return metrics


def main():
    dry_run = "--dry-run" in sys.argv

    all_metrics = []

    print("📊 Collecting OpenClaw session metrics...")
    all_metrics.extend(collect_openclaw_sessions())

    print("📊 Collecting Wiki benchmark metrics...")
    all_metrics.extend(collect_wiki_benchmark())

    print("📊 Collecting Xfyun API probe metrics...")
    all_metrics.extend(collect_xfyun_probe())

    print("📊 Collecting Grafana alerts...")
    all_metrics.extend(collect_grafana_alerts())

    # 推送时间戳指标，用于告警判断数据新鲜度
    all_metrics.append({"name": "openclaw_push_timestamp", "value": time.time(), "labels": {}})

    print(f"\n📊 Total: {len(all_metrics)} metrics")
    push_metrics(all_metrics, dry_run=dry_run)


if __name__ == "__main__":
    main()


