# 訊飛星火適配優化計劃

> 統一記錄，所有訊飛相關的配置、問題、數據收集、監控、cron 集中在此。
> 最後更新：2026-07-30

---

## 一、模型配置

| 項目 | 值 |
|------|-----|
| Provider ID | `讯飞星火` |
| API 協議 | `openai-completions` |
| Base URL | `https://maas-coding-api.cn-huabei-1.xf-yun.com/v2` |
| Model ID | `astron-code-latest` |
| Context Window | 128,000 |
| Max Output Tokens | 32,768 |
| Provider Timeout | 600s |
| Agent Timeout | 600s |
| Fallback | `ollama/qwen2.5:3b` |
| 計費 | Coding Plan 免費，成本=0，不追蹤 estimatedCostUsd |

## 二、Agent 運行參數

| 參數 | 值 | 說明 |
|------|-----|------|
| `reserveTokensFloor` | 24,000 | Compaction 觸發閾值 = 128K - 24K = 104K（81%觸發） |
| `keepRecentTokens` | 8,000 | Compaction 保留最近 8K tokens |
| `timeoutSeconds` | 600 | Agent 整體運行超時 |
| `blockStreamingDefault` | on | 微信不支援 edit message，用 block 模式 |
| `blockStreamingBreak` | text_end | 分段發送斷點 |
| `memorySearch.provider` | ollama | 本地 embedding |
| `memorySearch.model` | nomic-embed-text | 274MB，本地運行 |
| `memoryFlush.enabled` | true | Compaction 時自動整理記憶 |
| `memoryFlush.model` | 讯飞星火/astron-code-latest | 用訊飛做記憶整理 |
| `memoryFlush.forceFlushTranscriptBytes` | 2mb | 超過 2MB 強制 flush |

## 三、已知問題與修復歷史

### 問題 1：Token 計數不可靠
- **現象**：API 回報 input tokens 波動極大（曾報 1.5M）
- **影響**：不能依賴 API 回報的自動偵測，OpenClaw 內部計數為準
- **狀態**：✅ 已知，無法修復（訊飛 API 側問題），用 OpenClaw 自行計數繞過

### 問題 2：Compaction 不觸發
- **現象**：auto-compaction 經常不觸發，對話到上限才爆
- **根因**：
  1. `reserveTokensFloor` 原設 65,536，觸發閾值 = 200K - 65K = 135K（67%才觸發）
  2. `contextWindow` 原未聲明，OpenClaw 以為是 200K，實際 128K
- **修復**（2026-07-27）：
  - `reserveTokensFloor`: 65,536 → 20,000（後調整為 24,000）
  - `contextWindow`: 未設定 → 128,000
- **狀態**：✅ 已修復

### 問題 3：API 超時
- **現象**：偶爾響應慢，報 `The model did not produce a response before the model idle timeout`
- **修復**（2026-07-28）：
  - `models.providers.讯飞星火.timeoutSeconds`: 默認 → 120 → 600
  - `agents.defaults.timeoutSeconds`: 默認 → 180 → 600
- **狀態**：✅ 已修復

### 問題 4：微信串流不相容
- **現象**：微信沒有 edit message API，streaming 模式會發重複訊息
- **修復**：`blockStreamingDefault: on`，`blockStreamingBreak: text_end`
- **狀態**：✅ 已修復

### 問題 5：Cron 搶配額
- **現象**：01:00 多個任務同時跑會搶訊飛星火配額
- **修復**：深夜流水線合併為單一任務（Wiki審查→訊飛探測→記憶整理）
- **狀態**：✅ 已修復

## 四、數據收集體系

### 數據源

| 數據源 | 路徑/方式 | 採集頻率 |
|--------|----------|---------|
| sessions.json | `/vol1/@apphome/trim.openclaw/data/home/.openclaw/agents/main/sessions/sessions.json` | 每5分鐘 |
| Wiki Benchmark | Redis DB1 `tg:wiki-benchmark:result` | 每5分鐘 |
| 訊飛 API 探測 | HTTP POST 到訊飛 API（假 key，401=可達） | 每5分鐘 |
| Grafana 告警 | Redis DB1 `grafana:alerts` hash | 每5分鐘 |

### sessions.json 記錄的字段

| 字段 | 說明 | 已推送 Grafana？ |
|------|------|-----------------|
| totalTokens | 總 token 數 | ✅ |
| inputTokens | 輸入 tokens | ✅ |
| outputTokens | 輸出 tokens | ✅ |
| cacheRead | 快取讀取 tokens | ✅ |
| cacheWrite | 快取寫入 tokens | ✅ |
| compactionCount | Compaction 次數 | ✅ |
| runtimeMs | 運行時間（ms） | ✅ → 轉為秒 |
| contextTokens | 上下文窗口大小 | ✅ |
| contextBudgetStatus | 上下文預算狀態 | ❌ 結構複雜，暫不推 |
| estimatedCostUsd | 成本估算 | ❌ Coding Plan=0，無意義 |
| status | Session 狀態 | ❌ |
| model / modelProvider | 使用的模型 | ❌ 作為 label 已包含 |
| totalTokensFresh | Token 數是否新鮮 | ❌ |
| chatType | 對話類型 | ❌ 作為 label 已包含 |

### 推送到 Prometheus 的指標（24個）

**匯總指標：**
- `openclaw_sessions_total` — 總 session 數
- `openclaw_tokens_input_total` — 總 input tokens
- `openclaw_tokens_output_total` — 總 output tokens
- `openclaw_tokens_cache_read_total` — 總 cache read
- `openclaw_tokens_cache_write_total` — 總 cache write
- `openclaw_compaction_total` — 總 compaction 次數
- `openclaw_push_timestamp` — 最後推送時間戳

**各 Session 指標（by session, type）：**
- `openclaw_session_total_tokens`
- `openclaw_session_input_tokens`
- `openclaw_session_output_tokens`
- `openclaw_session_cache_read_tokens`
- `openclaw_session_compaction_count`
- `openclaw_session_runtime_seconds`
- `openclaw_session_context_tokens`

**訊飛 API 探測：**
- `openclaw_xfyun_api_reachable` — 可達性（0/1）
- `openclaw_xfyun_api_response_seconds` — 響應時間
- `openclaw_xfyun_api_status_code` — HTTP 狀態碼

**Wiki 指標（by wiki）：**
- `openclaw_wiki_hit_rate_percent` — 搜尋命中率
- `openclaw_wiki_orphan_pages` — 孤立頁面數
- `openclaw_wiki_cross_ref_density` — 交叉引用密度
- `openclaw_wiki_compliance_rate_percent` — 合規率
- `openclaw_wiki_stale_pages` — 過時頁面數
- `openclaw_wiki_total_tokens` — Token 估算
- `openclaw_wiki_benchmark_last_run_timestamp` — Benchmark 最後運行時間

**Grafana 告警（by alertname, severity）：**
- `openclaw_grafana_alert` — 告警狀態值

### 推送鏈路

```
sessions.json ─┐
Redis DB1 ─────┤→ push_metrics.py → Pushgateway(:9091) → Prometheus(:9090) → Grafana(:3000)
訊飛 API ──────┤     (每5分鐘 cron)
Grafana 告警 ──┘
```

## 五、監控與告警

### Prometheus 告警規則

| 規則 | 條件 | 嚴重程度 | 說明 |
|------|------|---------|------|
| OpenClawDataStale | `time() - openclaw_push_timestamp > 600` | warning | 推送超10分鐘未更新 |
| XfyunAPIDown | `openclaw_xfyun_api_reachable == 0` | critical | 訊飛 API 不可達 |
| WikiHitRateLow | `openclaw_wiki_hit_rate_percent < 70` | warning | Wiki 命中率過低 |

配置路徑：`/vol1/@appshare/prometheus/prometheus/alert_rules.yml`

### 告警通知鏈路

```
Prometheus 告警 → Grafana Contact Point(OpenClaw Webhook)
  → Webhook 接收器(:15010) → Redis DB1(grafana:alerts hash)
  → push_metrics.py 讀取 → openclaw_grafana_alert 指標
  → 心跳檢查 → 微信推送
```

### Grafana Dashboard

- Dashboard UID: `fnos-nas`
- 總面板: 46，其中 OpenClaw 相關: 14-16
- 數據源 UID: Prometheus=`cftjkd0m8y29sa`，Loki=`P8E80F9AEF21F6940`

### Webhook 服務

- 腳本：`scripts/grafana_webhook.py`
- 端口：15010
- 進程：後台運行中（PID 983707）
- ⚠️ @reboot 自啟未配置（需手動啟動或另建機制）

## 六、Cron 排程（訊飛適配相關）

| ID | 名稱 | 排程 | 類型 | 說明 |
|----|------|------|------|------|
| `0d936b13` | Push Metrics | */5 分鐘 | command | 採集指標推 Grafana，不消耗 token |

> 深夜流水線（01:00）和早安報告（07:00）是業務任務，只是碰巧用訊飛模型，不屬於適配優化範疇。

## 七、腳本清單

| 腳本 | 路徑 | 用途 |
|------|------|------|
| push_metrics.py | `scripts/push_metrics.py` | 每5分鐘採集4個數據源（sessions.json token用量、Redis Wiki Benchmark結果、訊飛API探測、Redis Grafana告警），推送24個指標到 Pushgateway |
| grafana_webhook.py | `scripts/grafana_webhook.py` | HTTP服務器（端口15010），接收Grafana告警POST，解析後寫入Redis DB1 `grafana:alerts`，已恢復告警自動清理 |
| wiki-benchmark.sh | `king-wiki-js/_internal/wiki-benchmark.sh` | Wiki健康度基準測試 — 搜尋命中率、交叉引用密度、孤立頁面、合規率、過時頁面、token估算，結果寫Redis供push_metrics.py讀取 |

> `redis_task_guard.py` 和 `heartbeat_guard.py` 是通用基礎設施（去重/限流/快取），不屬於訊飛適配範疇。

## 八、基礎設施依賴

| 服務 | 端口 | 說明 |
|------|------|------|
| Prometheus | 9090 | 指標存儲，180天保留 |
| Pushgateway | 9091 | 臨時指標接收（Docker, host網路） |
| Grafana | 3000 | 可視化（Docker, host網路） |
| Loki | 3100 | 日誌存儲，30天保留 |
| Alloy | 12345 | 日誌收集 |
| Redis | 6379 | DB0=SearXNG快取, DB1=TaskGuard+告警 |
| SearXNG | 8080 | 本地搜索引擎 |
| Ollama | 11434 | 本地 embedding（nomic-embed-text） |
| Webhook | 15010 | Grafana 告警接收 |

## 九、待辦 / 改進方向

- [ ] Webhook @reboot 自啟機制（目前手動啟動）
- [ ] 告警微信推送實際觸發測試（鏈路已通但未模擬真實告警）
- [ ] contextBudgetStatus 結構化推送（目前太複雜暫不推）
- [ ] 考慮即時推送（每次對話結束推送，而非等5分鐘 cron）
- [ ] 訊飛收費後啟用 estimatedCostUsd 追蹤
