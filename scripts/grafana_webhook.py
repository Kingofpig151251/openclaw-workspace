#!/usr/bin/env python3
"""极简 Grafana Alert webhook 接收器，写入 Redis DB1"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import redis

REDIS_KEY = "grafana:alerts"
REDIS_DB = 1

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            # Grafana 统一告警格式
            alerts = data.get('alerts', [data])
            r = redis.Redis(host='localhost', port=6379, db=REDIS_DB, decode_responses=True)
            
            for alert in alerts:
                status = alert.get('status', 'firing')
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})
                alertname = labels.get('alertname', 'Unknown')
                
                alert_data = {
                    'alertname': alertname,
                    'status': status,
                    'severity': labels.get('severity', 'info'),
                    'summary': annotations.get('summary', ''),
                    'description': annotations.get('description', ''),
                    'firedAt': alert.get('activeAt', alert.get('startsAt', '')),
                    'timestamp': time.time()
                }
                
                # 用 alertname 作为 hash field，自动覆盖（只保留最新状态）
                r.hset(REDIS_KEY, alertname, json.dumps(alert_data, ensure_ascii=False))
            
            # 清理已恢复的告警
            if data.get('status') == 'resolved' or data.get('title', '').endswith('Resolved'):
                for alert in alerts:
                    alertname = alert.get('labels', {}).get('alertname', '')
                    if alertname and alert.get('status') == 'resolved':
                        r.hdel(REDIS_KEY, alertname)
            
            print(f"[{time.strftime('%H:%M:%S')}] Received: {len(alerts)} alerts")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")
        
        # 始终返回 200
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def log_message(self, format, *args):
        pass  # 静默日志

if __name__ == '__main__':
    port = 15010
    server = HTTPServer(('127.0.0.1', port), WebhookHandler)
    print(f"Webhook receiver listening on 127.0.0.1:{port}")
    server.serve_forever()
