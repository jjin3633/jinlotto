# ML 모델 스펙

이 문서는 프로젝트에서 사용되는 ML 모델들의 입력, 출력, 학습 절차 및 운영 정책을 정리합니다.

## 개요
- 각 포지션(1~6)별로 분류기(Classifier)를 학습하여 해당 포지션의 번호(1~45)를 예측합니다.
- 모델 유형: RandomForestClassifier (초기), 하이퍼파라미터 튜닝 스크립트 제공
- 파일 위치: `models/position_{i}_clf.pkl` 및 튜닝본 `models/position_{i}_clf_tuned.pkl`

## 입력 피처
`PredictionService._create_features`에서 생성되는 피처 목록(핵심)
- 각 포지션의 원본 값: `number_1`..`number_6` (기본적으로 타겟으로 사용)
- 이동평균: `{number_i}_ma5`, `{number_i}_ma10` (i=1..6)
- 번호별 출현 카운트: `freq_1`..`freq_45` (각 행에서 해당 번호가 등장했는지 합산)
- `odd_count`

모델은 학습 시 `draw_number`, `draw_date`, `bonus_number`, `number_1..6` 컬럼을 제거하고 위 파생 피처만 사용하여 학습합니다.

## 출력
- 클래스: 1..45 (각 포지션에 대해 확률 분포)
- `predict_proba`를 사용하여 상위 K 후보를 샘플링(운영에서 K=8 사용)

## 학습 절차
- 스크립트: `scripts/train_classifiers.py`
- 데이터: `backend/data/lotto_data.csv`
- 검증: TimeSeriesSplit 권장(시계열 누수 방지)
- 저장: `joblib.dump(model, path)`

## 운영 정책
- 모델 로딩: 서비스 시작 또는 첫 요청 시 디스크에서 로드 후 날짜별 캐시에 저장
- 메모리 최적화: `joblib.load(..., mmap_mode='r')` 시도
- 모델 관리: 대형 바이너리는 Git에서 언트랙 처리(권장). 장기 보관/배포는 S3/Release 권장

## 성능 측정
- Top‑1/Top‑3 accuracy, 분포 캘리브레이션, predict_proba 기반의 상위 후보 정밀도 측정 권장
- `scripts/evaluate_models.py` 로 포지션별 평가 스크립트 제공


