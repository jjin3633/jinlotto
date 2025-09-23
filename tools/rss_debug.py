#!/usr/bin/env python3
"""
RSS 피드 디버깅 도구
Google Search Console RSS 오류 진단
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from email.utils import formatdate

def check_rss_accessibility():
    """RSS 피드 접근성 상세 확인"""
    url = "http://stretchinglotto.motiphysio.com/rss.xml"
    
    print(f"🔍 RSS 피드 디버깅: {url}")
    print("=" * 60)
    
    try:
        # 1. HTTP 요청 상세 정보
        print("1️⃣ HTTP 요청 테스트...")
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        print(f"   ✅ 상태 코드: {response.status_code}")
        print(f"   ✅ 응답 시간: {response.elapsed.total_seconds():.2f}초")
        print(f"   ✅ 콘텐츠 타입: {response.headers.get('content-type', 'N/A')}")
        print(f"   ✅ 콘텐츠 길이: {len(response.content)} bytes")
        print(f"   ✅ 서버: {response.headers.get('server', 'N/A')}")
        
        # 2. XML 구문 검사
        print("\n2️⃣ RSS XML 구문 검사...")
        try:
            root = ET.fromstring(response.content)
            print("   ✅ XML 구문 정상")
            
            # RSS 구조 확인
            if root.tag == 'rss':
                print("   ✅ RSS 루트 태그 확인")
                version = root.get('version')
                print(f"   ✅ RSS 버전: {version}")
            else:
                print(f"   ❌ 잘못된 루트 태그: {root.tag}")
            
            # 채널 정보 확인
            channel = root.find('channel')
            if channel is not None:
                print("   ✅ 채널 태그 확인")
                
                title = channel.find('title')
                link = channel.find('link')
                description = channel.find('description')
                
                print(f"   - 제목: {title.text if title is not None else 'N/A'}")
                print(f"   - 링크: {link.text if link is not None else 'N/A'}")
                print(f"   - 설명: {description.text if description is not None else 'N/A'}")
                
                # 아이템 확인
                items = channel.findall('item')
                print(f"   ✅ 아이템 개수: {len(items)}개")
                
                for i, item in enumerate(items):
                    item_title = item.find('title')
                    item_pubdate = item.find('pubDate')
                    
                    print(f"      {i+1}. {item_title.text if item_title is not None else 'N/A'}")
                    if item_pubdate is not None:
                        pubdate = item_pubdate.text
                        print(f"         발행일: {pubdate}")
                        
                        # 1970년 날짜 체크
                        if '1970' in pubdate:
                            print(f"         ❌ 잘못된 발행일 (1970년)")
                        else:
                            print(f"         ✅ 발행일 정상")
            else:
                print("   ❌ 채널 태그 없음")
                
        except ET.ParseError as e:
            print(f"   ❌ XML 구문 오류: {e}")
            return False
            
        # 3. RSS 피드 검증
        print("\n3️⃣ RSS 피드 검증...")
        
        issues = []
        
        if response.status_code != 200:
            issues.append(f"HTTP 상태 코드 오류: {response.status_code}")
        
        if response.elapsed.total_seconds() > 10:
            issues.append(f"응답 시간 지연: {response.elapsed.total_seconds():.2f}초")
        
        content_type = response.headers.get('content-type', '')
        if 'xml' not in content_type.lower() and 'rss' not in content_type.lower():
            issues.append(f"잘못된 Content-Type: {content_type}")
        
        # RSS 내용에서 1970년 날짜 확인
        if '1970' in response.text:
            issues.append("잘못된 발행일 (1970년 Unix Epoch)")
        
        if len(response.content) < 200:
            issues.append("RSS 피드 크기가 너무 작음")
        
        # 4. 종합 진단
        print("\n" + "=" * 60)
        print("📊 RSS 피드 진단 결과")
        print("=" * 60)
        
        if issues:
            print("❌ 발견된 문제점:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 모든 검사 통과!")
        
        # 5. 해결 방안 제시
        if issues:
            print("\n💡 해결 방안:")
            if response.status_code != 200:
                print("   1. 서버 설정 확인 및 RSS 파일 존재 여부 확인")
            if response.elapsed.total_seconds() > 10:
                print("   2. 서버 성능 최적화")
            if 'xml' not in content_type.lower():
                print("   3. RSS 파일의 MIME 타입을 'application/rss+xml' 또는 'application/xml'로 설정")
            if '1970' in response.text:
                print("   4. RSS 아이템의 pubDate를 현재 날짜로 업데이트")
        
        return len(issues) == 0
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False

def generate_improved_rss():
    """개선된 RSS 피드 생성"""
    print("\n🔧 개선된 RSS 피드 생성...")
    
    # 현재 날짜를 RFC 2822 형식으로 생성
    current_date = formatdate(localtime=True)
    
    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>스트레칭 로또 - 건강한 습관과 함께하는 로또</title>
    <link>http://stretchinglotto.motiphysio.com/</link>
    <description>스트레칭 후 AI가 추천하는 로또 번호를 받아보세요. 건강한 습관과 행운을 함께!</description>
    <language>ko-KR</language>
    <lastBuildDate>{current_date}</lastBuildDate>
    <ttl>1440</ttl>
    <generator>JinLotto RSS Generator</generator>
    <atom:link href="http://stretchinglotto.motiphysio.com/rss.xml" rel="self" type="application/rss+xml"/>
    
    <item>
      <title>스트레칭 로또 서비스 오픈!</title>
      <link>http://stretchinglotto.motiphysio.com/</link>
      <guid isPermaLink="false">jinlotto-service-open-2025</guid>
      <description><![CDATA[
        스트레칭 후 AI가 분석한 로또 번호를 받아보세요! 
        • 하루 1세트 개인 맞춤 번호 추천
        • 매주 월요일 최신 회차 당첨 결과 자동 매칭
        • 건강한 습관 형성과 함께하는 로또 서비스
      ]]></description>
      <pubDate>{current_date}</pubDate>
      <category>로또</category>
      <category>건강</category>
    </item>
    
    <item>
      <title>AI 기반 로또 번호 분석 시스템</title>
      <link>http://stretchinglotto.motiphysio.com/</link>
      <guid isPermaLink="false">jinlotto-ai-analysis-2025</guid>
      <description><![CDATA[
        머신러닝을 활용한 로또 번호 분석 및 추천 시스템을 제공합니다.
        • 과거 당첨 번호 패턴 분석
        • 개인별 맞춤 번호 생성
        • 실시간 당첨 결과 확인
      ]]></description>
      <pubDate>{current_date}</pubDate>
      <category>AI</category>
      <category>분석</category>
    </item>
  </channel>
</rss>'''
    
    # 프론트엔드와 백엔드 모두에 저장
    paths = [
        'frontend/rss.xml',
        'backend/static/rss.xml'
    ]
    
    for path in paths:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(rss_content)
            print(f"   ✅ {path} 업데이트 완료")
        except Exception as e:
            print(f"   ❌ {path} 업데이트 실패: {e}")

def main():
    print("🚨 RSS 피드 오류 해결 도구")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 현재 RSS 상태 확인
    is_ok = check_rss_accessibility()
    
    if not is_ok:
        print("\n🔧 문제 해결을 위한 개선된 RSS 피드를 생성합니다...")
        generate_improved_rss()
        
        print("\n📋 추가 해결 방안:")
        print("1. 웹서버 설정에서 .xml 파일의 MIME 타입을 'application/rss+xml'로 설정")
        print("2. RSS 피드 검증 도구로 구문 확인: https://validator.w3.org/feed/")
        print("3. Google Search Console에서 RSS 피드 재제출")
    
    print("\n✅ RSS 진단 완료!")

if __name__ == "__main__":
    main()
