#!/usr/bin/env python3
"""
SEO 모니터링 도구
- 사이트맵, robots.txt 상태 확인
- 메타태그 검증
- 페이지 로딩 속도 체크
- 기본 SEO 요소 점검
"""

import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json

class SEOMonitor:
    def __init__(self, base_url="https://stretchinglotto.motiphysio.com/"):
        self.base_url = base_url.rstrip('/')
        self.results = {}
    
    def check_sitemap(self):
        """사이트맵 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/sitemap.xml", timeout=10)
            self.results['sitemap'] = {
                'status': response.status_code,
                'accessible': response.status_code == 200,
                'size': len(response.content) if response.status_code == 200 else 0
            }
        except Exception as e:
            self.results['sitemap'] = {'status': 'error', 'error': str(e)}
    
    def check_robots_txt(self):
        """robots.txt 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/robots.txt", timeout=10)
            self.results['robots'] = {
                'status': response.status_code,
                'accessible': response.status_code == 200,
                'content': response.text[:200] if response.status_code == 200 else None
            }
        except Exception as e:
            self.results['robots'] = {'status': 'error', 'error': str(e)}
    
    def check_main_page_seo(self):
        """메인 페이지 SEO 요소 확인"""
        try:
            start_time = time.time()
            response = requests.get(self.base_url, timeout=15)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 메타태그 확인
                title = soup.find('title')
                description = soup.find('meta', attrs={'name': 'description'})
                keywords = soup.find('meta', attrs={'name': 'keywords'})
                og_title = soup.find('meta', attrs={'property': 'og:title'})
                og_description = soup.find('meta', attrs={'property': 'og:description'})
                
                # JSON-LD 구조화 데이터 확인
                json_ld = soup.find('script', attrs={'type': 'application/ld+json'})
                
                self.results['main_page'] = {
                    'status': response.status_code,
                    'load_time': round(load_time, 2),
                    'title': title.text if title else None,
                    'title_length': len(title.text) if title else 0,
                    'description': description.get('content') if description else None,
                    'description_length': len(description.get('content')) if description else 0,
                    'keywords': keywords.get('content') if keywords else None,
                    'og_title': og_title.get('content') if og_title else None,
                    'og_description': og_description.get('content') if og_description else None,
                    'has_json_ld': json_ld is not None,
                    'json_ld_content': json_ld.text if json_ld else None
                }
            else:
                self.results['main_page'] = {'status': response.status_code, 'error': 'Page not accessible'}
                
        except Exception as e:
            self.results['main_page'] = {'status': 'error', 'error': str(e)}
    
    def check_rss_feed(self):
        """RSS 피드 상태 확인"""
        try:
            response = requests.get(f"{self.base_url}/rss.xml", timeout=10)
            self.results['rss'] = {
                'status': response.status_code,
                'accessible': response.status_code == 200,
                'size': len(response.content) if response.status_code == 200 else 0
            }
        except Exception as e:
            self.results['rss'] = {'status': 'error', 'error': str(e)}
    
    def run_full_check(self):
        """전체 SEO 점검 실행"""
        print(f"🔍 SEO 모니터링 시작: {self.base_url}")
        print(f"⏰ 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        # 각 항목 점검
        print("📄 사이트맵 확인 중...")
        self.check_sitemap()
        
        print("🤖 robots.txt 확인 중...")
        self.check_robots_txt()
        
        print("📰 RSS 피드 확인 중...")
        self.check_rss_feed()
        
        print("🏠 메인 페이지 SEO 확인 중...")
        self.check_main_page_seo()
        
        return self.results
    
    def print_report(self):
        """결과 리포트 출력"""
        print("\n" + "="*60)
        print("📊 SEO 모니터링 결과 리포트")
        print("="*60)
        
        # 사이트맵 결과
        sitemap = self.results.get('sitemap', {})
        print(f"📄 사이트맵: {'✅ 정상' if sitemap.get('accessible') else '❌ 오류'}")
        if sitemap.get('accessible'):
            print(f"   - 크기: {sitemap.get('size', 0)} bytes")
        
        # robots.txt 결과
        robots = self.results.get('robots', {})
        print(f"🤖 robots.txt: {'✅ 정상' if robots.get('accessible') else '❌ 오류'}")
        
        # RSS 피드 결과
        rss = self.results.get('rss', {})
        print(f"📰 RSS 피드: {'✅ 정상' if rss.get('accessible') else '❌ 오류'}")
        
        # 메인 페이지 결과
        main = self.results.get('main_page', {})
        if main.get('status') == 200:
            print(f"🏠 메인 페이지: ✅ 정상 (로딩시간: {main.get('load_time', 0)}초)")
            print(f"   - 제목: {main.get('title', 'N/A')[:50]}...")
            print(f"   - 제목 길이: {main.get('title_length', 0)}자")
            print(f"   - 설명 길이: {main.get('description_length', 0)}자")
            print(f"   - Open Graph: {'✅' if main.get('og_title') else '❌'}")
            print(f"   - JSON-LD: {'✅' if main.get('has_json_ld') else '❌'}")
        else:
            print(f"🏠 메인 페이지: ❌ 오류 (상태: {main.get('status', 'N/A')})")
        
        # SEO 점수 계산
        score = 0
        total = 4
        
        if sitemap.get('accessible'): score += 1
        if robots.get('accessible'): score += 1
        if rss.get('accessible'): score += 1
        if main.get('status') == 200: score += 1
        
        print(f"\n🏆 전체 SEO 점수: {score}/{total} ({score/total*100:.0f}%)")
        
        # 개선 제안
        print("\n💡 개선 제안:")
        if not sitemap.get('accessible'):
            print("   - 사이트맵 파일 확인 필요")
        if not robots.get('accessible'):
            print("   - robots.txt 파일 확인 필요")
        if main.get('load_time', 0) > 3:
            print("   - 페이지 로딩 속도 개선 필요 (3초 이상)")
        if main.get('title_length', 0) > 60:
            print("   - 제목 길이 단축 권장 (60자 이하)")
        if main.get('description_length', 0) > 160:
            print("   - 설명 길이 단축 권장 (160자 이하)")

def main():
    monitor = SEOMonitor()
    monitor.run_full_check()
    monitor.print_report()
    
    # 결과를 JSON 파일로 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"seo_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': monitor.results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 결과가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    main()
