#!/usr/bin/env python3
"""
Google Search Console 테스트 도구
실제 Googlebot User-Agent로 접근 테스트
"""

import requests
from datetime import datetime

def test_googlebot_access():
    """Googlebot User-Agent로 접근 테스트"""
    
    # Google의 실제 User-Agent들
    user_agents = [
        'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Googlebot/2.1 (+http://www.google.com/bot.html)'
    ]
    
    urls = [
        'https://jinlotto.onrender.com/sitemap.xml',
        'https://jinlotto.onrender.com/rss.xml'
    ]
    
    print(f"🤖 Googlebot 접근 테스트")
    print(f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for url in urls:
        print(f"\n📄 테스트 URL: {url}")
        
        for i, ua in enumerate(user_agents):
            print(f"\n{i+1}️⃣ User-Agent: {ua[:50]}...")
            
            try:
                response = requests.get(
                    url, 
                    headers={'User-Agent': ua},
                    timeout=30
                )
                
                print(f"   ✅ 상태: {response.status_code}")
                print(f"   ✅ 응답시간: {response.elapsed.total_seconds():.2f}초")
                print(f"   ✅ 크기: {len(response.content)} bytes")
                print(f"   ✅ Content-Type: {response.headers.get('content-type', 'N/A')}")
                
                # 특별한 헤더 확인
                special_headers = ['X-Robots-Tag', 'Cache-Control', 'Server']
                for header in special_headers:
                    value = response.headers.get(header)
                    if value:
                        print(f"   📌 {header}: {value}")
                
            except Exception as e:
                print(f"   ❌ 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 결론:")
    print("모든 User-Agent에서 정상 응답이 나오면 Google 캐시 지연 문제입니다.")
    print("24-48시간 후 다시 확인하거나 GSC에서 강제 재처리 요청하세요.")

def test_gsc_specific_issues():
    """GSC 특화 문제 확인"""
    print(f"\n🔍 GSC 특화 이슈 확인")
    print("-" * 40)
    
    # 1. 사이트맵 크기 확인
    sitemap_response = requests.get('https://jinlotto.onrender.com/sitemap.xml')
    rss_response = requests.get('https://jinlotto.onrender.com/rss.xml')
    
    print(f"📄 사이트맵 크기: {len(sitemap_response.content)} bytes")
    print(f"📡 RSS 크기: {len(rss_response.content)} bytes")
    
    # 2. robots.txt에서 사이트맵 확인
    robots_response = requests.get('https://jinlotto.onrender.com/robots.txt')
    if 'sitemap.xml' in robots_response.text.lower():
        print("✅ robots.txt에 사이트맵 명시됨")
    else:
        print("❌ robots.txt에 사이트맵 미명시")
    
    # 3. 응답 헤더 분석
    print(f"\n📊 응답 헤더 분석:")
    print(f"사이트맵 Content-Type: {sitemap_response.headers.get('content-type')}")
    print(f"RSS Content-Type: {rss_response.headers.get('content-type')}")
    print(f"Cache-Control: {sitemap_response.headers.get('cache-control', 'None')}")

if __name__ == "__main__":
    test_googlebot_access()
    test_gsc_specific_issues()
    
    print(f"\n💡 다음 단계:")
    print("1. Google Search Console → URL 검사 → 색인 생성 요청")
    print("2. 24-48시간 후 재확인")
    print("3. 문제 지속 시 Google Search Console 커뮤니티에 문의")
