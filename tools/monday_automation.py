#!/usr/bin/env python3
"""
매주 월요일 오전 9시 통합 자동화 스크립트

기능:
1. 최신 로또 번호 업데이트
2. 당첨자 집계
3. 슬랙 알림 전송

실행: 매주 월요일 09:00 KST = 00:00 UTC
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

def get_kst_now():
    """한국 시간 현재 시각"""
    return datetime.now(timezone(timedelta(hours=9)))

def log_message(message: str):
    """로그 메시지 출력"""
    kst_time = get_kst_now().strftime('%Y-%m-%d %H:%M:%S KST')
    print(f"[{kst_time}] {message}")

def send_slack_notification(message: str, is_error: bool = False):
    """슬랙 알림 전송"""
    try:
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            log_message("❌ SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
            return False
        
        emoji = "❌" if is_error else "🎲"
        payload = {
            "text": f"{emoji} {message}"
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        log_message(f"✅ 슬랙 알림 전송 완료")
        return True
        
    except Exception as e:
        log_message(f"❌ 슬랙 알림 전송 실패: {e}")
        return False

def update_lotto_data():
    """로또 데이터 업데이트"""
    try:
        log_message("🔄 로또 데이터 업데이트 시작")
        
        base_url = os.getenv("MONITOR_BASE_URL")
        if not base_url:
            raise Exception("MONITOR_BASE_URL 환경변수가 설정되지 않았습니다.")
        
        update_url = base_url.rstrip('/') + '/api/data/update'
        
        # 스케줄러 토큰이 있으면 헤더에 추가
        headers = {"Content-Type": "application/json"}
        scheduler_token = os.getenv("SCHEDULER_TOKEN")
        if scheduler_token:
            headers["X-Scheduler-Token"] = scheduler_token
        
        response = requests.post(update_url, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        log_message(f"✅ 로또 데이터 업데이트 완료: {result.get('message', 'Success')}")
        
        return True, result
        
    except Exception as e:
        error_msg = f"로또 데이터 업데이트 실패: {e}"
        log_message(f"❌ {error_msg}")
        return False, {"error": str(e)}

def get_latest_draw_info():
    """최신 회차 정보 조회"""
    try:
        base_url = os.getenv("MONITOR_BASE_URL")
        if not base_url:
            raise Exception("MONITOR_BASE_URL이 설정되지 않았습니다.")
        
        latest_url = base_url.rstrip('/') + '/api/data/latest'
        response = requests.get(latest_url, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        if result.get('success') and result.get('data'):
            return result['data']
        else:
            raise Exception("최신 회차 정보를 가져올 수 없습니다.")
            
    except Exception as e:
        log_message(f"❌ 최신 회차 정보 조회 실패: {e}")
        return None

def calculate_matches():
    """당첨자 집계 실행"""
    try:
        log_message("🏆 당첨자 집계 시작")
        
        # Supabase 매칭 API 호출
        base_url = os.getenv("MONITOR_BASE_URL")
        if not base_url:
            raise Exception("MONITOR_BASE_URL이 설정되지 않았습니다.")
        
        match_url = base_url.rstrip('/') + '/api/data/match-supabase'
        
        headers = {"Content-Type": "application/json"}
        scheduler_token = os.getenv("SCHEDULER_TOKEN")
        if scheduler_token:
            headers["X-Scheduler-Token"] = scheduler_token
        
        response = requests.post(match_url, headers=headers, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        log_message(f"✅ 당첨자 집계 완료: {result.get('message', 'Success')}")
        
        return True, result
        
    except Exception as e:
        error_msg = f"당첨자 집계 실패: {e}"
        log_message(f"❌ {error_msg}")
        return False, {"error": str(e)}

def format_summary_message(latest_draw: Dict, update_result: Dict, match_result: Dict) -> str:
    """요약 메시지 포맷팅"""
    try:
        kst_time = get_kst_now().strftime('%Y-%m-%d %H:%M KST')
        
        # 기본 정보
        draw_number = latest_draw.get('draw_number', '?')
        draw_date = latest_draw.get('draw_date', '?')
        
        # 당첨번호 포맷팅
        numbers = []
        for i in range(1, 7):
            num = latest_draw.get(f'number_{i}')
            if num:
                numbers.append(str(num))
        
        bonus = latest_draw.get('bonus_number', '?')
        numbers_str = ', '.join(numbers) if numbers else '정보 없음'
        
        message = f"""🔥 로또 업뎃 떴다!! ({kst_time})

✨ {draw_number}회차 ({draw_date}) 결과 공개~
🎯 이번주 당첨번호: [{numbers_str}] + 보너스 {bonus}

🎊 당첨자 현황:
   🥇 1등: ?명 | 🥈 2등: ?명 | 🥉 3등: ?명 | 4등: ?명 | 5등: ?명"""

        return message
        
    except Exception as e:
        log_message(f"❌ 메시지 포맷팅 오류: {e}")
        return f"🔥 로또 업뎃 떴다!! ({get_kst_now().strftime('%Y-%m-%d %H:%M KST')})\n⚠️ 상세 정보 처리 중 오류 발생"

def main():
    """메인 실행 함수"""
    log_message("🚀 매주 월요일 로또 자동화 시작")
    
    try:
        # 1단계: 로또 데이터 업데이트
        update_success, update_result = update_lotto_data()
        if not update_success:
            error_msg = f"로또 업데이트 실패 ({get_kst_now().strftime('%Y-%m-%d %H:%M KST')})\n🔍 오류: {update_result.get('error', '알 수 없는 오류')}\n🛠️ 수동 확인 필요"
            send_slack_notification(error_msg, is_error=True)
            return 1
        
        # 2단계: 최신 회차 정보 조회
        latest_draw = get_latest_draw_info()
        if not latest_draw:
            error_msg = f"최신 회차 정보 조회 실패 ({get_kst_now().strftime('%Y-%m-%d %H:%M KST')})\n🛠️ 수동 확인 필요"
            send_slack_notification(error_msg, is_error=True)
            return 1
        
        # 3단계: 당첨자 집계
        match_success, match_result = calculate_matches()
        if not match_success:
            # 업데이트는 성공했지만 집계 실패
            error_msg = f"당첨자 집계 실패 ({get_kst_now().strftime('%Y-%m-%d %H:%M KST')})\n✅ 데이터 업데이트: 완료\n❌ 당첨자 집계: 실패\n🔍 오류: {match_result.get('error', '알 수 없는 오류')}"
            send_slack_notification(error_msg, is_error=True)
            return 1
        
        # 4단계: 성공 알림 전송
        summary_message = format_summary_message(latest_draw, update_result, match_result)
        send_slack_notification(summary_message, is_error=False)
        
        log_message("🎉 매주 월요일 로또 자동화 완료!")
        return 0
        
    except Exception as e:
        error_msg = f"자동화 실행 중 예상치 못한 오류 ({get_kst_now().strftime('%Y-%m-%d %H:%M KST')})\n🔍 오류: {str(e)}\n🛠️ 긴급 확인 필요"
        log_message(f"❌ {error_msg}")
        send_slack_notification(error_msg, is_error=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
