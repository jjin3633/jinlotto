import os
import json
import time
import requests
from datetime import datetime, timezone

MON_DIR = os.path.dirname(__file__)
SAMPLES = os.path.join(MON_DIR, 'samples.jsonl')
SERVICE_URL = os.getenv('SERVICE_URL', 'https://jinlotto.onrender.com')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK_URL')

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat()

def post_slack(text):
    if not SLACK_WEBHOOK:
        print('No SLACK_WEBHOOK_URL')
        return
    try:
        requests.post(SLACK_WEBHOOK, json={'text': text}, timeout=10)
    except Exception as e:
        print('Slack post failed', e)

def check_health():
    url = SERVICE_URL.rstrip('/') + '/api/health'
    try:
        r = requests.get(url, timeout=10)
        return r.status_code, r.text[:1000]
    except Exception as e:
        return None, str(e)

def check_predict():
    url = SERVICE_URL.rstrip('/') + '/api/predict'
    try:
        r = requests.post(url, json={'num_sets':1}, timeout=15)
        return r.status_code, (r.text[:2000] if r.text else '')
    except Exception as e:
        return None, str(e)

def main():
    hc, hbody = check_health()
    pc, pbody = check_predict()
    sample = {
        'ts': now_iso(),
        'health_status': hc,
        'health_body_snippet': hbody,
        'predict_status': pc,
        'predict_body_snippet': pbody
    }
    with open(SAMPLES, 'a', encoding='utf-8') as f:
        f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print('sample recorded', sample)
    if pc is None or pc >= 500 or hc is None or (hc >= 500):
        post_slack(f":warning: JinLotto alert at {sample['ts']} — predict_status={pc} health_status={hc}")

if __name__ == '__main__':
    main()


