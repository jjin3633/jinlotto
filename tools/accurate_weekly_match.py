#!/usr/bin/env python3
"""
정확한 기간별 필터링이 적용된 로또 매칭 스크립트

기능:
- 특정 회차의 추첨일 기준으로 정확한 기간 필터링
- 토요일 20:00 KST (UTC 11:00) 이전에 생성된 예측만 매칭
- generated_for 필드로 해당 회차용 예측만 선별
- Slack으로 정확한 결과 요약 전송

환경변수:
- SUPABASE_URL: Supabase 프로젝트 URL
- SUPABASE_ANON_KEY: Supabase 익명 키
- SLACK_WEBHOOK_URL: Slack 웹훅 URL
- MONITOR_BASE_URL: 서버 베이스 URL (기본: https://jinlotto.onrender.com)

사용법:
$ export SUPABASE_URL=... SUPABASE_ANON_KEY=... SLACK_WEBHOOK_URL=... && python tools/accurate_weekly_match.py [회차번호]
$ python tools/accurate_weekly_match.py 1186
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


def get_draw_info(draw_number: int) -> Optional[Dict]:
    """동행복권 API에서 특정 회차 정보 조회"""
    try:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_number}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('returnValue') == 'success':
            return {
                'draw_number': data['drwNo'],
                'draw_date': data['drwNoDate'],
                'numbers': [
                    data['drwtNo1'], data['drwtNo2'], data['drwtNo3'],
                    data['drwtNo4'], data['drwtNo5'], data['drwtNo6']
                ],
                'bonus_number': data['bnusNo'],
                'total_sales': data.get('totSellamnt', 0),
                'first_prize_amount': data.get('firstWinamnt', 0),
                'first_prize_winners': data.get('firstPrzwnerCo', 0)
            }
        else:
            print(f"❌ {draw_number}회차: 유효하지 않은 응답", file=sys.stderr)
            return None
    except Exception as e:
        print(f"❌ {draw_number}회차 조회 실패: {e}", file=sys.stderr)
        return None


def get_filtered_predictions(client, draw_number: int, draw_date: str) -> List[Dict]:
    """정확한 기간별 필터링이 적용된 예측 데이터 조회"""
    try:
        # 추첨일 파싱 (YYYY-MM-DD 형태)
        draw_datetime = datetime.strptime(draw_date, '%Y-%m-%d')
        
        # 토요일 20:00 KST = UTC 11:00 계산
        # KST는 UTC+9이므로, 20:00 KST = 11:00 UTC
        cutoff_utc = draw_datetime.replace(hour=11, minute=0, second=0, microsecond=0)
        cutoff_iso = cutoff_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        
        print(f"📅 필터링 기준:")
        print(f"   - 회차: {draw_number}회차용 예측")
        print(f"   - 생성시간: {cutoff_iso} 이전")
        print(f"   - 추첨일: {draw_date}")
        
        # Supabase 쿼리: 해당 회차용 + 추첨 전 생성된 예측만
        response = client.from_("predictions").select("*").filter(
            "generated_for", "lte", draw_date
        ).filter(
            "created_at", "lte", cutoff_iso
        ).execute()
        
        preds = getattr(response, "data", []) or []
        
        # 추가 필터링: 정확히 해당 회차용 예측만 (generated_for가 해당 회차 주간에 해당)
        filtered_preds = []
        for p in preds:
            generated_for = p.get('generated_for')
            if generated_for:
                # generated_for가 해당 회차 추첨일과 일치하거나 그 주간에 해당하는지 확인
                try:
                    gen_date = datetime.strptime(generated_for, '%Y-%m-%d')
                    # 해당 회차 추첨일 기준으로 ±7일 이내 (해당 주간)
                    if abs((gen_date - draw_datetime).days) <= 7:
                        filtered_preds.append(p)
                except:
                    continue
        
        print(f"📊 필터링 결과:")
        print(f"   - 전체 예측: {len(preds)}개")
        print(f"   - 해당 회차용: {len(filtered_preds)}개")
        
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


def send_slack_notification(draw_info: Dict, counts: Dict[int, int], total_predictions: int) -> bool:
    """Slack으로 결과 전송"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL 미설정: Slack 알림을 건너뜁니다.", file=sys.stderr)
        return False
    
    try:
        draw_number = draw_info['draw_number']
        numbers_str = ', '.join(map(str, draw_info['numbers']))
        
        message = f"""📣 회차 {draw_number} 정확한 결과 요약 (기간별 필터링)
🎯 당첨번호: {numbers_str} + 보너스 {draw_info['bonus_number']}
📅 추첨일: {draw_info['draw_date']}

🏆 매칭 결과 (총 {total_predictions}개 예측):
1등 (6개 일치): {counts[1]}명
2등 (5개+보너스): {counts[2]}명  
3등 (5개 일치): {counts[3]}명
4등 (4개 일치): {counts[4]}명
5등 (3개 일치): {counts[5]}명

✅ 정확한 기간별 필터링 적용됨
⏰ 추첨 전(토요일 20:00 KST) 생성된 예측만 집계"""
        
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        print("📱 Slack 전송 성공")
        return True
        
    except Exception as e:
        print(f"❌ Slack 전송 실패: {e}", file=sys.stderr)
        return False


def main():
    """메인 함수"""
    # 회차 번호 파라미터 처리
    draw_number = None
    if len(sys.argv) > 1:
        try:
            draw_number = int(sys.argv[1])
        except ValueError:
            print("❌ 잘못된 회차 번호입니다.", file=sys.stderr)
            return 1
    
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
    
    # 회차 정보가 없으면 최신 회차 조회
    if not draw_number:
        print("🔍 최신 회차 조회 중...")
        monitor_base = os.getenv("MONITOR_BASE_URL", "https://jinlotto.onrender.com")
        try:
            response = requests.get(f"{monitor_base.rstrip('/')}/api/data/latest", timeout=30)
            if response.status_code == 200:
                latest_data = response.json().get("data", {})
                draw_number = latest_data.get("draw_number")
                if draw_number:
                    print(f"📊 최신 회차: {draw_number}회차")
                else:
                    print("❌ 최신 회차 정보를 찾을 수 없습니다.", file=sys.stderr)
                    return 4
            else:
                print(f"❌ 최신 회차 조회 실패: {response.status_code}", file=sys.stderr)
                return 4
        except Exception as e:
            print(f"❌ 최신 회차 조회 중 오류: {e}", file=sys.stderr)
            return 4
    
    # 회차 정보 조회
    print(f"🎯 {draw_number}회차 정보 조회 중...")
    draw_info = get_draw_info(draw_number)
    if not draw_info:
        return 5
    
    print(f"✅ {draw_number}회차 당첨번호: {draw_info['numbers']} + 보너스 {draw_info['bonus_number']}")
    print(f"📅 추첨일: {draw_info['draw_date']}")
    
    # 정확한 기간별 필터링으로 예측 데이터 조회
    print(f"\n🔍 {draw_number}회차용 예측 데이터 조회 중...")
    predictions = get_filtered_predictions(client, draw_number, draw_info['draw_date'])
    
    if not predictions:
        print("⚠️ 해당 기간의 예측 데이터가 없습니다.")
        counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    else:
        # 매칭 결과 계산
        print(f"\n🎲 매칭 결과 계산 중...")
        counts = calculate_matches(predictions, draw_info['numbers'], draw_info['bonus_number'])
    
    # 결과 출력
    print(f"\n📊 {draw_number}회차 정확한 매칭 결과:")
    print(f"   총 예측 수: {len(predictions)}개")
    print(f"   1등 (6개 일치): {counts[1]}명")
    print(f"   2등 (5개+보너스): {counts[2]}명")
    print(f"   3등 (5개 일치): {counts[3]}명")
    print(f"   4등 (4개 일치): {counts[4]}명")
    print(f"   5등 (3개 일치): {counts[5]}명")
    
    # Slack 전송
    send_slack_notification(draw_info, counts, len(predictions))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
