# Heartbeat 任務

## 每次心跳（輕量檢查）

- [ ] 跑 wiki benchmark：`bash /vol1/@apphome/trim.openclaw/data/workspace/king-wiki-js/_internal/wiki-benchmark.sh`
- [ ] 搜尋命中率 < 70% → 自動改善 index.md 摘要（補關鍵詞）
- [ ] 跑 wiki benchmark：`bash /vol1/@apphome/trim.openclaw/data/workspace/king-wiki-js/_internal/wiki-benchmark.sh`
- [ ] 搜尋命中率 < 70% → 自動改善 index.md 摘要（補關鍵詞）
- [ ] description 太長(>80字) → 自動截短至30-60字
- [ ] 缺 frontmatter 欄位 → 自動補
- [ ] tags 首位不合規 → 自動修正
- [ ] 有過時頁面(>30天) → 標記到 contradictions.md
- [ ] Ingest 深度異常低 → 提醒小king
- [ ] 檢查 Grafana 告警：`curl -s 'http://127.0.0.1:9090/api/v1/query?query=openclaw_grafana_alert' | python3 -c "import sys,json; d=json.load(sys.stdin); alerts=[r for r in d['data']['result'] if float(r['value'][1])>0]; print(f'{len(alerts)}條告警') if not alerts else [print(f'⚠️ {a["metric"]["alertname"]}: {a["metric"].get("severity","?")}') for a in alerts]"`
- [ ] 有告警 → 推微信通知小king（含告警名稱、嚴重程度、描述）
- [ ] 結果只在小king在線且有事要報告時才推，沒事就 HEARTBEAT_OK

## 每週深度審查（週一或首次心跳時執行）

- [ ] 檢查上次深度審查日期（記在下方 state），若 >7天則執行
- [ ] **導航完整性**：新頁面是否都加了導航頁連結？
- [ ] **主題索引覆蓋**：index.md 主題索引是否包含所有新頁面？
- [ ] **Orphan 頁面掃描**：有沒有頁面沒被任何頁面連結？
- [ ] **交叉引用密度**：密度 <5 連結/頁面 → 補雙向連結
- [ ] **矛盾掃描**：不同頁面間是否有互相矛盾的聲明？
- [ ] **概念缺口**：多次出現但沒有獨立頁面的概念？
- [ ] **work/ 佔比**：超過全庫 40% → 標記需關注
- [ ] **洞察區膨脹**：超過 5-6 篇 → 考慮合併相近的
- [ ] **超大頁面**：>100行 → 考慮拆分
- [ ] 執行完更新下方 state 日期

## 自動修復規則（心跳可安全執行，不需確認）

- description 太長 → 截短至30-60字，保留具體名詞
- 缺 frontmatter → 根據頁面內容自動補
- tags 首位不合規 → 改為分類名
- 導航頁漏連結 → 自動補上
- 搜尋命中率下降 → 補 index.md 關鍵詞
- orphan 頁面 → 在相關導航頁加連結

## 需要小king確認才執行

- 刪除/合併頁面
- 修改實質內容（非格式/結構性修改）
- 標記矛盾（需確認哪個版本正確）
- 建立新洞察頁面

## State

```json
{
  "lastDeepAudit": "2026-07-27",
  "lastBenchmarkHitRate": "100%",
  "lastBenchmarkTokens": 105027,
  "lastMailSync": "down — agently-cli OAuth expired since 7/28, 4+ auth links sent 7/29-7/30, awaiting 小king re-auth"
}
```
