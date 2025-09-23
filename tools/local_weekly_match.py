#!/usr/bin/env python3
"""로컬에서 주기 실행할 수 있는 스크립트
- Supabase predictions 테이블에서 예측을 조회
- /api/data/latest에서 최신 회차를 조회하여 1~5등 카운트 집계
- Slack Webhook으로 요약 전송

환경변수:
 - SUPABASE_URL
 - SUPABASE_ANON_KEY
 - SLACK_WEBHOOK_URL (옵션)
 - MONITOR_BASE_URL (옵션, 기본 https://stretchinglotto.motiphysio.com/)

사용법(테스트):
 $ export SUPABASE_URL=... SUPABASE_ANON_KEY=... SLACK_WEBHOOK_URL=... \
   && python tools/local_weekly_match.py
"""

import os
import sys
import json
from typing import List, Dict

try:
    from supabase import create_client
except Exception as e:
    print("supabase client not installed. pip install supabase", file=sys.stderr)
    raise

import requests


def compute_rank(user_numbers: List[int], draw_numbers: List[int], bonus: int) -> int:
    user_set = set(int(x) for x in user_numbers)
    draw_set = set(int(x) for x in draw_numbers)
    matched = user_set & draw_set
    match_count = len(matched)
    bonus_match = int(bonus) in user_set
    if match_count == 6:
        return 1
    if match_count == 5 and bonus_match:
        return 2
    if match_count == 5:
        return 3
    if match_count == 4:
        return 4
    if match_count == 3:
        return 5
    return 0


def main():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    MONITOR_BASE = os.getenv("MONITOR_BASE_URL", "https://stretchinglotto.motiphysio.com/")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Missing SUPABASE_URL or SUPABASE_ANON_KEY", file=sys.stderr)
        return 2

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # predictions 가져오기
    try:
        preds_res = client.from_("predictions").select("*").execute()
        preds = getattr(preds_res, "data", []) or []
    except Exception as e:
        print("Failed to fetch predictions:", e, file=sys.stderr)
        return 3

    # 최신 회차 반영: 서버의 /api/data/update를 호출해 CSV/DB 동기화 시도한 뒤 최신 회차 조회
    try:
        update_url = f"{MONITOR_BASE.rstrip('/')}/api/data/update"
        headers = {}
        mon_token = os.getenv("MONITOR_SCHEDULER_TOKEN") or os.getenv("SCHEDULER_TOKEN")
        if mon_token:
            headers["X-Scheduler-Token"] = mon_token
        try:
            up = requests.post(update_url, headers=headers, timeout=120)
            if up.status_code != 200:
                # 경고만 출력; 계속해서 최신 회차 조회 시도
                print(f"Warning: /api/data/update returned status {up.status_code}", file=sys.stderr)
        except Exception as e:
            print("Warning: failed to call /api/data/update:", e, file=sys.stderr)

        # 최신 회차 조회
        r = requests.get(f"{MONITOR_BASE.rstrip('/')}/api/data/latest", timeout=30)
        r.raise_for_status()
        latest = r.json().get("data") or {}
    except Exception as e:
        print("Failed to fetch latest draw:", e, file=sys.stderr)
        return 4

    if not latest:
        print("No latest draw found", file=sys.stderr)
        return 5

    try:
        draw_number = int(latest.get("draw_number"))
        draw_numbers = [
            int(latest.get("number_1", 0)),
            int(latest.get("number_2", 0)),
            int(latest.get("number_3", 0)),
            int(latest.get("number_4", 0)),
            int(latest.get("number_5", 0)),
            int(latest.get("number_6", 0)),
        ]
        bonus = int(latest.get("bonus_number", 0))
    except Exception as e:
        print("Invalid latest draw schema:", e, file=sys.stderr)
        return 6

    counts: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for p in preds:
        nums = p.get("numbers")
        if isinstance(nums, list) and len(nums) >= 6:
            try:
                rank = compute_rank(nums[:6], draw_numbers, bonus)
                if rank in counts:
                    counts[rank] += 1
            except Exception:
                continue

    message = (
        f"📣 회차 {draw_number} 결과 요약\n"
        f"1등: {counts[1]}\n2등: {counts[2]}\n3등: {counts[3]}\n4등: {counts[4]}\n5등: {counts[5]}"
    )

    if SLACK_WEBHOOK_URL:
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
            print("Slack sent")
        except Exception as e:
            print("Failed to post Slack:", e, file=sys.stderr)
            print(message)
            return 7
    else:
        print(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())


