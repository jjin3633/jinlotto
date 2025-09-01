#!/usr/bin/env python3
"""
헬스 모니터: 주기적으로 /api/health 체크 후 장애/복구를 Slack으로 통보

필요 환경변수:
  - MONITOR_BASE_URL: 배포된 서비스의 베이스 URL (예: https://jinlotto.onrender.com)
  - SLACK_WEBHOOK_URL: Slack Incoming Webhook URL
"""
import os
import json
import logging
import requests
from pathlib import Path


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STATE_FILE = Path("/tmp/jinlotto_health_state.txt")


def post_to_slack(text: str) -> None:
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        logger.info("SLACK_WEBHOOK_URL 미설정: Slack 알림 생략")
        return
    try:
        resp = requests.post(url, data=json.dumps({"text": text}), headers={"Content-Type": "application/json"}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Slack 전송 실패: %s", e)


def read_last_state() -> str:
    try:
        if STATE_FILE.exists():
            return STATE_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return "UNKNOWN"


def write_state(state: str) -> None:
    try:
        STATE_FILE.write_text(state, encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    base_url = os.environ.get("MONITOR_BASE_URL")
    if not base_url:
        logger.error("MONITOR_BASE_URL 미설정: 종료")
        return

    health_url = base_url.rstrip("/") + "/api/health"

    try:
        r = requests.get(health_url, timeout=8)
        ok = r.status_code == 200
    except Exception:
        ok = False

    last = read_last_state()
    if ok:
        logger.info("헬스체크 OK: %s", health_url)
        if last in ("DOWN", "UNKNOWN"):
            post_to_slack("✅ 서버 복구: 서비스가 정상 응답합니다")
        write_state("UP")
    else:
        logger.warning("헬스체크 실패: %s", health_url)
        if last != "DOWN":
            post_to_slack("❌ 서버 장애: /api/health 응답 실패 또는 상태 비정상")
        write_state("DOWN")


if __name__ == "__main__":
    main()


