# 데이터 사전: `lotto_data.csv`

이 문서는 프로젝트에서 사용하는 로또 원시 데이터(`backend/data/lotto_data.csv`)의 스키마, 샘플, 전처리 규칙을 정리합니다.

## 컬럼 설명
- `draw_number` (int) : 회차 번호 (예: 1, 2, ...)
- `draw_date` (date, yyyy-mm-dd) : 추첨일자
- `number_1` ~ `number_6` (int) : 추첨된 6개 번호(오름차순 보장되지 않음)
- `bonus_number` (int) : 보너스 번호
- `total_sales` (int, optional) : 총 판매액
- `first_prize_amount` (int, optional) : 1등 당첨금
- `first_prize_winners` (int, optional) : 1등 당첨자 수

## 데이터 타입/제약
- 모든 번호 컬럼은 1~45 사이의 정수여야 함. 범위를 벗어나면 이상치로 처리.
- `draw_date`에 파싱 오류가 발생하면 `NaT`로 설정 후 경고 로그 남김.

## 샘플 레코드
```csv
draw_number,draw_date,number_1,number_2,number_3,number_4,number_5,number_6,bonus_number,total_sales,first_prize_amount,first_prize_winners
1,2002-12-07,10,23,29,33,37,40,16,100000000000,2000000000,3
```

## 전처리 규칙 (`DataService.preprocess_data` 참고)
- `draw_date`를 pandas.to_datetime(format='mixed', errors='coerce')로 변환
- 번호 컬럼의 범위 체크(1~45) 및 이상치 로그
- 결측치는 생성 규칙에 따라 `fillna(0)` 또는 모델 입력에서 제거

## 피쳐 생성(ML용)
`PredictionService._create_features`에서 자동으로 생성되는 파생 컬럼:
- 각 위치별 이동평균: `{number_i}_ma5`, `{number_i}_ma10`
- 번호별 출현 카운트: `freq_1` ~ `freq_45` (각 행에서 해당 번호가 등장했는지 카운트)
- `odd_count`: 한 회차의 홀수 개수

## 저장 / 동기화
- CSV는 `backend/data/lotto_data.csv`에 저장. 운영에서는 Supabase(DB) 동기화 기능(`/api/data/sync-db`)을 사용.

---
참고: 추가 필드가 있을 경우 위 스키마를 갱신하세요. 머신러닝 특성 변경 시 `scripts/train_classifiers.py`와 `scripts/show_proba_shap.py`를 함께 검토해야 합니다.


