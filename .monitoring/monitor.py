#!/usr/bin/env python3
"""Simple monitor for JinLotto service.

Polls service health and predict endpoints and posts alerts to Slack when
failure or thresholds occur. Stores time-series samples under .monitoring/.

Requires env vars:
- RENDER_API_KEY: Render API key (read-only)
- SLACK_WEBHOOK_URL: Slack incoming webhook URL
- SERVICE_ID: Render service id (optional, discovery used if absent)
- SERVICE_URL: Base URL of service e.g. https://jinlotto.onrender.com

Run: python .monitoring/monitor.py
"""
import os
import time
import json
import requests
from datetime import datetime, timezone

MON_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(MON_DIR, exist_ok=True)

RENDER_API_KEY = os.getenv('RENDER_API_KEY')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')
SERVICE_ID = os.getenv('SERVICE_ID')
SERVICE_URL = os.getenv('SERVICE_URL', 'https://jinlotto.onrender.com')

INTERVAL = int(os.getenv('MON_INTERVAL_SECONDS', '600'))
TIMEOUT = int(os.getenv('MON_HTTP_TIMEOUT', '15'))

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()

def post_slack(text):
    if not SLACK_WEBHOOK:
        return
    payload = {"text": text}
    try:
        requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
    except Exception:
        pass

def check_health():
    url = SERVICE_URL.rstrip('/') + '/api/health'
    t0 = time.time()
    try:
        r = requests.get(url, timeout=TIMEOUT)
        dt = time.time() - t0
        return r.status_code, r.text[:1000], dt
    except Exception as e:
        return None, str(e), None

def check_predict():
    url = SERVICE_URL.rstrip('/') + '/api/predict'
    headers = {'Content-Type': 'application/json'}
    payload = {'num_sets': 1}
    t0 = time.time()
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        dt = time.time() - t0
        return r.status_code, (r.text[:2000] if r.text else ''), dt
    except Exception as e:
        return None, str(e), None

def sample_one():
    hc, hbody, hdt = check_health()
    pc, pbody, pdt = check_predict()
    sample = {
        'ts': now_iso(),
        'health_status': hc,
        'health_body_snippet': hbody,
        'health_ms': None if hdt is None else round(hdt*1000,1),
        'predict_status': pc,
        'predict_body_snippet': pbody,
        'predict_ms': None if pdt is None else round(pdt*1000,1)
    }
    fn = os.path.join(MON_DIR, 'samples.jsonl')
    with open(fn, 'a', encoding='utf-8') as f:
        f.write(json.dumps(sample, ensure_ascii=False) + '\n')

    # immediate alerting rules
    if pc is None or pc >= 500 or hc is None or (hc >= 500):
        post_slack(f":warning: JinLotto alert at {sample['ts']} — predict_status={pc} health_status={hc}")
    if pdt is not None and pdt > 10.0:
        post_slack(f":hourglass_flowing_sand: JinLotto slow response at {sample['ts']} — predict {round(pdt,1)}s")

def discover_service_id():
    if SERVICE_ID:
        return SERVICE_ID
    if not RENDER_API_KEY:
        return None
    try:
        headers = {'Authorization': f'Bearer {RENDER_API_KEY}'}
        r = requests.get('https://api.render.com/v1/services', headers=headers, timeout=10)
        r.raise_for_status()
        items = r.json()
        for it in items:
            svc = it.get('service') or it
            if svc.get('name') == 'jinlotto' or svc.get('slug') == 'jinlotto':
                return svc.get('id')
    except Exception:
        pass
    return None

def main_loop():
    post_slack(':white_check_mark: JinLotto monitor started')
    svc = discover_service_id()
    if svc:
        print('monitoring service id', svc)
    else:
        print('service id not discovered; proceeding with URL checks')

    while True:
        try:
            sample_one()
        except Exception as e:
            post_slack(f":x: Monitor error: {e}")
        time.sleep(INTERVAL)

if __name__ == '__main__':
    if not SLACK_WEBHOOK:
        print('SLACK_WEBHOOK_URL not set; exiting')
    else:
        main_loop()


