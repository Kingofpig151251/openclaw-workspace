#!/usr/bin/env python3
"""
訊飛星火模型上下文窗口測試腳本
在深夜流水線中運行，逐步測試每個模型實際支持的上下文長度。

策略：
1. 發送 progressively 更長的 prompt（4K → 8K → 16K → 32K → 64K → 128K → 256K → 512K）
2. 如果某個長度成功，記錄並繼續加大
3. 如果失敗（context length exceeded），記錄最大成功長度
4. 結果寫入 PostgreSQL 和 JSON 文件

用法：
  .venv/bin/python scripts/xfyun-model-context-test.py [--model MODEL_ID] [--quick]
  --model: 只測指定模型，不指定則全部測
  --quick: 只測 4K/16K/64K/128K 四個檔位
"""

import json
import time
import sys
import os
import urllib.request
import urllib.error
import psycopg2
from datetime import datetime

# === 配置 ===
CONFIG_PATH = "/vol1/@apphome/trim.openclaw/data/home/.openclaw/openclaw.json"
RESULT_PATH = "/vol1/@apphome/trim.openclaw/data/workspace/memory/xfyun-model-context-results.json"
PG_DSN = "host=127.0.0.1 port=5433 dbname=thoth user=thoth password=***"

# 測試的 token 檔位
FULL_THRESHOLDS = [4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]
QUICK_THRESHOLDS = [4096, 16384, 65536, 131072]

# 填充用的無意義文本（每行約 20 tokens）
FILLER_LINE = "This is a context window test. The quick brown fox jumps over the lazy dog. "
FILLER_BLOCK = (FILLER_LINE * 50 + "\n")  # ~1000 chars ≈ ~250 tokens per block


def load_config():
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    provider = cfg['models']['providers']['訊飛星火']
    return provider['apiKey'], provider['baseUrl']


def estimate_tokens(text):
    """粗略估算 token 數：英文約 4 chars/token"""
    return len(text) // 4


def build_prompt(target_tokens):
    """構建指定大小的 prompt"""
    # 系統提示 + 填充 + 簡單問題
    blocks_needed = target_tokens // 250 + 1
    filler = FILLER_BLOCK * blocks_needed
    actual_tokens = estimate_tokens(filler)
    
    return [
        {"role": "system", "content": "You are a helpful assistant. Please respond briefly."},
        {"role": "user", "content": filler + "\n\nPlease reply with 'OK' and the approximate token count you received."}
    ], actual_tokens


def test_model(api_key, base_url, model_id, target_tokens, timeout=30):
    """測試某個模型在指定 token 數下是否正常回應"""
    messages, actual_tokens = build_prompt(target_tokens)
    
    payload = json.dumps({
        "model": model_id,
        "messages": messages,
        "max_tokens": 20,
        "temperature": 0.1
    }).encode()
    
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            elapsed = time.time() - start
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = data.get('usage', {})
            return {
                "success": True,
                "actual_tokens": actual_tokens,
                "elapsed_s": round(elapsed, 1),
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "response": content[:100]
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')[:200]
        return {
            "success": False,
            "actual_tokens": actual_tokens,
            "error": f"HTTP {e.code}: {body}",
            "error_type": "http_error"
        }
    except Exception as e:
        return {
            "success": False,
            "actual_tokens": actual_tokens,
            "error": str(e)[:200],
            "error_type": type(e).__name__
        }


def get_all_models(api_key, base_url):
    """從配置獲取所有模型 ID"""
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    models = cfg['models']['providers']['訊飛星火']['models']
    return [(m['id'], m.get('contextWindow', 128000)) for m in models]


def save_results(results):
    """保存結果到 JSON 文件"""
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"📄 結果已保存到 {RESULT_PATH}")


def save_to_db(results):
    """保存結果到 PostgreSQL"""
    try:
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor()
        
        # 建表（如果不存在）
        cur.execute("""
            CREATE TABLE IF NOT EXISTS xfyun_model_context_tests (
                id SERIAL PRIMARY KEY,
                model_id TEXT NOT NULL,
                tested_at TIMESTAMP DEFAULT NOW(),
                max_success_tokens INTEGER,
                config_context_window INTEGER,
                tested_thresholds JSONB,
                status TEXT,
                notes TEXT
            )
        """)
        
        for model_id, data in results.items():
            cur.execute("""
                INSERT INTO xfyun_model_context_tests 
                (model_id, max_success_tokens, config_context_window, tested_thresholds, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                model_id,
                data.get('max_success_tokens'),
                data.get('config_context_window'),
                json.dumps(data.get('thresholds', {})),
                data.get('status', 'unknown'),
                data.get('notes', '')
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        print("📊 結果已寫入 PostgreSQL")
    except Exception as e:
        print(f"⚠️ DB 寫入失敗: {e}")


def main():
    api_key, base_url = load_config()
    
    # 參數解析
    target_model = None
    quick = False
    for arg in sys.argv[1:]:
        if arg == '--quick':
            quick = True
        elif arg == '--model':
            pass
        elif sys.argv.index(arg) > 0 and sys.argv[sys.argv.index(arg)-1] == '--model':
            target_model = arg
    
    thresholds = QUICK_THRESHOLDS if quick else FULL_THRESHOLDS
    models = get_all_models(api_key, base_url)
    
    if target_model:
        models = [(m, cw) for m, cw in models if m == target_model]
        if not models:
            print(f"❌ 模型 {target_model} 不在配置中")
            return
    
    print(f"🧪 訊飛星火模型上下文窗口測試")
    print(f"   模型數: {len(models)}")
    print(f"   測試檔位: {thresholds}")
    print(f"   模式: {'快速' if quick else '完整'}")
    print(f"   時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    for model_id, config_cw in models:
        print(f"\n{'='*60}")
        print(f"📋 測試模型: {model_id} (配置 contextWindow={config_cw})")
        print(f"{'='*60}")
        
        model_result = {
            "model_id": model_id,
            "config_context_window": config_cw,
            "thresholds": {},
            "max_success_tokens": 0,
            "status": "unknown",
            "notes": ""
        }
        
        max_success = 0
        last_error = ""
        
        for threshold in thresholds:
            # 如果配置的 contextWindow 比 threshold 小，跳過
            if threshold > config_cw * 2:  # 允許測到 2 倍配置值
                print(f"  ⏭️  {threshold:>7d} tokens — 超過配置的 2 倍，跳過")
                model_result["thresholds"][str(threshold)] = {"status": "skipped", "reason": "exceeds 2x config"}
                continue
            
            print(f"  🔄 測試 {threshold:>7d} tokens...", end=" ", flush=True)
            
            # 對大 token 數增加超時
            timeout = max(30, threshold // 2048)
            result = test_model(api_key, base_url, model_id, threshold, timeout=timeout)
            
            if result["success"]:
                print(f"✅ ({result['elapsed_s']}s, prompt_tokens={result['prompt_tokens']})")
                model_result["thresholds"][str(threshold)] = {
                    "status": "success",
                    "elapsed_s": result["elapsed_s"],
                    "prompt_tokens": result["prompt_tokens"],
                    "response": result["response"]
                }
                max_success = threshold
            else:
                error_short = result.get("error", "?")[:80]
                print(f"❌ {error_short}")
                model_result["thresholds"][str(threshold)] = {
                    "status": "failed",
                    "error": result.get("error", ""),
                    "error_type": result.get("error_type", "")
                }
                last_error = error_short
                break  # 失敗就不再繼續加大
            
            # 避免限流
            time.sleep(2)
        
        model_result["max_success_tokens"] = max_success
        
        if max_success == 0:
            model_result["status"] = "failed"
            model_result["notes"] = f"所有檔位都失敗。最後錯誤: {last_error}"
        elif max_success >= thresholds[-1]:
            model_result["status"] = "max_reached"
            model_result["notes"] = f"達到最大測試檔位 {max_success} tokens，可能支持更大"
        else:
            model_result["status"] = "measured"
            model_result["notes"] = f"最大支持 {max_success} tokens"
        
        results[model_id] = model_result
        
        print(f"\n  📊 結果: {model_result['status']} — {model_result['notes']}")
    
    # 匯總
    print(f"\n{'='*60}")
    print(f"📋 測試匯總")
    print(f"{'='*60}")
    print(f"{'模型':<25s} {'最大成功':>10s} {'配置值':>10s} {'狀態':>12s}")
    print("-" * 60)
    for model_id, data in results.items():
        print(f"{model_id:<25s} {data['max_success_tokens']:>10d} {data['config_context_window']:>10d} {data['status']:>12s}")
    
    # 保存結果
    save_results(results)
    save_to_db(results)
    
    # 生成配置更新建議
    print(f"\n💡 配置更新建議:")
    for model_id, data in results.items():
        if data['status'] == 'measured' and data['max_success_tokens'] != data['config_context_window']:
            print(f"  {model_id}: {data['config_context_window']} → {data['max_success_tokens']}")


if __name__ == '__main__':
    main()
