#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """서비스 상태 테스트"""
    print("=== 서비스 상태 확인 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("서비스 정상 작동")
            print(f"   상태: {response.json().get('status', 'unknown')}")
        else:
            print(f"서비스 오류 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"서비스 연결 실패: {e}")
    print()

def test_data_summary():
    """데이터 요약 테스트"""
    print("=== 데이터 요약 정보 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/data/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary_data = data.get('data', {})
                print("데이터 요약 조회 성공")
                print(f"   총 회차: {summary_data.get('total_draws', 0)}회")
                print(f"   데이터 범위: {summary_data.get('date_range', {})}")
                latest_draw = summary_data.get('latest_draw', {})
                if latest_draw:
                    print(f"   최신 회차: {latest_draw.get('draw_number', 'N/A')}회")
            else:
                print("데이터 요약 조회 실패")
        else:
            print(f"데이터 요약 조회 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"데이터 요약 조회 실패: {e}")
    print()

def test_comprehensive_analysis():
    """종합 분석 테스트"""
    print("=== 종합 분석 결과 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/comprehensive")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analysis_data = data.get('data', {})
                print("종합 분석 완료")
                print(f"   총 회차: {analysis_data.get('total_draws', 0)}회")
                
                # 핫/콜드 번호
                hot_numbers = analysis_data.get('hot_numbers', [])
                cold_numbers = analysis_data.get('cold_numbers', [])
                print(f"   핫 번호 (최근 50회): {hot_numbers[:5]}")
                print(f"   콜드 번호: {cold_numbers[:5]}")
                
                # 홀짝 비율
                odd_even = analysis_data.get('odd_even_ratio', {})
                print(f"   홀수 비율: {odd_even.get('odd_ratio', 0):.1%}")
                print(f"   짝수 비율: {odd_even.get('even_ratio', 0):.1%}")
                
                # 새로운 세밀한 분석 결과들
                print("\n세밀한 분석 결과:")
                
                # 계절별 분석
                seasonal = analysis_data.get('seasonal_analysis', {})
                if seasonal:
                    print("   계절별 분석:")
                    for season, data in seasonal.items():
                        draw_count = data.get('draw_count', 0)
                        hot_nums = data.get('hot_numbers', [])[:3]
                        print(f"      {season}: {draw_count}회, 핫번호: {hot_nums}")
                
                # 합계 분석
                sum_analysis = analysis_data.get('sum_analysis', {})
                if sum_analysis:
                    print(f"   번호 합계: 평균 {sum_analysis.get('avg_sum', 0):.1f}")
                
                # 소수 분석
                prime_analysis = analysis_data.get('prime_analysis', {})
                if prime_analysis:
                    avg_prime = prime_analysis.get('avg_prime_count', 0)
                    print(f"   소수 번호: 평균 {avg_prime:.1f}개")
            else:
                print("종합 분석 실패")
        else:
            print(f"종합 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"종합 분석 실패: {e}")
    print()

def test_seasonal_analysis():
    """계절별 분석 테스트"""
    print("=== 계절별 패턴 분석 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/seasonal")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                seasonal_data = data.get('data', {})
                print("계절별 분석 완료")
                
                for season, analysis in seasonal_data.items():
                    draw_count = analysis.get('draw_count', 0)
                    hot_numbers = analysis.get('hot_numbers', [])[:3]
                    cold_numbers = analysis.get('cold_numbers', [])[:3]
                    
                    print(f"   {season} ({draw_count}회):")
                    print(f"      핫번호: {hot_numbers}")
                    print(f"      콜드번호: {cold_numbers}")
            else:
                print("계절별 분석 실패")
        else:
            print(f"계절별 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"계절별 분석 실패: {e}")
    print()

def test_monthly_analysis():
    """월별 분석 테스트"""
    print("=== 월별 패턴 분석 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/monthly")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                monthly_data = data.get('data', {})
                print("월별 분석 완료")
                
                # 가장 많은 회차가 있는 월 3개만 표시
                month_counts = [(month, data.get('draw_count', 0)) for month, data in monthly_data.items()]
                top_months = sorted(month_counts, key=lambda x: x[1], reverse=True)[:3]
                
                for month, count in top_months:
                    analysis = monthly_data.get(month, {})
                    hot_numbers = analysis.get('hot_numbers', [])[:3]
                    print(f"   {month}월 ({count}회): 핫번호 {hot_numbers}")
            else:
                print("월별 분석 실패")
        else:
            print(f"월별 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"월별 분석 실패: {e}")
    print()

def test_sum_analysis():
    """합계 분석 테스트"""
    print("=== 번호 합계 패턴 분석 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/sum")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                sum_data = data.get('data', {})
                print("합계 분석 완료")
                print(f"   최소 합계: {sum_data.get('min_sum', 0)}")
                print(f"   최대 합계: {sum_data.get('max_sum', 0)}")
                print(f"   평균 합계: {sum_data.get('avg_sum', 0):.1f}")
                print(f"   표준편차: {sum_data.get('std_sum', 0):.1f}")
                
                # 가장 흔한 합계 5개
                common_sums = sum_data.get('most_common_sums', [])[:5]
                print(f"   가장 흔한 합계: {[f'{sum_val}({count}회)' for sum_val, count in common_sums]}")
            else:
                print("합계 분석 실패")
        else:
            print(f"합계 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"합계 분석 실패: {e}")
    print()

def test_prime_analysis():
    """소수 분석 테스트"""
    print("=== 소수 번호 패턴 분석 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/prime")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                prime_data = data.get('data', {})
                print("소수 분석 완료")
                print(f"   소수 번호들: {prime_data.get('prime_numbers', [])}")
                print(f"   평균 소수 개수: {prime_data.get('avg_prime_count', 0):.1f}개")
                
                # 소수 개수 분포
                distribution = prime_data.get('prime_count_distribution', {})
                print(f"   소수 개수 분포: {dict(distribution)}")
            else:
                print("소수 분석 실패")
        else:
            print(f"소수 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"소수 분석 실패: {e}")
    print()

def test_ending_analysis():
    """끝자리 분석 테스트"""
    print("=== 끝자리 패턴 분석 ===")
    try:
        response = requests.get(f"{BASE_URL}/api/analysis/ending")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ending_data = data.get('data', {})
                print("끝자리 분석 완료")
                
                # 가장 흔한 끝자리 5개
                common_endings = ending_data.get('most_common_endings', [])[:5]
                print(f"   가장 흔한 끝자리: {[f'{ending}({count}회)' for ending, count in common_endings]}")
            else:
                print("끝자리 분석 실패")
        else:
            print(f"끝자리 분석 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"끝자리 분석 실패: {e}")
    print()

def test_prediction():
    """예측 테스트"""
    print("=== 로또 번호 예측 결과 ===")
    print("예측 방법: 과거 데이터 분석을 통한 통계적 예측")
    print("주의: 이는 참고용이며, 실제 당첨을 보장하지 않습니다.")
    print()

    # 통계적 예측 (5세트)
    payload = {
        "method": "statistical",
        "num_sets": 5,
        "include_bonus": False
    }

    try:
        response = requests.post(f"{BASE_URL}/api/predict", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                prediction_data = data.get('data', {})
                sets = prediction_data.get('sets', [])
                confidence_scores = prediction_data.get('confidence_scores', [])

                print("추천 번호 세트 (5세트):")
                for i, numbers in enumerate(sets, 1):
                    confidence = confidence_scores[i-1] if i <= len(confidence_scores) else 0.3
                    print(f"   세트 {i}: {numbers} (신뢰도: {confidence:.1%})")

                print()
                print("예측 근거:")
                reasoning = prediction_data.get('reasoning', [])
                for reason in reasoning[:3]:
                    print(f"   - {reason}")
            else:
                print("예측 실패")
        else:
            print(f"예측 실패 (상태 코드: {response.status_code})")
    except Exception as e:
        print(f"예측 실패: {e}")
    print()

def main():
    """모든 테스트 실행"""
    print("로또 분석 서비스 테스트 시작")
    print("=" * 50)
    
    try:
        # 기본 테스트
        test_health()
        test_data_summary()
        test_comprehensive_analysis()
        
        # 새로운 세밀한 분석 테스트
        test_seasonal_analysis()
        test_monthly_analysis()
        test_sum_analysis()
        test_prime_analysis()
        test_ending_analysis()
        
        # 예측 테스트
        test_prediction()
        
        print("모든 테스트 완료!")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
