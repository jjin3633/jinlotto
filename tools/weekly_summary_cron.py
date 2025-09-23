#!/usr/bin/env python3
"""
매주 월요일 오전 10시 KST 자동 실행되는 로또 결과 요약 스크립트

기능:
- 최신 회차의 정확한 기간별 필터링 매칭 결과
- 슬랙으로 이모지 포함 예쁜 형태로 전송
- 한국 시간 기준 매주 월요일 오전 10시 실행

환경변수:
- SUPABASE_URL: Supabase 프로젝트 URL
- SUPABASE_ANON_KEY: Supabase 익명 키  
- SLACK_WEBHOOK_URL: Slack 웹훅 URL
 - MONITOR_BASE_URL: 서버 베이스 URL (기본: https://stretchinglotto.motiphysio.com/)

Render Cron 설정:
schedule: "0 1 * * 1"  # 매주 월요일 01:00 UTC = 10:00 KST
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

try:
    from supabase import create_client
except Exception as e:
    print("supabase client not installed. pip install supabase", file=sys.stderr)
    raise


def compute_rank(user_numbers: List[int], draw_numbers: List[int], bonus: int) -> int:
    """로또 등수 계산"""
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


def get_latest_draw_info() -> Optional[Dict]:
    """최신 회차 정보 조회"""
    try:
        # 서버 API에서 최신 회차 조회
        monitor_base = os.getenv("MONITOR_BASE_URL", "https://stretchinglotto.motiphysio.com/")
        response = requests.get(f"{monitor_base.rstrip('/')}/api/data/latest", timeout=30)
        
        if response.status_code == 200:
            latest_data = response.json().get("data", {})
            if latest_data:
                return {
                    'draw_number': latest_data.get("draw_number"),
                    'draw_date': latest_data.get("draw_date"),
                    'numbers': [
                        latest_data.get("number_1"), latest_data.get("number_2"),
                        latest_data.get("number_3"), latest_data.get("number_4"),
                        latest_data.get("number_5"), latest_data.get("number_6")
                    ],
                    'bonus_number': latest_data.get("bonus_number")
                }
        
        # 서버 실패 시 동행복권 API 직접 호출
        print("⚠️ 서버 API 실패, 동행복권 API 직접 호출", file=sys.stderr)
        
        # 최신 회차 번호 추정 (현재 날짜 기준)
        current_date = datetime.now()
        # 2002년 12월 7일 1회차 기준으로 대략적인 회차 계산
        start_date = datetime(2002, 12, 7)
        weeks_passed = (current_date - start_date).days // 7
        estimated_draw = min(weeks_passed + 1, 1200)  # 최대 1200회차까지 확인
        
        # 최근 회차부터 역순으로 확인
        for draw_no in range(estimated_draw, max(estimated_draw - 10, 1), -1):
            url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
            try:
                resp = requests.get(url, timeout=10)
                data = resp.json()
                if data.get('returnValue') == 'success':
                    return {
                        'draw_number': data['drwNo'],
                        'draw_date': data['drwNoDate'],
                        'numbers': [
                            data['drwtNo1'], data['drwtNo2'], data['drwtNo3'],
                            data['drwtNo4'], data['drwtNo5'], data['drwtNo6']
                        ],
                        'bonus_number': data['bnusNo']
                    }
            except:
                continue
        
        return None
        
    except Exception as e:
        print(f"❌ 최신 회차 조회 실패: {e}", file=sys.stderr)
        return None


def get_filtered_predictions(client, draw_number: int, draw_date: str) -> List[Dict]:
    """정확한 기간별 필터링이 적용된 예측 데이터 조회"""
    try:
        # 추첨일 파싱 (YYYY-MM-DD 형태)
        draw_datetime = datetime.strptime(draw_date, '%Y-%m-%d')
        
        # 토요일 20:00 KST 계산 (새로운 데이터는 KST로 저장됨)
        cutoff_kst = draw_datetime.replace(hour=20, minute=0, second=0, microsecond=0)
        cutoff_utc = draw_datetime.replace(hour=11, minute=0, second=0, microsecond=0)  # 기존 UTC 데이터용
        
        cutoff_kst_iso = cutoff_kst.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        cutoff_utc_iso = cutoff_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        # Supabase 쿼리: 해당 회차용 + 추첨 전 생성된 예측만 (KST/UTC 호환)
        response = client.from_("predictions").select("*").filter(
            "generated_for", "lte", draw_date
        ).or_(
            f"created_at.lte.{cutoff_kst_iso},created_at.lte.{cutoff_utc_iso}"
        ).execute()
        
        preds = getattr(response, "data", []) or []
        
        # 추가 필터링: 정확히 해당 회차용 예측만 (generated_for가 해당 회차 주간에 해당)
        filtered_preds = []
        for p in preds:
            generated_for = p.get('generated_for')
            if generated_for:
                try:
                    gen_date = datetime.strptime(generated_for, '%Y-%m-%d')
                    # 해당 회차 추첨일 기준으로 ±7일 이내 (해당 주간)
                    if abs((gen_date - draw_datetime).days) <= 7:
                        filtered_preds.append(p)
                except:
                    continue
        
        return filtered_preds
        
    except Exception as e:
        print(f"❌ 예측 데이터 조회 실패: {e}", file=sys.stderr)
        return []


def calculate_matches(predictions: List[Dict], draw_numbers: List[int], bonus: int) -> Dict[int, int]:
    """매칭 결과 계산"""
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for p in predictions:
        nums = p.get("numbers")
        if isinstance(nums, list) and len(nums) >= 6:
            try:
                rank = compute_rank(nums[:6], draw_numbers, bonus)
                if rank in counts:
                    counts[rank] += 1
            except Exception:
                continue
    
    return counts


def send_weekly_summary(draw_info: Dict, counts: Dict[int, int], total_predictions: int) -> bool:
    """주간 요약을 슬랙으로 전송 (이모지 포함)"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL 미설정", file=sys.stderr)
        return False
    
    try:
        draw_number = draw_info['draw_number']
        numbers_str = ', '.join(map(str, draw_info['numbers']))
        
        # 요청된 이모지 형태로 메시지 구성
        message = f""":mega: 회차 {draw_number} 정확한 결과 요약 (기간별 필터링)
:dart: 당첨번호: {numbers_str} + 보너스 {draw_info['bonus_number']}
:calendar: 추첨일: {draw_info['draw_date']}

:trophy: 매칭 결과 (총 {total_predictions}개 예측):
1등 (6개 일치): {counts[1]}명
2등 (5개+보너스): {counts[2]}명  
3등 (5개 일치): {counts[3]}명
4등 (4개 일치): {counts[4]}명
5등 (3개 일치): {counts[5]}명

:white_check_mark: 정확한 기간별 필터링 적용됨
:alarm_clock: 추첨 전(토요일 20:00 KST) 생성된 예측만 집계"""
        
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        print("📱 주간 요약 슬랙 전송 성공")
        return True
        
    except Exception as e:
        print(f"❌ 슬랙 전송 실패: {e}", file=sys.stderr)
        return False


def main():
    """메인 함수 - 매주 월요일 오전 10시 KST 실행"""
    print(f"🕙 주간 로또 결과 요약 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 환경변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL 또는 SUPABASE_ANON_KEY가 설정되지 않았습니다.", file=sys.stderr)
        return 2
    
    # Supabase 클라이언트 생성
    try:
        client = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"❌ Supabase 클라이언트 생성 실패: {e}", file=sys.stderr)
        return 3
    
    # 최신 회차 정보 조회
    print("🔍 최신 회차 조회 중...")
    draw_info = get_latest_draw_info()
    if not draw_info:
        print("❌ 최신 회차 정보를 조회할 수 없습니다.", file=sys.stderr)
        return 4
    
    draw_number = draw_info['draw_number']
    print(f"✅ {draw_number}회차 당첨번호: {draw_info['numbers']} + 보너스 {draw_info['bonus_number']}")
    
    # 정확한 기간별 필터링으로 예측 데이터 조회
    print(f"🔍 {draw_number}회차용 예측 데이터 조회 중...")
    predictions = get_filtered_predictions(client, draw_number, draw_info['draw_date'])
    
    # 매칭 결과 계산
    print(f"🎲 매칭 결과 계산 중...")
    counts = calculate_matches(predictions, draw_info['numbers'], draw_info['bonus_number'])
    
    # 결과 출력
    print(f"📊 {draw_number}회차 주간 요약:")
    print(f"   총 예측 수: {len(predictions)}개")
    print(f"   1등: {counts[1]}명, 2등: {counts[2]}명, 3등: {counts[3]}명")
    print(f"   4등: {counts[4]}명, 5등: {counts[5]}명")
    
    # 슬랙 전송
    success = send_weekly_summary(draw_info, counts, len(predictions))
    
    if success:
        print("✅ 주간 요약 완료")
        return 0
    else:
        print("❌ 주간 요약 실패")
        return 5


if __name__ == "__main__":
    sys.exit(main())
