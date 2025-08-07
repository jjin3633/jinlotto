# 🎰 JinLotto - 로또 번호 추천 서비스

## 📋 프로젝트 개요

대한민국 로또(6/45) 과거 당첨 번호 데이터를 분석하여, 통계 및 머신러닝 기반 "번호 추천" 서비스를 제공하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **📊 통계적 분석**: 번호별 출현 빈도, 홀짝 비율, 구간별 분포
- **🤖 머신러닝 예측**: RandomForest 기반 번호 예측
- **📈 고급 분석**: 계절별, 월별, 주별 패턴 분석
- **🎯 번호 추천**: 5세트 번호 자동 생성
- **🌐 실시간 데이터**: 최신 회차 정보 자동 업데이트

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **Python 3.13**: 최신 Python 버전
- **pandas & numpy**: 데이터 분석
- **scikit-learn**: 머신러닝
- **requests**: API 통신

### Frontend
- **HTML5/CSS3**: 반응형 디자인
- **JavaScript**: 동적 인터페이스
- **Chart.js**: 데이터 시각화

### Deployment
- **Render**: 클라우드 배포
- **Gunicorn**: WSGI 서버

## 📁 프로젝트 구조

```
jinlotto/
├── README.md                 # 프로젝트 문서
├── requirements.txt          # Python 의존성
├── runtime.txt              # Python 버전
├── Procfile                 # Render 배포 설정
├── build_frontend.py        # 프론트엔드 빌드 스크립트
├── main.py                  # 애플리케이션 진입점
├── .gitignore              # Git 무시 파일
├── docs/                   # 문서
│   ├── DEPLOYMENT.md       # 배포 가이드
│   ├── TEST_DEPLOYMENT.md  # 테스트 체크리스트
│   └── prd.md             # 요구사항 문서
├── backend/                # 백엔드 코드
│   ├── main.py            # FastAPI 애플리케이션
│   ├── app/               # 애플리케이션 모듈
│   │   ├── models/        # 데이터 모델
│   │   ├── services/      # 비즈니스 로직
│   │   ├── routes/        # API 라우트
│   │   └── utils/         # 유틸리티
│   ├── data/              # 데이터 파일
│   ├── tests/             # 테스트 코드
│   └── static/            # 정적 파일 (빌드됨)
└── frontend/              # 프론트엔드 코드
    ├── index.html         # 메인 페이지
    ├── styles.css         # 스타일시트
    └── script.js          # JavaScript 로직
```

## 🚀 빠른 시작

### 로컬 개발

1. **저장소 클론**
```bash
git clone https://github.com/jjin3633/jinlotto.git
cd jinlotto
```

2. **가상환경 생성**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **프론트엔드 빌드**
```bash
python build_frontend.py
```

5. **서버 실행**
```bash
python main.py
```

6. **브라우저에서 접속**
```
http://localhost:8000
```

### 배포

1. **Render에서 배포**
   - GitHub 저장소 연결
   - Build Command: `pip install -r requirements.txt && python build_frontend.py`
   - Start Command: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120`

## 📊 API 엔드포인트

### 기본 API
- `GET /api` - API 환영 메시지
- `GET /api/health` - 서비스 상태 확인

### 데이터 API
- `GET /api/data/summary` - 데이터 요약 정보
- `POST /api/data/collect` - 데이터 수집
- `POST /api/data/update` - 데이터 업데이트

### 분석 API
- `GET /api/analysis/comprehensive` - 종합 분석
- `GET /api/analysis/statistical` - 통계 분석
- `GET /api/analysis/seasonal` - 계절별 분석

### 예측 API
- `POST /api/predict` - 번호 예측 (5세트)

## 🎯 사용 예시

### 번호 예측
```bash
curl -X POST "http://localhost:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{"num_sets": 5}'
```

### 데이터 요약
```bash
curl "http://localhost:8000/api/data/summary"
```

## 📈 성능 지표

- **페이지 로딩**: < 3초
- **API 응답**: < 2초
- **번호 생성**: < 1초
- **동시 사용자**: 100+ 지원

## 🔧 개발 가이드

### 코드 스타일
- **Python**: PEP 8 준수
- **JavaScript**: ES6+ 사용
- **CSS**: BEM 방법론

### 테스트
```bash
# 백엔드 테스트
cd backend
python -m pytest tests/

# 프론트엔드 테스트
# 브라우저에서 수동 테스트
```

### 배포 체크리스트
- [ ] 모든 테스트 통과
- [ ] 프론트엔드 빌드 성공
- [ ] API 엔드포인트 동작 확인
- [ ] 성능 테스트 완료

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## ⚠️ 면책 조항

이 서비스는 **참고용**으로만 제공됩니다. 로또 번호 추천은 과학적 예측이 불가능하며, 실제 당첨을 보장하지 않습니다. 건전한 복권 이용을 권장합니다.

## 📞 문의

- **GitHub**: [jjin3633/jinlotto](https://github.com/jjin3633/jinlotto)
- **이메일**: jjin@motiphysio.com

---

**🎉 행운을 빕니다!** 🍀
