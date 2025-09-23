# 🎲 JinLotto — 스트레칭 로또 프로젝트 완전 가이드 (2025.09.22)

이 문서는 **스트레칭 로또** 프로젝트의 모든 것을 담은 **완전한 운영 가이드**입니다. 신규 개발자가 이 문서만으로도 프로젝트를 완전히 이해하고 운영할 수 있도록 작성되었습니다.

> ⚠️ **보안 주의**: 실제 API 키나 웹훅 URL은 이 문서에 포함되지 않습니다. 모든 시크릿은 Render 환경변수에서 관리됩니다.

---

## 📋 목차

1. [🎯 서비스 개요](#-서비스-개요)
2. [🏗️ 프로젝트 구조](#️-프로젝트-구조)
3. [🚀 배포 및 운영](#-배포-및-운영)
4. [💻 로컬 개발 환경](#-로컬-개발-환경)
5. [🔌 API 엔드포인트](#-api-엔드포인트)
6. [🤖 ML 예측 파이프라인](#-ml-예측-파이프라인)
7. [🎨 프론트엔드 구조](#-프론트엔드-구조)
8. [🗄️ 데이터베이스 스키마](#️-데이터베이스-스키마)
9. [⏰ 자동화 및 크론 작업](#-자동화-및-크론-작업)
10. [🔒 보안 및 환경변수](#-보안-및-환경변수)
11. [📊 SEO 및 모니터링](#-seo-및-모니터링)
12. [🛠️ 도구 및 스크립트](#️-도구-및-스크립트)
13. [📈 최근 주요 변경사항](#-최근-주요-변경사항)
14. [🚨 운영 런북](#-운영-런북)
15. [✅ 인수인계 체크리스트](#-인수인계-체크리스트)

---

## 🎯 서비스 개요

### 핵심 컨셉
- **서비스명**: 스트레칭 로또 (JinLotto)
- **컨셉**: 스트레칭 후 AI 추천 로또 번호를 받는 건강한 습관 형성 서비스
- **URL**: https://stretchinglotto.motiphysio.com/ (메인), http://43.201.75.105:8000 (서브)

### 사용자 플로우
1. **스트레칭 후 번호 받기** 버튼 클릭
2. **스트레칭 영상 1분 시청** (YouTube API 랜덤 영상)
3. **스트레칭 완료** 후 **닉네임 입력**
4. **AI 분석된 개인 맞춤 로또 번호** 확인

### 기술 스택
- **백엔드**: FastAPI + SQLAlchemy + Supabase PostgreSQL
- **프론트엔드**: Vanilla HTML/CSS/JavaScript
- **ML**: scikit-learn RandomForestClassifier (포지션별 6개 모델)
- **배포**: Render (Web Service + 7개 Cron Jobs)
- **알림**: Slack Webhooks (메인 + 스트레칭 알림)
- **외부 API**: 동행복권 API, YouTube API

### 핵심 운영 포인트
1. **하루 1회 고정 번호**: 사용자별 쿠키(`jl_uid`) 기반 고정 추천
2. **빠른 응답**: 첫 요청 시 통계적 빠른 응답 → 백그라운드 ML 정제
3. **자동 매칭**: 매주 월요일 10시 KST 자동 당첨 결과 매칭 및 슬랙 알림
4. **스트레칭 알림**: 매시간 50분 MZ 감성 슬랙 알림 (10:50~16:50)

---

## 🏗️ 프로젝트 구조

```
승진/1. Project/2. 번호추첨/
├── 📁 assets/                     # 정적 에셋 (이미지, 미디어)
│   ├── 📁 images/                 # 이미지 파일
│   │   ├── favicon.png            # 파비콘
│   │   ├── laurel1.png, laurel2.png # 로렐 장식 이미지
│   │   └── logo.svg               # 로고 SVG
│   └── 📁 media/
│       └── Main_KR_Home.mp4       # 메인 비디오
├── 📁 backend/                    # 백엔드 애플리케이션
│   ├── 📁 app/
│   │   ├── 📁 db/                 # 데이터베이스 모델 및 세션
│   │   │   ├── models.py          # SQLAlchemy 모델 (User, Prediction, Draw, Match)
│   │   │   └── session.py         # DB 세션 관리 (Supabase 연결)
│   │   ├── 📁 models/             # Pydantic 모델
│   │   │   └── lotto_models.py    # API 요청/응답 모델 (닉네임 필드 포함)
│   │   ├── 📁 routes/             # API 라우터
│   │   │   ├── api.py             # 메인 API 엔드포인트 (/predict, /health 등)
│   │   │   └── static.py          # 정적 파일 서빙 (SEO 최적화)
│   │   ├── 📁 services/           # 비즈니스 로직
│   │   │   ├── analysis_service.py # 통계 분석
│   │   │   ├── data_service.py    # 로또 데이터 수집/전처리
│   │   │   ├── match_service.py   # 당첨 매칭 로직
│   │   │   └── prediction_service.py # ML 예측 서비스 (핵심 로직)
│   │   └── 📁 utils/
│   │       └── slack_notifier.py  # 슬랙 알림 헬퍼
│   ├── 📁 data/                   # 로컬 데이터
│   │   ├── app.db                 # SQLite (로컬 개발용)
│   │   └── lotto_data.csv         # 로또 회차 데이터 (1-1190회차)
│   ├── 📁 static/                 # 배포된 정적 파일 (frontend에서 복사됨)
│   │   ├── index.html             # 메인 페이지 (닉네임 모달 포함)
│   │   ├── script.js              # 프론트엔드 로직 (YouTube API, 닉네임 처리)
│   │   ├── styles.css             # 스타일시트 (반응형 디자인)
│   │   ├── robots.txt, sitemap.xml, rss.xml # SEO 파일들
│   │   └── [미디어 파일들]         # 이미지, 비디오 등
│   ├── batch_update.py            # 로또 데이터 배치 업데이트
│   ├── health_monitor.py          # 헬스 모니터링
│   ├── main.py                    # FastAPI 앱 인스턴스
│   ├── test_api.py, test_prediction.py # 테스트 파일
│   └── [기타 설정 파일들]
├── 📁 frontend/                   # 프론트엔드 소스 (개발용)
│   ├── index.html                 # 메인 HTML (닉네임 모달 구조 포함)
│   ├── script.js                  # JavaScript 로직 (사용자 플로우)
│   ├── styles.css                 # CSS 스타일 (닉네임 모달 스타일 포함)
│   └── [SEO 파일들]               # robots.txt, sitemap.xml, rss.xml 등
├── 📁 models/                     # ML 모델 파일
│   ├── position_0_clf.pkl         # 1번 자리 분류기 (기본)
│   ├── position_0_clf_tuned.pkl   # 1번 자리 분류기 (튜닝됨)
│   ├── position_1-5_clf.pkl       # 2-6번 자리 분류기들
│   ├── position_1-5_clf_tuned.pkl # 2-6번 자리 분류기들 (튜닝됨)
│   └── seq_position_0-5.pkl       # 시퀀셜 모델들
├── 📁 scripts/                    # ML 학습/평가 스크립트
│   ├── build_frontend.py          # 프론트엔드 빌드 스크립트
│   ├── train_classifiers.py       # 모델 학습
│   ├── tune_classifiers.py        # 하이퍼파라미터 튜닝
│   ├── train_sequential_models.py # 시퀀셜 모델 학습
│   ├── evaluate_models.py         # 모델 평가
│   ├── show_proba_shap.py         # SHAP 분석
│   └── evaluation_results.csv     # 평가 결과
├── 📁 tools/                      # 운영 도구
│   ├── monday_automation.py       # 🆕 월요일 9시 통합 자동화 (MZ 스타일)
│   ├── stretching_reminder.py     # 스트레칭 알림봇 (MZ 감성)
│   ├── weekly_summary_cron.py     # 주간 당첨 결과 요약
│   ├── accurate_weekly_match.py   # 정확한 매칭 로직
│   ├── local_weekly_match.py      # 로컬 매칭 테스트
│   ├── supabase_predict_summary.py # Supabase 예측 요약
│   └── [SEO 디버그 도구들]        # seo_monitor.py, robots_debug.py 등
├── 📁 docs/                       # 문서
│   ├── API_SPEC.md                # API 명세
│   ├── DATA_SCHEMA.md             # 데이터 스키마
│   ├── DEPLOY_RUNBOOK.md          # 배포 런북
│   ├── ML_MODEL_SPEC.md           # ML 모델 명세
│   └── [기타 문서들]
├── deploy_to_server.ps1/.sh       # 서버 배포 스크립트
├── main.py                        # 루트 진입점 (Render용)
├── render.yaml                    # Render 배포 설정 (월요일 9시 통합 자동화)
├── requirements.txt               # Python 의존성
├── PROJECT_OVERVIEW.md            # 이 문서
└── README.md                      # 프로젝트 개요
```

---

## 🚀 배포 및 운영

### Render 배포 설정

**Web Service 설정** (`render.yaml`):
```yaml
services:
  - type: web
    name: jinlotto
    env: python
    plan: free
    autoDeploy: true
    region: oregon
    buildCommand: |
      pip install -r requirements.txt
      python -c "
      import shutil
      shutil.copy2('frontend/index.html', 'backend/static/index.html')
      shutil.copy2('frontend/script.js', 'backend/static/script.js')  
      shutil.copy2('frontend/styles.css', 'backend/static/styles.css')
      print('✅ Frontend files copied to backend/static/')
      "
    startCommand: |
      gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 300
    healthCheckPath: /api/health
```

**핵심 환경변수**:
- `ENABLE_ML`: ML 모델 사용 여부 (true/false)
- `WARMUP_ON_STARTUP`: 시작 시 모델 워밍업 (false - 배포 타임아웃 방지)
- `SLACK_WEBHOOK_URL`: 메인 슬랙 웹훅 (시크릿)
- `STRETCHING_SLACK_WEBHOOK_URL`: 스트레칭 알림용 웹훅 (시크릿)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`: Supabase 연결 (시크릿)

### 배포 프로세스
1. **GitHub 푸시** → Render 자동 배포 트리거
2. **빌드 단계**: Python 의존성 설치 + 프론트엔드 파일 복사 (Python 스크립트)
3. **시작 단계**: Gunicorn으로 FastAPI 앱 실행 (2 workers, 300초 타임아웃)
4. **헬스체크**: `/api/health` 엔드포인트 확인

### 최근 배포 최적화 (2025.09.19)
- **문제**: `cp` 명령어 호환성 이슈로 프론트엔드 파일 복사 실패
- **해결**: Python `shutil.copy2()` 사용으로 크로스 플랫폼 호환성 확보
- **결과**: 닉네임 모달 및 메인 비디오 수정사항 정상 배포

---

## 💻 로컬 개발 환경

### 설정 단계
```bash
# 1. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # Linux/Mac

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 프론트엔드 빌드 (선택사항)
python scripts/build_frontend.py

# 4. 서버 실행
python main.py
# 또는: uvicorn backend.main:app --reload --port 8000

# 5. 접속
# http://localhost:8000
```

### 개발 도구
- **API 테스트**: `backend/test_api.py`, `backend/test_prediction.py`
- **모델 학습**: `python scripts/train_classifiers.py`
- **모델 평가**: `python scripts/evaluate_models.py`
- **데이터 수집**: `POST /api/data/collect` 또는 `POST /api/data/update`

### 의존성 (`requirements.txt`)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
pandas
numpy
scikit-learn
requests==2.31.0
beautifulsoup4==4.12.2
python-multipart==0.0.6
pydantic
SQLAlchemy==2.0.31
psycopg[binary]==3.2.9  # Python 3.13 호환
```

---

## 🔌 API 엔드포인트

### 핵심 엔드포인트

#### `POST /api/predict` - 로또 번호 예측
**목적**: 사용자별 하루 고정 추천 번호 반환 (닉네임 포함)

**요청**:
```json
{
  "method": "statistical",  // statistical, ml, hybrid
  "num_sets": 1,
  "include_bonus": false,
  "nickname": "홍길동"       // 닉네임 (2025.09.19 추가)
}
```

**응답**:
```json
{
  "success": true,
  "message": "오늘의 고정 추천을 반환했습니다.",
  "data": {
    "mode": "daily-fixed",
    "generated_for": "20250919",
    "valid_until": "2025-09-20T00:00:00+09:00",
    "user_key": "uuid-string",
    "sets": [[3,6,14,19,26,31]],
    "confidence_scores": [0.533],
    "reasoning": [],
    "analysis_summary": "오늘(20250919)의 고정 추천 세트"
  }
}
```

**핵심 로직**:
1. 쿠키 `jl_uid`로 사용자 식별 (없으면 새로 생성)
2. 날짜별 고정 추천 파일 확인 (`backend/data/daily_recommendations/`)
3. 없으면 통계적 빠른 응답 + 백그라운드 ML 정제
4. 닉네임과 함께 Supabase `predictions` 테이블에 저장

#### `GET /api/health` - 헬스체크
**목적**: 서비스 상태 확인 (경량, 빠른 응답)
```json
{
  "status": "healthy",
  "message": "로또 분석 서비스가 정상 작동 중입니다."
}
```

#### 데이터 관리 API
- `POST /api/data/collect`: 동행복권 API에서 회차 데이터 수집
- `POST /api/data/update`: 최신 회차만 갱신
- `POST /api/data/sync-db`: CSV → Supabase 동기화

#### 정적 파일 서빙 (`backend/app/routes/static.py`)
- `/sitemap.xml`: SEO 사이트맵 (XML, Cache-Control 헤더)
- `/rss.xml`: RSS 피드 (XML, 인코딩 최적화)
- `/robots.txt`: 크롤링 규칙 (Allow: /)
- `/static/*`: 정적 파일 (이미지, CSS, JS)

---

## 🤖 ML 예측 파이프라인

### 모델 구조
- **타입**: RandomForestClassifier × 6개 (포지션별)
- **파일**: `models/position_{0-5}_clf.pkl`
- **입력**: 피처 엔지니어링된 수치 데이터 (이동평균, 빈도수, 홀수 개수)
- **출력**: 1-45번 각 번호의 선택 확률

### 예측 프로세스 (`backend/app/services/prediction_service.py`)
```python
class PredictionService:
    def get_daily_fixed_predictions(self, user_key: str, date_str: str, num_sets: int = 1):
        # 1. 캐시된 추천 확인
        cache_file = f"backend/data/daily_recommendations/{date_str}/{user_key}.json"
        if os.path.exists(cache_file):
            return load_cached_prediction(cache_file)
        
        # 2. 빠른 통계적 응답 생성
        quick_response = generate_statistical_prediction(num_sets)
        
        # 3. 백그라운드 ML 정제 큐잉
        if ENABLE_ML:
            queue_ml_refinement(user_key, date_str, num_sets)
        
        return quick_response

    def _create_features(self, df):
        # 이동평균 (5회차, 10회차)
        for pos in range(6):
            df[f'number_{pos+1}_ma5'] = df[f'number_{pos+1}'].rolling(5).mean()
            df[f'number_{pos+1}_ma10'] = df[f'number_{pos+1}'].rolling(10).mean()
        
        # 번호별 빈도수 (1-45)
        for num in range(1, 46):
            df[f'freq_{num}'] = calculate_frequency(df, num)
        
        # 홀수 개수
        df['odd_count'] = count_odd_numbers(df)
        
        return df
```

### 신뢰도 계산
```python
def calculate_confidence(prediction_data):
    confidence = (
        CONF_BASE +  # 기본 신뢰도 (0.40)
        CONF_W_CONSENSUS * consensus_ratio +  # 모델 간 합의도 (0.30)
        CONF_W_HOT * hot_number_ratio +       # 핫넘버 포함 비율 (0.10)
        entropy_bonus                         # 엔트로피 기반 보너스
    )
    return min(max(confidence, CONF_MIN), CONF_MAX)  # 0.40 ~ 0.80 범위
```

### 제약 조건
- **홀짝 균형**: `ENFORCE_ODD_EVEN_BALANCE=true`
- **구간 분포**: `ENFORCE_RANGE_COVERAGE=true` (1-15, 16-30, 31-45)
- **연속 제한**: `MAX_CONSECUTIVE=2` (최대 2개 연속 번호)

---

## 🎨 프론트엔드 구조

### 핵심 파일
- **`frontend/index.html`**: 메인 페이지 구조 (닉네임 모달 포함)
- **`frontend/script.js`**: 사용자 인터랙션 로직 (YouTube API, 닉네임 처리)
- **`frontend/styles.css`**: 반응형 스타일시트 (닉네임 모달 스타일)

### 사용자 플로우 구현

#### 1. 메인 비디오 자동재생 (`script.js`)
```javascript
function initMainVideo() {
    const mainVideo = document.querySelector('.ad-video');
    if (mainVideo) {
        const tryAutoplay = () => {
            mainVideo.play().catch(error => {
                console.log('자동재생 실패:', error);
                // 사용자 클릭 시 재생 폴백
                mainVideo.addEventListener('click', () => {
                    mainVideo.play();
                }, { once: true });
            });
        };
        tryAutoplay();
        // 사용자 인터랙션 시 재시도
        document.addEventListener('click', tryAutoplay, { once: true });
        document.addEventListener('touchstart', tryAutoplay, { once: true });
    }
}
```

#### 2. 스트레칭 모달 (YouTube API)
```javascript
// YouTube API 통합
function loadYouTubeAPI() {
    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
}

// 1분 시청 타이머
function startWatchTimer() {
    watchTimer = setInterval(() => {
        secondsWatched++;
        updateWatchProgress();
        if (secondsWatched >= 60) {
            enableStretchDoneButton();
        }
    }, 1000);
}

// 랜덤 영상 선택
const YT_VIDEO_IDS = [
    'RUGuHL0-Yug', 'TK-svYT9Qqg', 'WXtLkFVS2QY', 
    'XvG6EZTGYjs', 'Qm1Q8YYop18'
];
```

#### 3. 닉네임 입력 모달 (2025.09.19 추가)
```javascript
function handleStretchDone() {
    handleStretchClose();
    openNicknameModal();  // 스트레칭 완료 → 닉네임 입력
}

function handleNicknameConfirm() {
    const nickname = nicknameInput.value.trim();
    if (!nickname) {
        alert('닉네임을 입력해주세요!');
        return;
    }
    closeNicknameModal();
    handlePrediction(nickname);  // 닉네임과 함께 예측 요청
}

async function handlePrediction(nickname = null) {
    const response = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method: 'statistical',
            num_sets: 1,
            include_bonus: false,
            nickname: nickname  // 닉네임 포함
        }),
    });
    // ... 응답 처리
}
```

### 반응형 디자인 (`styles.css`)
```css
/* 닉네임 모달 스타일 */
.nickname-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

.nickname-input:focus {
    outline: none;
    border-color: #4285f4;
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
}

/* 모바일 우선 반응형 */
@media (max-width: 768px) {
    .modal-content {
        width: 95vw;
        margin: 20px auto;
    }
}
```

---

## 🗄️ 데이터베이스 스키마

### Supabase PostgreSQL 테이블

#### `users` 테이블
```sql
CREATE TABLE users (
    user_key VARCHAR(64) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Seoul')
);
```

#### `predictions` 테이블 (2025.09.19 닉네임 추가)
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_key VARCHAR(64) REFERENCES users(user_key),
    generated_for DATE NOT NULL,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Seoul'),
    set_index INTEGER NOT NULL,
    numbers JSON NOT NULL,  -- [n1, n2, n3, n4, n5, n6]
    source VARCHAR(32) DEFAULT 'daily-fixed',
    nickname VARCHAR(50)    -- 2025.09.19 추가
);

-- 인덱스
CREATE INDEX idx_predictions_user_key ON predictions(user_key);
CREATE INDEX idx_predictions_generated_for ON predictions(generated_for);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);
```

#### `draws` 테이블
```sql
CREATE TABLE draws (
    draw_number INTEGER PRIMARY KEY,
    draw_date DATE NOT NULL,
    numbers JSON NOT NULL,  -- [n1, n2, n3, n4, n5, n6]
    bonus_number INTEGER NOT NULL
);
```

#### `matches` 테이블
```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES predictions(id),
    draw_number INTEGER REFERENCES draws(draw_number),
    rank INTEGER NOT NULL,  -- 1-5등 (0=꽝)
    match_count INTEGER NOT NULL,
    bonus_match BOOLEAN NOT NULL,
    matched_numbers JSON NOT NULL,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'Asia/Seoul')
);
```

### RLS (Row Level Security) 정책
```sql
-- 모든 테이블에 RLS 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE draws ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

-- 임시 전체 허용 정책 (운영 시 세분화 필요)
CREATE POLICY "Temporary allow all" ON users FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON predictions FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON draws FOR ALL TO public USING (true);
CREATE POLICY "Temporary allow all" ON matches FOR ALL TO public USING (true);
```

### 타임존 처리 (`backend/app/db/models.py`)
```python
def kst_now():
    """한국 시간(KST) 기준 현재 시간 반환 (timezone-naive로 저장)"""
    kst_time = datetime.now(timezone(timedelta(hours=9)))
    # Supabase에서는 timezone-naive datetime을 저장하므로 timezone 정보 제거
    return kst_time.replace(tzinfo=None)
```

---

## ⏰ 자동화 및 크론 작업

### Render Cron Jobs (7개)

#### 1. 월요일 9시 통합 자동화 🆕
```yaml
- type: cron
  name: lotto-monday-automation
  # 매주 월요일 00:00 UTC = 09:00 KST (한국 시간 오전 9시)
  schedule: "0 0 * * 1"
  env: python
  region: oregon
  command: python tools/monday_automation.py
  envVars:
    - key: SLACK_WEBHOOK_URL
      sync: false
    - key: MONITOR_BASE_URL
      sync: false
    - key: SUPABASE_URL
      sync: false
    - key: SUPABASE_ANON_KEY
      sync: false
    - key: SCHEDULER_TOKEN
      sync: false
```

**통합 작업 내용**:
1. 최신 로또 번호 업데이트
2. 당첨자 집계 실행
3. MZ 스타일 슬랙 알림 전송
4. 오류 처리 및 상세 로깅

#### 2. 헬스 모니터링
```yaml
- type: cron
  name: lotto-health-monitor
  schedule: "*/5 * * * *"  # 5분마다
  command: python backend/health_monitor.py
```

#### 3. 스트레칭 알림 (6개 작업)
```yaml
# 10:50, 11:50, 12:50, 14:50, 15:50, 16:50 KST
- type: cron
  name: stretching-reminder-10-50
  schedule: "50 1 * * *"  # 10:50 KST = 01:50 UTC
  command: python tools/stretching_reminder.py
  envVars:
    - key: STRETCHING_SLACK_WEBHOOK_URL
      sync: false  # 환경변수로 관리
```

### 매칭 로직 상세 (`tools/accurate_weekly_match.py`)

#### 정확한 기간 필터링
```python
def get_predictions_for_matching(supabase, draw_number: int, draw_date: date):
    """
    특정 회차에 대해 매칭할 예측들을 가져옴
    - 이전 회차 추첨 이후 ~ 현재 회차 추첨 전까지의 예측만 포함
    """
    # 이전 회차 정보 가져오기
    prev_draw = supabase.table("draws").select("*").eq("draw_number", draw_number - 1).execute()
    
    if prev_draw.data:
        # 이전 회차 추첨일 다음날 00:00 KST
        prev_date = datetime.fromisoformat(prev_draw.data[0]["draw_date"])
        start_time = datetime.combine(prev_date.date() + timedelta(days=1), time.min)
    else:
        # 첫 회차인 경우 1주일 전부터
        start_time = datetime.combine(draw_date - timedelta(days=7), time.min)
    
    # 현재 회차 추첨일 20:00 KST (추첨 시간)
    end_time = datetime.combine(draw_date, time(20, 0))
    
    # KST 기준으로 필터링
    start_kst_iso = start_time.isoformat()
    end_kst_iso = end_time.isoformat()
    
    predictions = supabase.table("predictions").select("*").gte(
        "created_at", start_kst_iso
    ).lt("created_at", end_kst_iso).execute()
    
    return predictions.data
```

---

## 🔒 보안 및 환경변수

### 환경변수 관리

#### Render Dashboard에서 설정해야 할 시크릿
```bash
# 데이터베이스
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...

# 슬랙 웹훅 (2025.09.18 보안 강화)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
STRETCHING_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...

# 모니터링
MONITOR_BASE_URL=https://stretchinglotto.motiphysio.com/

# ML 설정
ENABLE_ML=true
WARMUP_ON_STARTUP=false  # 배포 타임아웃 방지
```

#### 코드에서 안전한 사용 (`tools/stretching_reminder.py`)
```python
# ❌ 절대 금지 (2025.09.18 이전)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# ✅ 올바른 방법 (2025.09.18 이후)
SLACK_WEBHOOK_URL = os.getenv("STRETCHING_SLACK_WEBHOOK_URL")
if not SLACK_WEBHOOK_URL:
    print("ERROR: STRETCHING_SLACK_WEBHOOK_URL not set", file=sys.stderr)
    sys.exit(1)
```

### 보안 이슈 및 해결 (2025.09.18)
- **문제**: 하드코딩된 웹훅 URL이 GitHub에 노출되어 Slack에서 무효화
- **해결**: 모든 웹훅 URL을 환경변수로 이동
- **적용**: `render.yaml`에서 `sync: false`로 설정하여 Render Dashboard에서 관리

### 보안 체크리스트
- [ ] **웹훅 URL 노출 확인**: GitHub 히스토리에 하드코딩된 웹훅 없는지 확인
- [ ] **API 키 로테이션**: 노출된 키는 즉시 폐기하고 새 키 발급
- [ ] **RLS 정책**: Supabase 테이블별 적절한 접근 제어 설정
- [ ] **CORS 설정**: 필요한 도메인만 허용
- [ ] **입력 검증**: 사용자 입력 (닉네임 등) 길이 제한 및 검증 (최대 50자)

---

## 📊 SEO 및 모니터링

### SEO 최적화 (2025.08.27 완료)

#### 메타 태그 및 구조화 데이터 (`frontend/index.html`)
```html
<title>스트레칭 로또 | 로또 번호 추천</title>
<meta name="description" content="스트레칭 후 로또 번호를 받아보세요. 건강한 습관과 함께하는 로또 번호 생성기">
<meta name="keywords" content="로또, 로또번호, 번호추천, 스트레칭, 운동, AI추천">
<link rel="canonical" href="https://stretchinglotto.motiphysio.com/">

<!-- 구조화 데이터 -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "스트레칭 로또",
  "description": "스트레칭 후 로또 번호를 받아보세요...",
  "url": "https://stretchinglotto.motiphysio.com/"
}
</script>
```

#### robots.txt (크롤링 허용)
```txt
User-agent: *
Allow: /

# SEO 파일들 명시적 허용
Allow: /sitemap.xml
Allow: /rss.xml
Allow: /robots.txt

Sitemap: https://stretchinglotto.motiphysio.com/sitemap.xml
```

#### sitemap.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://stretchinglotto.motiphysio.com/</loc>
    <lastmod>2025-08-27</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

#### RSS 피드 (`frontend/rss.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>스트레칭 로또 - 건강한 습관과 함께하는 로또</title>
    <link>https://stretchinglotto.motiphysio.com/</link>
    <description>스트레칭 후 AI가 추천하는 로또 번호를 받아보세요.</description>
    <lastBuildDate>Wed, 27 Aug 2025 11:15:51 +0900</lastBuildDate>
  </channel>
</rss>
```

### Google Search Console 설정
- **사이트맵 제출**: `https://stretchinglotto.motiphysio.com/sitemap.xml`
- **RSS 피드**: `https://stretchinglotto.motiphysio.com/rss.xml`
- **소유권 확인**: `<meta name="google-site-verification" content="..."/>`

### SEO 디버그 도구
```python
# tools/seo_monitor.py - SEO 상태 모니터링
def check_seo_health():
    checks = [
        check_sitemap_accessibility(),
        check_rss_feed_validity(),
        check_robots_txt(),
        check_page_load_speed()
    ]
    return generate_seo_report(checks)
```

---

## 🛠️ 도구 및 스크립트

### ML 관련 스크립트

#### `scripts/train_classifiers.py` - 모델 학습
```python
def train():
    ds = DataService()
    df = ds.load_data()
    features_df = prediction_service._create_features(df)
    
    for position in range(6):
        X = features_df.drop(columns=number_columns).fillna(0)
        y = features_df[f'number_{position+1}']
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        model.fit(X, y)
        
        joblib.dump(model, f'models/position_{position}_clf.pkl')
        print(f"✅ Position {position} model saved")
```

#### `scripts/evaluate_models.py` - 모델 평가
```python
def evaluate_with_time_series_split():
    tscv = TimeSeriesSplit(n_splits=5)
    scores = []
    
    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        scores.append(score)
    
    return np.mean(scores), np.std(scores)
```

### 운영 도구

#### `tools/stretching_reminder.py` - MZ 감성 스트레칭 알림봇
```python
MZ_MESSAGES = [
    {
        "text": "🏃‍♀️ 스트레칭 타임이에요! 몸이 굳어가고 있어요 ㅠㅠ",
        "emoji": "🤸‍♀️"
    },
    {
        "text": "💪 잠깐! 스트레칭하고 로또 번호 받아가세요~ 일석이조 아니겠어요?",
        "emoji": "🎯"
    },
    {
        "text": "🧘‍♀️ 목과 어깨가 뻐근하지 않나요? 스트레칭 한번 하고 행운의 번호도 받아보세요!",
        "emoji": "✨"
    }
]

def send_mz_stretching_reminder():
    message = random.choice(MZ_MESSAGES)
    payload = {
        "text": f"{message['emoji']} {message['text']}\n\n🎲 <{JINLOTTO_URL}|지금 바로 스트레칭하고 번호받기>"
    }
    
    response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
    if response.status_code == 200:
        print("✅ 스트레칭 알림 전송 성공")
    else:
        print(f"❌ 스트레칭 알림 전송 실패: {response.status_code}")
```

#### `tools/weekly_summary_cron.py` - 주간 당첨 결과 요약
```python
def generate_weekly_summary():
    # 1. 최신 회차 정보 가져오기
    latest_draw = get_latest_draw_from_supabase()
    
    # 2. 해당 회차에 대한 예측들 매칭
    predictions = get_predictions_for_matching(latest_draw)
    matches = evaluate_matches_for_draw(predictions, latest_draw)
    
    # 3. 통계 생성
    stats = {
        "total_predictions": len(predictions),
        "total_matches": len([m for m in matches if m["rank"] > 0]),
        "rank_distribution": calculate_rank_distribution(matches)
    }
    
    # 4. 슬랙 메시지 생성 및 전송
    message = f"""
🎯 **{latest_draw['draw_number']}회차 당첨 결과 요약**

📊 **전체 통계**
• 총 예측 수: {stats['total_predictions']}개
• 당첨 예측 수: {stats['total_matches']}개
• 당첨률: {stats['total_matches']/stats['total_predictions']*100:.1f}%

🏆 **등수별 분포**
{format_rank_distribution(stats['rank_distribution'])}

🎲 <{JINLOTTO_URL}|다음 회차 번호 받으러 가기>
    """
    
    send_to_slack(message)
```

### 디버그 도구

#### SEO 디버그 도구들
- `tools/sitemap_debug.py`: 사이트맵 접근성 테스트
- `tools/rss_debug.py`: RSS 피드 유효성 검사
- `tools/robots_debug.py`: robots.txt 크롤링 규칙 확인
- `tools/gsc_test.py`: Google Search Console 연동 테스트

---

## 📈 최근 주요 변경사항 (2025.09.22 기준)

### 1. 월요일 9시 통합 자동화 구현 (2025.09.22) 🔥
**변경사항**:
- **통합 스크립트**: `tools/monday_automation.py` 새로 생성
- **스케줄 통합**: 기존 08:00 + 10:00 → 09:00 KST 단일 실행
- **MZ 스타일 알림**: "🔥 로또 업뎃 떴다!!" 메시지로 변경
- **render.yaml**: `lotto-monday-automation` 크론 작업으로 통합

**구현 세부사항**:
```python
# tools/monday_automation.py - MZ 스타일 메시지
message = f"""🔥 로또 업뎃 떴다!! ({kst_time})

✨ {draw_number}회차 ({draw_date}) 결과 공개~
🎯 이번주 당첨번호: [{numbers_str}] + 보너스 {bonus}

🎊 당첨자 현황:
   🥇 1등: ?명 | 🥈 2등: ?명 | 🥉 3등: ?명 | 4등: ?명 | 5등: ?명"""
```

### 2. 프로젝트 정리 및 최적화 (2025.09.22) 🧹
**정리된 항목**:
- **불필요한 파일 삭제**: 임시 파일, 캐시 폴더, 가상환경 제거
- **파일 구조 정리**: 현재 구조에 맞게 문서 업데이트
- **배포 최적화**: 정리된 구조로 배포 속도 향상

### 3. 닉네임 기능 추가 (2025.09.18-19) 🆕
**변경사항**:
- **DB 스키마**: `predictions` 테이블에 `nickname VARCHAR(50)` 컬럼 추가
- **API**: `PredictionRequest`에 `nickname` 필드 추가
- **프론트엔드**: 스트레칭 완료 후 닉네임 입력 모달 추가
- **사용자 플로우**: 스트레칭 → 닉네임 입력 → 번호 확인

**구현 세부사항**:
```python
# backend/app/models/lotto_models.py
class PredictionRequest(BaseModel):
    method: str = "statistical"
    num_sets: int = 5
    include_bonus: bool = False
    nickname: Optional[str] = None  # 닉네임 추가

# backend/app/routes/api.py
nickname = getattr(request, 'nickname', None)
if nickname and len(nickname.strip()) > 50:
    nickname = nickname.strip()[:50]  # 최대 50자 제한

pred = dbm.Prediction(
    user_key=user_key,
    generated_for=gen_for,
    set_index=idx + 1,
    numbers=[int(x) for x in nums],
    source=fixed.get('mode', 'daily-fixed'),
    nickname=nickname,  # 닉네임 저장
)
```

### 4. 메인 비디오 자동재생 개선 (2025.09.19) 🎥
**문제**: 브라우저 자동재생 정책으로 메인 비디오 재생 안됨
**해결**:
- `controls` 속성 추가로 사용자 수동 재생 가능
- JavaScript 자동재생 시도 + 사용자 클릭 폴백
- 브라우저 호환성을 위한 `<p>` 태그 폴백 추가

```html
<!-- frontend/index.html -->
<video class="ad-video" autoplay muted loop playsinline preload="auto" controls>
    <source src="/static/Main_KR_Home.mp4" type="video/mp4" />
    <p>브라우저가 비디오를 지원하지 않습니다. <a href="/static/Main_KR_Home.mp4">비디오 다운로드</a></p>
</video>
```

### 5. 배포 파이프라인 최적화 (2025.09.19) 🚀
**문제**: `render.yaml`의 `buildCommand`가 구버전 파일로 덮어씀
**해결**: Python `shutil.copy2()` 사용으로 크로스 플랫폼 호환성 확보

```yaml
# render.yaml (이전)
buildCommand: |
  pip install -r requirements.txt
  cp frontend/index.html backend/static/index.html  # ❌ 호환성 이슈

# render.yaml (현재)
buildCommand: |
pip install -r requirements.txt
  python -c "
  import shutil
  shutil.copy2('frontend/index.html', 'backend/static/index.html')
  shutil.copy2('frontend/script.js', 'backend/static/script.js')  
  shutil.copy2('frontend/styles.css', 'backend/static/styles.css')
  print('✅ Frontend files copied to backend/static/')
  "
```

### 6. 슬랙 웹훅 보안 강화 (2025.09.18) 🔒
**문제**: 하드코딩된 웹훅 URL이 GitHub에 노출되어 Slack에서 무효화
**해결**: 모든 웹훅 URL을 환경변수로 이동

```python
# tools/stretching_reminder.py (이전)
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."  # ❌ 하드코딩

# tools/stretching_reminder.py (현재)
SLACK_WEBHOOK_URL = os.getenv("STRETCHING_SLACK_WEBHOOK_URL")  # ✅ 환경변수
```

```yaml
# render.yaml
envVars:
  - key: STRETCHING_SLACK_WEBHOOK_URL
    sync: false  # Render Dashboard에서 관리
```

### 7. 스트레칭 알림봇 구현 (2025.09.18) 💪
**기능**: 매시간 50분 MZ 감성 스트레칭 알림
**시간**: 10:50, 11:50, 12:50, 14:50, 15:50, 16:50 KST
**메시지**: 랜덤 MZ 스타일 메시지 + 서비스 링크

### 8. SEO 최적화 완료 (2025.08.27) 📊
**해결된 문제**:
- Google Search Console 사이트맵/RSS 크롤링 오류
- `robots.txt`: `Disallow: /` → `Allow: /`로 변경
- RSS 피드: `pubDate` 1970년 오류 → 현재 날짜로 수정
- 메타 태그: 구조화 데이터 및 소셜 미디어 태그 추가

**문제**: UTC/KST 혼재로 인한 데이터 불일치
**해결**: 모든 시간을 KST 기준으로 통일
**적용**: `kst_now()` 함수로 timezone-naive datetime 저장

---

## 🚨 운영 런북

### 메모리 초과/OOM 대응 🔥
**증상**: Render 로그에서 워커 재시작, "Memory limit exceeded"
**즉시 조치**:
1. **ML 비활성화**: `ENABLE_ML=false` 설정 → 재배포
2. **워커 수 감소**: `workers=1`로 줄여서 메모리 사용량 감소
3. **모델 워밍업 비활성화**: `WARMUP_ON_STARTUP=false` 유지

**장기 해결**:
- Render 플랜 업그레이드 (Free → Starter $7/월)
- 모델 경량화 (`models/*_tuned.pkl` 제거)
- 모델 로딩 최적화 (mmap_mode 활용)

### 502/타임아웃 오류 대응 ⏱️
**증상**: "502 Bad Gateway", "Worker timed out"
**진단 단계**:
1. **로그 확인**: Render Dashboard → Logs에서 Gunicorn 로그 확인
2. **ML 분리 테스트**: `ENABLE_ML=false`로 설정하여 ML 연산 영향 확인
3. **타임아웃 조정**: `render.yaml`에서 `timeout` 값 증가 (현재 300초)

**근본 해결**:
- 백그라운드 큐 최적화
- 모델 로딩 시간 단축
- 응답 시간 모니터링 강화

### 슬랙 알림 실패 대응 📢
**증상**: 스트레칭 알림 또는 주간 요약 미전송
**확인 단계**:
1. **웹훅 URL 확인**: Render 환경변수에서 올바른 URL 설정 여부
2. **웹훅 유효성**: Slack 워크스페이스에서 웹훅 상태 확인
3. **로그 확인**: 크론 작업 로그에서 오류 메시지 확인

**해결 방법**:
```bash
# 새 웹훅 생성 후 환경변수 업데이트
# Render Dashboard → Environment → Add Environment Variable
STRETCHING_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/NEW_WEBHOOK_URL
```

### 배포 실패 대응 🚀
**증상**: "Build failed", "Deploy failed"
**진단 단계**:
1. **빌드 로그 확인**: Render Dashboard에서 빌드 실패 원인 파악
2. **의존성 문제**: `requirements.txt` 버전 충돌 확인
3. **파일 복사 실패**: `buildCommand`의 Python 스크립트 오류 확인

**해결 방법**:
```bash
# 로컬에서 빌드 테스트
python -c "
import shutil
shutil.copy2('frontend/index.html', 'backend/static/index.html')
print('✅ Build test successful')
"

# 수동 재배포
# Render Dashboard → Manual Deploy
```

### 데이터베이스 연결 오류 🗄️
**증상**: "Connection refused", "Authentication failed"
**확인 단계**:
1. **Supabase 상태**: Supabase Dashboard에서 프로젝트 상태 확인
2. **연결 문자열**: `SUPABASE_URL`, `SUPABASE_ANON_KEY` 환경변수 확인
3. **RLS 정책**: 테이블 접근 권한 확인

**해결 방법**:
```sql
-- RLS 정책 확인
SELECT * FROM pg_policies WHERE tablename IN ('users', 'predictions', 'draws', 'matches');

-- 임시 접근 허용 (디버깅용)
DROP POLICY IF EXISTS "Temporary allow all" ON predictions;
CREATE POLICY "Temporary allow all" ON predictions FOR ALL TO public USING (true);
```

---

## ✅ 인수인계 체크리스트

### 🔥 즉시 수행 (우선순위 1)
- [ ] **Slack 웹훅 보안 확인**: GitHub 히스토리에 노출된 웹훅 URL 없는지 확인
- [ ] **환경변수 설정**: Render Dashboard에서 모든 시크릿 환경변수 설정 확인
  - [ ] `SUPABASE_URL`, `SUPABASE_ANON_KEY`
  - [ ] `SLACK_WEBHOOK_URL`, `STRETCHING_SLACK_WEBHOOK_URL`
  - [ ] `MONITOR_BASE_URL`
- [ ] **Supabase RLS**: 모든 테이블에 적절한 RLS 정책 적용
- [ ] **배포 상태 확인**: https://stretchinglotto.motiphysio.com/ 정상 작동 확인
- [ ] **닉네임 기능 확인**: 스트레칭 → 닉네임 입력 → 번호 확인 플로우 테스트

### 📊 24시간 모니터링 (우선순위 2)
- [ ] **메모리 사용량**: Render 로그에서 OOM 발생 빈도 확인
- [ ] **응답 시간**: `/api/predict` 평균 응답 시간 10초 이하 유지
- [ ] **크론 작업**: 모든 자동화 작업 정상 실행 확인
  - [ ] 스트레칭 알림 (매시간 50분)
  - [ ] 주간 요약 (월요일 10시)
  - [ ] 헬스 모니터링 (5분마다)
- [ ] **슬랙 알림**: 스트레칭 알림 및 주간 요약 정상 전송 확인

### 🛠️ 개발 환경 (우선순위 3)
- [ ] **로컬 환경**: 가상환경 설정 및 로컬 서버 실행 테스트
- [ ] **API 테스트**: 주요 엔드포인트 정상 작동 확인
  - [ ] `POST /api/predict` (닉네임 포함)
  - [ ] `GET /api/health`
  - [ ] `POST /api/data/update`
- [ ] **모델 학습**: ML 모델 재학습 프로세스 숙지
- [ ] **프론트엔드 빌드**: 프론트엔드 변경사항 배포 프로세스 확인

### 📚 문서화 (우선순위 4)
- [ ] **API 문서**: `docs/API_SPEC.md` 최신 상태 유지
- [ ] **데이터 스키마**: `docs/DATA_SCHEMA.md` 업데이트 (닉네임 필드 포함)
- [ ] **배포 가이드**: `docs/DEPLOY_RUNBOOK.md` 검토
- [ ] **테스트 케이스**: 주요 기능별 테스트 시나리오 작성

### 🔮 향후 개선 (우선순위 5)
- [ ] **모델 성능**: ML 모델 정확도 개선 방안 검토
- [ ] **사용자 경험**: 프론트엔드 UX/UI 개선사항 정리
- [ ] **확장성**: 사용자 증가 대비 인프라 확장 계획
- [ ] **보안 강화**: 추가 보안 조치 (rate limiting, input validation 등)
- [ ] **닉네임 활용**: 닉네임 기반 개인화 기능 확장

---

## 🚀 자주 사용하는 명령어

### 로컬 개발
```bash
# 서버 실행
python main.py

# 프론트엔드 빌드
python scripts/build_frontend.py

# 모델 학습
python scripts/train_classifiers.py

# API 테스트
python backend/test_api.py

# 의존성 설치
pip install -r requirements.txt
```

### 데이터 관리
```bash
# 최신 로또 데이터 수집
curl -X POST http://localhost:8000/api/data/update

# DB 동기화
curl -X POST http://localhost:8000/api/data/sync-db

# 수동 매칭 실행
python tools/accurate_weekly_match.py

# 예측 테스트 (닉네임 포함)
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"method":"statistical","num_sets":1,"nickname":"테스트"}'
```

### 배포 및 모니터링
```bash
# Git 배포
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main

# SEO 상태 확인
python tools/seo_monitor.py

# 헬스 체크
curl https://stretchinglotto.motiphysio.com/api/health

# 스트레칭 알림 테스트
python tools/stretching_reminder.py
```

### 디버깅
```bash
# 환경변수 확인
echo $STRETCHING_SLACK_WEBHOOK_URL

# 모델 성능 평가
python scripts/evaluate_models.py

# 프론트엔드 파일 수동 복사
python -c "
import shutil
shutil.copy2('frontend/index.html', 'backend/static/index.html')
shutil.copy2('frontend/script.js', 'backend/static/script.js')
shutil.copy2('frontend/styles.css', 'backend/static/styles.css')
print('✅ Files copied')
"
```

---

## 📞 긴급 연락처 및 권한

### 시스템 권한
- **GitHub**: `main` 브랜치 push 권한 필요
- **Render**: 프로젝트 소유자 또는 collaborator 권한
- **Supabase**: 프로젝트 관리자 권한
- **Slack**: 워크스페이스 관리자 (웹훅 관리용)

### 외부 서비스
- **동행복권 API**: 공개 API (별도 인증 불필요)
- **YouTube API**: 프론트엔드에서 직접 사용 (iframe API)
- **Google Search Console**: SEO 모니터링용

### 중요 URL
- **메인 서비스**: https://stretchinglotto.motiphysio.com/
- **서브 서비스**: http://43.201.75.105:8000
- **Render Dashboard**: https://dashboard.render.com
- **Supabase Dashboard**: https://supabase.com/dashboard
- **GitHub Repository**: https://github.com/jjin3633/jinlotto

---

## 🔄 버전 관리

**현재 버전**: v2.2.0 (2025.09.22)
- 🔥 월요일 9시 통합 자동화 구현 (MZ 스타일 알림)
- 🧹 프로젝트 정리 및 최적화 (불필요한 파일 제거)
- ✨ 닉네임 기능 추가 (사용자 플로우 개선)
- 🎥 메인 비디오 자동재생 개선 (브라우저 호환성)
- 🚀 배포 파이프라인 최적화 (Python 빌드 스크립트)
- 🔒 슬랙 웹훅 보안 강화 (환경변수 관리)

**이전 주요 버전**:
- v2.0.0 (2025.08.27): SEO 최적화 완료, Google Search Console 연동
- v1.5.0 (2025.08.25): 타임존 통일 및 스트레칭 알림봇 구현
- v1.0.0 (2025.08.01): 초기 서비스 런칭

---

## 🎯 마무리

이 문서는 **스트레칭 로또** 프로젝트의 모든 측면을 포괄하는 **살아있는 문서**입니다. 

### 📝 문서 업데이트 가이드
시스템 변경사항이 있을 때마다 다음 섹션들을 업데이트해주세요:
- **서비스 개요**: 새로운 기능이나 플로우 변경 시
- **프로젝트 구조**: 새 파일이나 디렉토리 추가 시
- **API 엔드포인트**: 새 엔드포인트나 요청/응답 스키마 변경 시
- **데이터베이스 스키마**: 테이블이나 컬럼 변경 시
- **최근 주요 변경사항**: 모든 중요한 변경사항 기록
- **운영 런북**: 새로운 문제나 해결책 발견 시

### 🤝 기여 가이드
새로운 개발자가 프로젝트에 기여할 때:
1. 이 문서를 먼저 읽고 전체 구조 파악
2. 로컬 환경 설정 후 기본 기능 테스트
3. 변경사항 구현 후 관련 문서 섹션 업데이트
4. 테스트 완료 후 배포 및 모니터링

### 💡 추가 질문이나 지원이 필요한 경우
- **기술적 문제**: 이 문서의 운영 런북 섹션 참조
- **새로운 기능**: API 엔드포인트 및 프론트엔드 구조 섹션 참조
- **배포 이슈**: 배포 및 운영 섹션의 트러블슈팅 가이드 참조

**이 프로젝트가 사용자들에게 건강한 습관과 함께 행운을 가져다주길 바랍니다!** 🍀✨

---

*마지막 업데이트: 2025.09.22 - 월요일 9시 통합 자동화 및 프로젝트 정리 완료*
