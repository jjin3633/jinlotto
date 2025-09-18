#!/usr/bin/env python3
"""
🏃‍♀️ MZ 감성 스트레칭 알림봇 🏃‍♂️

매시간 50분에 슬랙으로 스트레칭 알림을 보내는 스크립트
- 10:50, 11:50, 12:50, 14:50, 15:50, 16:50 KST
- MZ 세대 감성의 재미있는 메시지
- JinLotto 서비스 링크 포함

환경변수:
- STRETCHING_SLACK_WEBHOOK_URL: 스트레칭 알림용 슬랙 웹훅 URL

사용법:
$ export STRETCHING_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... && python tools/stretching_reminder.py
"""

import os
import sys
import json
import requests
import random
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# 슬랙 웹훅 URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
JINLOTTO_URL = "http://43.201.75.105:8000/"

def get_mz_stretching_messages() -> List[Dict]:
    """MZ 감성 스트레칭 메시지 리스트"""
    messages = [
        {
            "text": "🚨 스트레칭 타임이 왔어요! 🚨\n\n💪 몸이 굳어가고 있지 않나요? 지금 바로 스트레칭하고\n🍀 행운의 로또 번호도 받아가세요! ✨\n\n진짜 1분이면 끝나요 ㅋㅋ 믿고 따라와 주세요~ 💖",
            "emoji": "🏃‍♀️"
        },
        {
            "text": "⏰ 띵동! 스트레칭 알림이 도착했어요! ⏰\n\n🧘‍♂️ 잠깐만 일어나서 몸 좀 풀어봐요!\n🎯 스트레칭 완료하면 오늘의 럭키 넘버까지 겟! \n\n일석이조 아닌가요? 헤헤 😎✨",
            "emoji": "🤸‍♀️"
        },
        {
            "text": "🔥 스트레칭 챌린지 시작! 🔥\n\n💻 모니터만 보고 있으면 거북목 온다구요~\n🌟 1분 투자해서 건강도 챙기고 로또 번호도 챙기고!\n\n이런 꿀템이 어디 있어요? 바로 고고! 🚀",
            "emoji": "💪"
        },
        {
            "text": "📢 잠깐! 스트레칭 타임입니다! 📢\n\n🪑 의자에서 일어나세요~ 몸이 뻐근하지 않나요?\n✨ 간단한 스트레칭으로 몸도 마음도 리프레시!\n🎲 그리고 오늘의 행운 번호까지 받아가세요! 💎",
            "emoji": "🧘‍♀️"
        },
        {
            "text": "🎵 스트레칭 송이 울려퍼진다~ 🎵\n\n🕺 어깨 돌리고~ 목 돌리고~ 허리도 쭉!\n🌈 몸이 가벼워지는 느낌 아시죠?\n🍀 스트레칭 끝나면 로또 번호로 마무리까지! 완벽 👌",
            "emoji": "🎶"
        },
        {
            "text": "⚡ 번개처럼 빠른 스트레칭 타임! ⚡\n\n🏃‍♂️ 딱 1분만 투자하세요! 진짜 1분!\n💝 건강한 몸 + 행운의 번호 = 오늘 하루 완승!\n\n이미 일어나고 계시죠? ㅋㅋㅋ 🤩",
            "emoji": "⚡"
        }
    ]
    return messages

def send_stretching_reminder():
    """스트레칭 알림 메시지를 슬랙으로 전송"""
    try:
        # 랜덤 메시지 선택
        messages = get_mz_stretching_messages()
        selected_message = random.choice(messages)
        
        # 현재 시간 (KST)
        kst = timezone(timedelta(hours=9))
        now = datetime.now(kst)
        time_str = now.strftime("%H:%M")
        
        # 슬랙 메시지 구성
        slack_payload = {
            "text": f"{selected_message['emoji']} *스트레칭 타임* {selected_message['emoji']}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🕐 {time_str} 스트레칭 타임이 왔어요! 🕐"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": selected_message['text']
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🎯 *지금 바로 스트레칭하러 가기* 👇\n<{JINLOTTO_URL}|✨ 로또 스트레칭에서 스트레칭 & 번호받기 ✨>"
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "스트레칭 GO!",
                            "emoji": False
                        },
                        "url": JINLOTTO_URL,
                        "action_id": "stretching_button"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"💡 *Tip:* 매시간 50분마다 알림이 와요! 건강한 하루 되세요~ 💖"
                        }
                    ]
                }
            ]
        }
        
        # 슬랙으로 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            SLACK_WEBHOOK_URL, 
            data=json.dumps(slack_payload), 
            headers=headers, 
            timeout=10
        )
        response.raise_for_status()
        
        print(f"✅ 스트레칭 알림 전송 성공! ({time_str} KST)")
        print(f"📱 메시지: {selected_message['text'][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ 스트레칭 알림 전송 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🏃‍♀️ MZ 감성 스트레칭 알림봇 시작!")
    
    # 현재 시간 확인
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    print(f"🕐 현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')} KST")
    
    # 스트레칭 알림 전송
    success = send_stretching_reminder()
    
    if success:
        print("🎉 스트레칭 알림 전송 완료!")
    else:
        print("😢 스트레칭 알림 전송 실패...")
        sys.exit(1)

if __name__ == "__main__":
    main()
