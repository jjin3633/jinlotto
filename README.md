# 🎰 JinLotto - 로또 번호 추천 서비스

## 📋 프로젝트 개요

대한민국 로또(6/45) 과거 당첨 번호 데이터를 분석하여, 통계 및 머신러닝 기반 "번호 추천" 서비스를 제공하는 웹 애플리케이션입니다.

## 🚀 주요 기능

- **📊 통계적 분석**: 번호별 출현 빈도, 홀짝 비율, 구간별 분포
- **🤖 머신러닝 예측**: RandomForest 기반 번호 예측
- **📈 고급 분석**: 계절별, 월별, 주별 패턴 분석
- **🎯 번호 추천**: 1세트 번호 자동 생성(하루 1회 고정)
- **🌐 실시간 데이터**: 최신 회차 정보 자동 업데이트
- **🧠 매칭/알림**: 전 회차와 예측 번호 매칭 후 1~5등 집계 슬랙 알림
- **🧘 스트레칭 유도 UX**: 유튜브 모달에서 60초 시청 후에만 번호 발급(40초 워밍업)
- **💬 의견 남기기**: 우측 상단 버튼 → 모달 입력 → 슬랙으로 의견 수집

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **Python 3.13**: 최신 Python 버전
- **pandas & numpy**: 데이터 분석
- **scikit-learn**: 머신러닝
- **requests**: API 통신

### Database
- **Supabase (PostgreSQL)**: 영구 저장소(예측/회차/매칭)
- **SQLAlchemy 2.0**: ORM/세션 관리
- **psycopg (psycopg3)**: PostgreSQL 드라이버 (Session/Transaction Pooler, IPv4 호환)

### Frontend
- **HTML5/CSS3**: 반응형 디자인
- **JavaScript**: 동적 인터페이스
- **Chart.js**: 데이터 시각화

### Deployment
- **Render**: 클라우드 배포
- **Gunicorn**: WSGI 서버

### Infra/DevOps
- **GitHub Actions**: Keep-Alive(10분), Weekly Update(월 09:00 KST)
- **Slack Incoming Webhooks**: 매칭 요약(1~5등), 서버 시작/종료, 예측 실패 로그, 사용자 의견 수집 알림

## 📁 프로젝트 구조

```
jinlotto/
├── README.md                 # 프로젝트 문서
├── requirements.txt          # Python 의존성 (psycopg3 사용)
├── runtime.txt               # Python 버전
├── Procfile                  # Render 배포 설정
├── render.yaml               # Render infra 설정(선택)
├── main.py                   # 애플리케이션 진입점 (backend.main:app 노출)
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
│   ├── data/              # 로컬 개발 데이터(운영에선 DB 사용)
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
python scripts/build_frontend.py
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
   - Build Command: `pip install -r requirements.txt && python scripts/build_frontend.py`
   - Start Command: `gunicorn main:app --bind 0.0.0.0:$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 180`
   - Health Check Path: `/api/health`

2. **환경 변수(Render)**
   - `DATABASE_URL`: Supabase Session/Transaction Pooler, psycopg3 스킴 사용
     - 예) `postgresql+psycopg://postgres.<ref>:<PASSWORD>@aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres?sslmode=require`
   - `SLACK_WEBHOOK_URL`: Slack 인커밍 웹훅 URL

3. **GitHub Actions(선택)**
   - Keep-Alive(10분 간격 헬스 핑): `.github/workflows/keep-alive.yml`
   - Weekly Update(월 09:00 KST): `.github/workflows/lotto-weekly-update.yml`
     - 리포지토리 시크릿: `BASE_URL`, `SLACK_WEBHOOK_URL`

## 📊 API 엔드포인트

### 기본 API
- `GET /api` - API 환영 메시지
- `GET /api/health` - 서비스 상태 확인

### 데이터 API
- `GET /api/data/summary` - 데이터 요약 정보
- `POST /api/data/collect` - 데이터 수집
- `POST /api/data/update` - 데이터 업데이트
 - `POST /api/data/sync-db` - CSV → DB(draws) 전체 백필
 - `POST /api/data/sync-db-range?start_draw=&end_draw=` - CSV → DB 구간 백필
 - `POST /api/data/match-latest` - 최신 회차 매칭 강제 + Slack 요약 발송(1~5등)

### 분석 API
- `GET /api/analysis/comprehensive` - 종합 분석
- `GET /api/analysis/statistical` - 통계 분석
- `GET /api/analysis/seasonal` - 계절별 분석

### 예측 API
- `POST /api/predict` - 번호 예측 (1세트)

### 기타/피드백 API
- `POST /api/feedback` - 사용자 의견 수집 → 슬랙 전송

### 디버그 API(운영 전 비활성화 권장)
- `GET /api/debug/db-conn` - DB 연결 확인
- `GET /api/debug/db-stats` - 테이블 카운트 확인

## 🔔 운영 로직(주요 자동화)

1) 매주 월요일 09:00 KST:
- GitHub Actions가 `POST /api/data/update` 호출
- 최신 회차를 `draws`에 upsert 후, 예측과 매칭 → Slack에 1~5등 요약 발송

2) 매칭 필터 규칙:
- `generated_for <= draw_date`
- `created_at <= draw_date 20:00 KST(= UTC 11:00)`

3) 서버 라이프사이클/장애 알림:
- 시작 시: "🚀 JinLotto 서버 시작" 슬랙 전송(중복 방지 처리)
- 종료 시: "🛑 JinLotto 서버 종료" 슬랙 전송
- 전역 예외: "❗ 서버 오류 발생: ..." 슬랙 전송
- 예측 실패: `/api/predict` 예외 시 상세 원인 슬랙 전송

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

### 사용자 의견 전송
```bash
curl -X POST "http://localhost:8000/api/feedback" \
     -H "Content-Type: application/json" \
     -d '{"message": "페이지 상단 여백을 조금 줄여주세요"}'
```

## 📈 성능 지표

- **페이지 로딩**: < 3초
- **API 응답**: < 2초
- **번호 생성**: < 1초
- **동시 사용자**: 100+ 지원

### 추가 최적화
- DB 인덱스 권장: `predictions(generated_for)`, `predictions(created_at)`, `matches(draw_number)`, `matches(prediction_id)`
- 워밍업: 스트레칭 모달 시청 40초 시점에 `/api/health` 1회 호출로 콜드스타트 완화

## 🖥️ 프론트 UX 요약
- 메인 버튼: "스트레칭 후 번호받기"
- 유튜브 모달: 60초 시청 시에만 [스트레칭 완료] 활성화(중간 40초에 서버 워밍업)
- 완료 시: 번호 발급 및 버튼 비활성화(하루 1회)
- 결과 영역 하단: "🍀 행운을 빌어요!"
- 우측 상단: "의견 남기기" 버튼 → 모달 입력 → 슬랙 알림

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

## 🗂️ 모델 파일 관리 및 저장소 용량 안내

- **중요**: 모델 바이너리(`models/*.pkl`)는 크기가 매우 클 수 있어 저장소 용량을 빠르게 증가시킵니다. 운영/배포에 사용하지 않는 튜닝 모델(`*_tuned.pkl`)과 연구용 순차 모델(`seq_position_*.pkl`)은 최신 커밋에서 추적 해제되어 원격 저장소에서 제거되어 있습니다. 로컬에는 파일이 그대로 남아 있으니 필요 시 복원 가능합니다.
- **권장 작업**:
  - 단기: 불필요한 모델을 로컬에서 백업한 뒤 `models/`내 정리(예: `seq_*.pkl`, `_tuned.pkl` 삭제 또는 보관)
  - 중기: 대형 바이너리는 **Git LFS**로 이전하거나(팀 전체 동의 필요), 외부 스토리지(S3, Drive)에 보관 후 CI/배포에서 다운로드하도록 구성하세요.
  - 장기: 원격 히스토리에서 대형 파일을 완전히 제거하려면 `git filter-repo` 또는 `git lfs migrate` 같은 히스토리 재작성 절차가 필요합니다(주의: 브랜치/PR 영향).

- **로컬에서 빠르게 확인/복원하는 방법**:
  - 현재 로컬 `models/`에 모델 파일이 남아 있으면 서비스는 그대로 작동합니다. 원격 저장소에서 제거된 파일을 다시 푸시하려면 일반 커밋으로 추가하면 됩니다(권장하지 않음).

## 🧪 디버깅 유틸리티

- 내부 확률(predict_proba)과 SHAP을 빠르게 확인하려면 프로젝트 루트에서 아래 스크립트를 실행하세요:
  ```bash
  # Windows PowerShell
  $env:PYTHONPATH = (Get-Location).ToString(); python .\scripts\show_proba_shap.py
  ```
- SHAP 계산은 데이터/샘플 크기에 따라 오래 걸리니, 스크립트 내 `X_sample` 크기를 줄여 빠르게 테스트하세요.

## 🔒 API 동작 관련 주의
- 화면상 노출되는 `reasoning`(근거) 정보는 기본적으로 빈 배열로 반환되어 **UI에 노출되지 않도록 설정**되어 있습니다(프라이버시/디자인 목적). 내부 로깅이나 디버깅을 위해 별도 활성화 가능합니다.

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
