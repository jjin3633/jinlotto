#!/usr/bin/env python3
"""
주간 배치: 최신 로또 당첨 데이터 업데이트 스크립트

Render 크론 또는 외부 스케줄러에서 실행하십시오.
"""
import logging
import os
import json
import traceback
import requests

# Render 크론에서 루트 기준으로 실행되므로 절대 경로 임포트를 사용
from backend.app.services.data_service import DataService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def post_to_slack(text: str) -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.info("SLACK_WEBHOOK_URL 미설정: Slack 알림을 건너뜁니다.")
        return
    try:
        payload = {"text": text}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Slack 알림 실패: %s", e)


def main() -> None:
    data_service = DataService()
    logger.info("주간 배치 시작: 최신 로또 데이터 업데이트")
    try:
        df = data_service.update_latest_data()
        if df is not None and not df.empty:
            latest_draw = int(df['draw_number'].max())
            start_draw = int(df['draw_number'].min())
            total = len(df)
            msg = f"✅ 로또 데이터 주간 업데이트 완료\n- 보유 회차: {start_draw} ~ {latest_draw} (총 {total})"
            logger.info(msg)
            post_to_slack(msg)
        else:
            msg = "⚠️ 주간 업데이트 완료: 데이터프레임이 비어있습니다."
            logger.warning(msg)
            post_to_slack(msg)
    except Exception as e:
        err = f"❌ 로또 데이터 주간 업데이트 실패: {e}\n``{traceback.format_exc()}``"
        logger.error(err)
        post_to_slack(err)


if __name__ == "__main__":
    main()


