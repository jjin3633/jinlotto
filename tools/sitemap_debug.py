#!/usr/bin/env python3
"""
사이트맵 디버깅 도구
Google Search Console 사이트맵 오류 진단
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import json

def check_sitemap_accessibility():
    """사이트맵 접근성 상세 확인"""
    url = "http://stretchinglotto.motiphysio.com/sitemap.xml"
    
    print(f"🔍 사이트맵 디버깅: {url}")
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
        
        # 2. 리다이렉트 확인
        if response.history:
            print(f"   🔄 리다이렉트 발생: {len(response.history)}회")
            for i, resp in enumerate(response.history):
                print(f"      {i+1}. {resp.status_code} -> {resp.url}")
        else:
            print("   ✅ 리다이렉트 없음")
        
        # 3. XML 구문 검사
        print("\n2️⃣ XML 구문 검사...")
        try:
            root = ET.fromstring(response.content)
            print("   ✅ XML 구문 정상")
            
            # 네임스페이스 확인
            if root.tag.endswith('urlset'):
                print("   ✅ urlset 태그 확인")
            else:
                print(f"   ❌ 잘못된 루트 태그: {root.tag}")
            
            # URL 개수 확인
            urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            print(f"   ✅ URL 개수: {len(urls)}개")
            
            # 각 URL 검증
            for i, url_elem in enumerate(urls):
                loc = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None:
                    print(f"      {i+1}. {loc.text}")
                
        except ET.ParseError as e:
            print(f"   ❌ XML 구문 오류: {e}")
            return False
            
        # 4. Google 크롤러 시뮬레이션
        print("\n3️⃣ Google 크롤러 시뮬레이션...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        
        google_response = requests.get(url, headers=headers, timeout=30)
        print(f"   ✅ Googlebot 접근: {google_response.status_code}")
        
        if google_response.status_code != response.status_code:
            print(f"   ⚠️  일반 요청과 다른 응답: {response.status_code} vs {google_response.status_code}")
        
        # 5. robots.txt 확인
        print("\n4️⃣ robots.txt 확인...")
        robots_url = "http://stretchinglotto.motiphysio.com/robots.txt"
        robots_response = requests.get(robots_url, timeout=10)
        
        if robots_response.status_code == 200:
            print("   ✅ robots.txt 접근 가능")
            if 'sitemap.xml' in robots_response.text.lower():
                print("   ✅ robots.txt에 사이트맵 명시됨")
            else:
                print("   ⚠️  robots.txt에 사이트맵 미명시")
        else:
            print(f"   ❌ robots.txt 접근 불가: {robots_response.status_code}")
        
        # 6. 종합 진단
        print("\n" + "=" * 60)
        print("📊 종합 진단 결과")
        print("=" * 60)
        
        issues = []
        
        if response.status_code != 200:
            issues.append(f"HTTP 상태 코드 오류: {response.status_code}")
        
        if response.elapsed.total_seconds() > 10:
            issues.append(f"응답 시간 지연: {response.elapsed.total_seconds():.2f}초")
        
        content_type = response.headers.get('content-type', '')
        if 'xml' not in content_type.lower():
            issues.append(f"잘못된 Content-Type: {content_type}")
        
        if len(response.content) < 100:
            issues.append("사이트맵 크기가 너무 작음")
        
        if issues:
            print("❌ 발견된 문제점:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("✅ 모든 검사 통과!")
        
        # 7. 해결 방안 제시
        if issues:
            print("\n💡 해결 방안:")
            if response.status_code != 200:
                print("   1. 서버 설정 확인 및 사이트맵 파일 존재 여부 확인")
            if response.elapsed.total_seconds() > 10:
                print("   2. 서버 성능 최적화 또는 CDN 사용 고려")
            if 'xml' not in content_type.lower():
                print("   3. 웹서버에서 .xml 파일의 MIME 타입을 'application/xml' 또는 'text/xml'로 설정")
        
        return len(issues) == 0
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False

def generate_improved_sitemap():
    """개선된 사이트맵 생성"""
    print("\n🔧 개선된 사이트맵 생성...")
    
    sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
  <url>
    <loc>http://stretchinglotto.motiphysio.com/</loc>
    <lastmod>{}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>'''.format(datetime.now().strftime('%Y-%m-%d'))
    
    # 프론트엔드와 백엔드 모두에 저장
    paths = [
        'frontend/sitemap.xml',
        'backend/static/sitemap.xml'
    ]
    
    for path in paths:
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sitemap_content)
            print(f"   ✅ {path} 업데이트 완료")
        except Exception as e:
            print(f"   ❌ {path} 업데이트 실패: {e}")

def main():
    print("🚨 Google Search Console 사이트맵 오류 해결 도구")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 현재 사이트맵 상태 확인
    is_ok = check_sitemap_accessibility()
    
    if not is_ok:
        print("\n🔧 문제 해결을 위한 개선된 사이트맵을 생성하시겠습니까? (y/n)")
        # 자동으로 생성
        generate_improved_sitemap()
        
        print("\n📋 추가 해결 방안:")
        print("1. 웹서버 설정에서 .xml 파일의 MIME 타입 확인")
        print("2. Google Search Console에서 기존 사이트맵 삭제 후 재제출")
        print("3. 24-48시간 후 다시 확인")
    
    print("\n✅ 진단 완료!")

if __name__ == "__main__":
    main()
