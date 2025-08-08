#!/usr/bin/env python3
"""
주간 배치: 최신 로또 당첨 데이터 업데이트 스크립트

Render 크론 또는 외부 스케줄러에서 실행하십시오.
"""
import logging

from app.services.data_service import DataService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> None:
    data_service = DataService()
    logger.info("주간 배치 시작: 최신 로또 데이터 업데이트")
    df = data_service.update_latest_data()
    if df is not None and not df.empty:
        logger.info("배치 완료: 총 %d 회차 (최신: %s)", len(df), int(df['draw_number'].max()))
    else:
        logger.warning("배치 완료: 데이터프레임이 비어있습니다.")


if __name__ == "__main__":
    main()


