import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_sample_data():
    """샘플 로또 데이터 생성"""
    data = []
    start_date = datetime(2002, 12, 7)
    
    for i in range(1, 1001):
        draw_date = start_date + timedelta(days=i*7)
        numbers = sorted(random.sample(range(1, 46), 6))
        bonus = random.randint(1, 45)
        
        data.append({
            'draw_number': i,
            'draw_date': draw_date.strftime('%Y-%m-%d'),
            'number_1': numbers[0],
            'number_2': numbers[1],
            'number_3': numbers[2],
            'number_4': numbers[3],
            'number_5': numbers[4],
            'number_6': numbers[5],
            'bonus_number': bonus
        })
    
    return pd.DataFrame(data)

def statistical_prediction(df, num_sets=5):
    """통계 기반 번호 예측"""
    # 번호별 출현 빈도 계산
    frequency = {}
    number_columns = ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6']
    
    for col in number_columns:
        for num in df[col]:
            frequency[num] = frequency.get(num, 0) + 1
    
    # 가중치 기반 선택
    weights = [frequency.get(i, 1) for i in range(1, 46)]
    
    predictions = []
    for _ in range(num_sets):
        # 가중치 기반으로 6개 번호 선택
        selected = random.choices(range(1, 46), weights=weights, k=6)
        # 중복 제거 및 정렬
        selected = sorted(list(set(selected)))
        # 6개가 되지 않으면 추가 선택
        while len(selected) < 6:
            additional = random.choices(range(1, 46), weights=weights, k=1)[0]
            if additional not in selected:
                selected.append(additional)
        selected.sort()
        predictions.append(selected)
    
    return predictions

def main():
    print("🎰 로또 번호 예측 테스트")
    print("=" * 50)
    
    # 샘플 데이터 생성
    print("📊 샘플 데이터 생성 중...")
    df = generate_sample_data()
    print(f"✅ {len(df)}회차 데이터 생성 완료")
    
    # 통계적 예측
    print("\n🎯 통계적 예측 결과 (5세트):")
    predictions = statistical_prediction(df, 5)
    
    for i, numbers in enumerate(predictions, 1):
        print(f"   세트 {i}: {numbers}")
    
    # 번호별 출현 빈도 분석
    print("\n📈 번호별 출현 빈도 (상위 10개):")
    frequency = {}
    for col in ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6']:
        for num in df[col]:
            frequency[num] = frequency.get(num, 0) + 1
    
    top_numbers = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    for num, freq in top_numbers:
        print(f"   {num}번: {freq}회")
    
    print("\n⚠️ 주의: 이는 참고용이며, 실제 당첨을 보장하지 않습니다.")

if __name__ == "__main__":
    main()
