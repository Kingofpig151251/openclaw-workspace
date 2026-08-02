# Heartbeat 任務

## 每次心跳（每 2 小時）

- [ ] 檢查 Grafana 告警：`curl -s 'http://127.0.0.1:9090/api/v1/query?query=openclaw_grafana_alert' | python3 -c "import sys,json; d=json.load(sys.stdin); alerts=[r for r in d['data']['result'] if float(r['value'][1])>0]; print(f'{len(alerts)}條告警') if not alerts else [print(f'⚠️ {a[\"metric\"][\"alertname\"]}: {a[\"metric\"].get(\"severity\",\"?\")}') for a in alerts]"`
- [ ] 有告警 → 推微信通知小king
- [ ] 無事 → HEARTBEAT_OK

## 規則

- 08:00-24:00 才跑，深夜不打擾
- 用 auto 模型，不消耗 xopglm52 額度
- 無事不報告，有告警才通知
