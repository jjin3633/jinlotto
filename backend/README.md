# 로또 번호 분석 백엔드 API

대한민국 로또(6/45) 과거 당첨 번호 데이터를 분석하여 통계 및 머신러닝 기반 번호 추천 서비스를 제공하는 FastAPI 기반 백엔드입니다.

## 🚀 주요 기능

- **데이터 수집 및 전처리**: 로또 당첨 번호 데이터 자동 수집 및 정제
- **통계 분석**: 번호별 출현 빈도, 핫/콜드 번호, 홀짝 비율 등 분석
- **머신러닝 예측**: RandomForest 기반 번호 예측 모델
- **시각화 데이터**: 차트 및 그래프용 데이터 제공
- **법적 고지**: 도박 중독 예방 및 책임 한계 고지

## 📋 API 엔드포인트

### 기본 정보
- `GET /` - API 정보 및 엔드포인트 목록
- `GET /api/health` - 서비스 상태 확인

### 데이터 분석
- `GET /api/data/summary` - 데이터 요약 정보
- `GET /api/analysis/comprehensive` - 종합 분석 결과
- `GET /api/analysis/frequency` - 번호별 출현 빈도
- `GET /api/analysis/hot-cold` - 핫/콜드 번호 분석

### 번호 예측
- `POST /api/predict` - 번호 예측 (statistical/ml/hybrid)

### 시각화
- `GET /api/visualization/frequency-chart` - 빈도 차트 데이터
- `GET /api/visualization/odd-even-chart` - 홀짝 비율 차트

### 기타
- `GET /api/disclaimer` - 법적 고지사항

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
# 개발 모드
python main.py

# 또는 uvicorn 직접 사용
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 테스트

```bash
# API 테스트 실행
python test_api.py
```

## 📊 예측 방법

### 1. Statistical (통계적)
- 과거 출현 빈도를 기반으로 한 가중치 기반 선택
- 가장 기본적이고 안정적인 방법

### 2. ML (머신러닝)
- RandomForest 모델을 사용한 패턴 학습
- 시계열 특성과 복잡한 패턴 분석

### 3. Hybrid (하이브리드)
- 통계적 방법과 ML 방법을 결합
- 두 방법의 장점을 모두 활용

## 🔧 프로젝트 구조

```
backend/
├── app/
│   ├── models/          # Pydantic 모델
│   ├── services/        # 비즈니스 로직
│   ├── routes/          # API 라우트
│   └── utils/           # 유틸리티
├── data/                # 데이터 파일
├── tests/               # 테스트 파일
├── main.py              # 메인 애플리케이션
├── requirements.txt     # 의존성
└── README.md           # 문서
```

## 🚀 Render 배포

### 1. Render 설정
- **Build Command**: `chmod +x build.sh && ./build.sh`
- **Start Command**: `chmod +x start.sh && ./start.sh`

### 2. 환경 변수
- `PYTHON_VERSION`: `3.9`
- `PORT`: `10000`

## ⚠️ 중요 고지사항

- 본 서비스는 **참고용**이며, 실제 당첨을 보장하지 않습니다
- 로또는 완전한 확률 게임으로 과학적 예측이 불가능합니다
- 건전한 복권 이용을 권장하며, 과도한 구매를 자제해 주세요
- 도박 중독 예방을 위해 적절한 금액으로 구매하시기 바랍니다

## 📝 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해 주세요.
