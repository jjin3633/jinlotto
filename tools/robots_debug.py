#!/usr/bin/env python3
"""
robots.txt 디버깅 도구
Google 차단 문제 진단
"""

import requests
from datetime import datetime

def check_robots_txt():
    """robots.txt 상세 확인"""
    url = "http://stretchinglotto.motiphysio.com/robots.txt"
    
    print(f"🤖 robots.txt 디버깅: {url}")
    print("=" * 60)
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"✅ 상태 코드: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"✅ 크기: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"\n📄 robots.txt 내용:")
            print("-" * 40)
            print(response.text)
            print("-" * 40)
            
            # 문제 진단
            content = response.text.lower()
            
            print(f"\n🔍 문제 진단:")
            
            # 1. Disallow 규칙 확인
            if 'disallow: /' in content and 'allow:' not in content:
                print("❌ 모든 크롤링 차단됨: 'Disallow: /' 발견")
                return False
            elif 'disallow: /sitemap.xml' in content:
                print("❌ 사이트맵 직접 차단됨")
                return False
            elif 'disallow: /rss.xml' in content:
                print("❌ RSS 직접 차단됨")
                return False
            else:
                print("✅ 차단 규칙 없음")
            
            # 2. Allow 규칙 확인
            if 'allow: /' in content:
                print("✅ 전체 허용 규칙 있음")
            else:
                print("⚠️ 명시적 허용 규칙 없음")
            
            # 3. 사이트맵 선언 확인
            if 'sitemap:' in content:
                print("✅ 사이트맵 선언됨")
            else:
                print("⚠️ 사이트맵 미선언")
            
            return True
        else:
            print(f"❌ robots.txt 접근 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def test_specific_urls():
    """특정 URL들의 robots.txt 준수 여부 확인"""
    print(f"\n🎯 특정 URL 테스트")
    print("-" * 40)
    
    test_urls = [
        'http://stretchinglotto.motiphysio.com/',
        'http://stretchinglotto.motiphysio.com/sitemap.xml',
        'http://stretchinglotto.motiphysio.com/rss.xml'
    ]
    
    for url in test_urls:
        print(f"\n📄 테스트: {url}")
        
        # robots.txt 체크 시뮬레이션
        try:
            response = requests.get(url, timeout=10)
            print(f"   ✅ 접근 가능: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 접근 실패: {e}")

def generate_correct_robots():
    """올바른 robots.txt 생성"""
    print(f"\n🔧 올바른 robots.txt 생성")
    print("-" * 40)
    
    correct_robots = """User-agent: *
Allow: /

# SEO 파일들 명시적 허용
Allow: /sitemap.xml
Allow: /rss.xml
Allow: /robots.txt

# 사이트맵 위치 선언
Sitemap: http://stretchinglotto.motiphysio.com/sitemap.xml
"""
    
    print("권장 robots.txt 내용:")
    print(correct_robots)
    
    # 파일 저장
    paths = [
        'frontend/robots.txt',
        'backend/static/robots.txt'
    ]
    
    for path in paths:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(correct_robots)
            print(f"✅ {path} 업데이트 완료")
        except Exception as e:
            print(f"❌ {path} 업데이트 실패: {e}")

def main():
    print("🚨 robots.txt 차단 문제 해결 도구")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # robots.txt 확인
    is_ok = check_robots_txt()
    
    # 특정 URL 테스트
    test_specific_urls()
    
    if not is_ok:
        print("\n🔧 문제 해결을 위한 올바른 robots.txt를 생성합니다...")
        generate_correct_robots()
        
        print(f"\n📋 다음 단계:")
        print("1. 변경사항 배포")
        print("2. 10-15분 후 Google Search Console에서 재테스트")
        print("3. URL 검사 도구로 다시 확인")
    
    print(f"\n✅ robots.txt 진단 완료!")

if __name__ == "__main__":
    main()
