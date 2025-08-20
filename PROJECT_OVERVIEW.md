# JinLotto — 운영/인수인계용 종합 문서

이 문서는 이 프로젝트 전체(코드, 배포, ML 파이프라인, 운영 절차, 최근 변경사항, 보안 이슈 등)를 **한 번에 파악**하고 곧바로 업무 인수인계할 수 있도록 실무 중심으로 정리한 문서입니다. 신규 담당자가 이 파일만 읽어도 시스템을 운영·디버깅·배포·확장할 수 있도록 최대한 자세히 작성했습니다.

> 주의: 이 문서에는 실제 비밀 값(키/웹훅 등)을 포함하지 않습니다. 시크릿은 Render 환경변수나 GitHub Secrets 등 시크릿 스토어에 보관하세요.

---

목차
- 요약 (1페이지) — 즉시 인수인계에 필요한 핵심 포인트
- 레포 구조 및 핵심 파일 설명
- 로컬 개발/테스트 가이드(명령어, 체크리스트)
- 배포·운영 설정 (Render 기준)
- API 엔드포인트 상세(예/에러/주의사항)
- 예측 파이프라인(통계·ML·통합 흐름과 파일 경로)
- ML 모델 스펙(입력/출력/학습/배포 정책)
- 최근 변경 이력 및 이유(우리가 수행한 작업 요약)
- 운영 런북(문제 발생시 조치: OOM, 502, worker crash 등)
- 보안·민감값 처리 지침(즉시 실행 항목 포함)
- 모니터링·알림 구성(24시간 모니터링 요약 포함)
- 인수인계 체크리스트(우선순위 작업 목록)
- 자주 쓰는 명령 모음

---

요약(1페이지)
- 서비스: JinLotto (로또 번호 추천)
- 엔진: FastAPI + scikit-learn 기반 ML(포지션별 분류기) + 통계 혼합
- 배포: Render (autodeploy from GitHub)
- 핵심 운영 포인트:
  1. `/api/predict`는 사용자가 하루 1회 고정으로 번호를 받는 엔드포인트입니다. 첫 호출 시 통계적 빠른 응답을 반환하고, 서버는 백그라운드에서 ML 정제 작업을 수행해 파일로 저장합니다.
  2. ML 모델은 대형 바이너리로 메모리 사용이 큽니다. 현재 메모리 관련 완화 조치를 적용했고(모델 캐시, joblib mmap, 백그라운드 큐), 배포 타임아웃을 확장했습니다.
  3. 보안: API 키/웹훅은 절대 Git에 커밋하지 않음. 만약 노출되면 즉시 폐기(rotate)해야 함.

레포 구조(핵심)
- `main.py` — 앱 진입점
- `Procfile`, `render.yaml` — 배포 스크립트 (Start 명령, env 설정)
- `backend/app/routes/api.py` — REST API 엔드포인트 정의
- `backend/app/services/data_service.py` — 데이터 수집/전처리
- `backend/app/services/prediction_service.py` — 예측 로직(통계, ML, unified) — 핵심 로직 수정 지점
- `backend/app/utils/slack_notifier.py` — Slack 알림 헬퍼
- `backend/db/` — DB 모델·세션
- `backend/data/` — 로컬 CSV 데이터(운영에서는 DB 사용)
- `scripts/` — 학습·튜닝·평가·디버그 스크립트
- `models/` — 학습된 모델(로컬 저장, 원격 저장소에는 일부만 보관)
- `.monitoring/` — 로컬 모니터 스크립트(민감값 주의)
- `docs/` — 상세 문서(현재 원격에서 언트랙됨; 로컬 보관 권장)

로컬 개발·테스트(핵심 명령)
1. 가상환경
```
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
```
2. 의존성
```
pip install -r requirements.txt
```
3. 프론트 빌드
```
python scripts/build_frontend.py
```
4. 서버 실행
```
python main.py
```
5. 엔드포인트 테스트
```
POST http://localhost:8000/api/predict  {"num_sets":3}
GET  http://localhost:8000/api/health
```

배포/운영(주요)
- Start command (Render):
  `gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 300`
- 중요 환경변수:
  - `ENABLE_ML` (true/false): ML 경로 스위치
  - `WARMUP_ON_STARTUP` (true/false): 서비스 시작 시 모델 워밍업
  - `SLACK_WEBHOOK_URL`: Slack 알림(시크릿)
  - `DATABASE_URL` 등 DB 연결 문자열(시크릿)
- Health check: `/api/health`

API 엔드포인트 상세(핵심)
- `POST /api/predict`:
  - 요청: `{"num_sets": <int>}`
  - 동작:
    1. user cookie(`jl_uid`)로 user_key 생성/식별
    2. `PredictionService.get_daily_fixed_predictions` 호출
    3. 기존 저장 파일이 있으면 반환
    4. 없으면 통계적 빠른 응답을 반환하고 ML 정제 작업을 백그라운드로 큐잉
  - 응답 예: `sets`(list of sets), `confidence_scores`, `analysis_summary`
  - 주의: 응답 `reasoning`은 UI에 노출되지 않도록 빈 배열로 반환함(설정 가능)
- `GET /api/health`:
  - 가볍게 서비스 상태 반환(항상 빠르게 응답)
- 데이터 관리: `/api/data/collect`, `/api/data/update`, `/api/data/sync-db`

예측 파이프라인(구체)
1. 데이터 로드(`backend/data/lotto_data.csv` 또는 DB)
2. `_create_features`: 위치별 이동평균(`_ma5`, `_ma10`), `freq_1..freq_45`, `odd_count`
3. 모델 로드: `models/position_{i}_clf.pkl`(날짜별 캐시)
4. `predict_proba`로 포지션별 확률 벡터 생성
5. 샘플링 전략: 각 포지션 상위 K(기본 8) 후보에서 확률 기반 샘플링
6. 다양성 제약 적용(홀짝/구간/연속 제한)
7. confidence 계산: consensus 비율 + hot-number 비율 + 엔트로피 기반 가중

ML 모델 스펙
- 타입: RandomForestClassifier (position별)
- 입/출력:
  - 입력: `_create_features`의 파생 피처(수치형)
  - 출력: 클래스(1..45), `predict_proba`
- 학습/튜닝 스크립트: `scripts/train_classifiers.py`, `scripts/tune_classifiers.py`
- 평가: `scripts/evaluate_models.py` (TimeSeriesSplit 사용 권장)
- 저장: `models/position_{i}_clf.pkl` (대형 바이너리 — 저장 정책 필요)

최근 변경 및 이유(핵심)
- predict_proba 입력 전처리 추가: dtype 충돌(특히 DateTime)으로 예측 실패/예외 발생을 방지
- 모델 로드 캐시(날짜별): 매요청 디스크 로드로 인한 지연/메모리 스파이크 완화
- joblib mmap_mode 적용 시도: 로딩 시 메모리 피크 완화 목적
- ML 백그라운드 큐 도입: 첫 요청의 빠른 응답 보장 및 ML 연산으로 인한 대기 제거
- 리포지토리: 대형 모델 파일 일부 언트랙 처리(원격 용량 감소)
- 배포 설정: Gunicorn timeout 120→300으로 확장(ML 작업 고려)

운영 런북(긴급 대응 요약)
- 메모리 초과/OOM:
  1. Render 로그 확인(시간대/워커 재시작)
  2. 임시: `ENABLE_ML=false` 설정 → 재배포(ML 비활성화)
  3. 임시(대체): workers 수를 1로 낮춤
  4. 장기: 인스턴스 메모리 업그레이드 또는 모델 경량화
- 502/타임아웃:
  1. Gunicorn 로그/Traceback 확인
  2. ML 연산으로 인한 지연인지 확인(임시 `ENABLE_ML=false`로 분리)
- 워커 crash:
  1. 로그에서 `Worker timed out` 메시지 확인
  2. timeout 증분(현재 300s) 또는 모델 로드 최적화

보안·민감값 처리 지침(즉시 수행 항목)
- 절대 커밋 금지: API 키, Slack webhook URL, DB 비밀번호, Render API Key
- 즉시 수행: 만약 키/웹훅을 노출했다면 해당 키를 즉시 폐기(rotate)하고 새 키를 시크릿 스토어에 등록
- 레포 정리: 과거 커밋에 노출된 민감값이 있다면 `git filter-repo` 또는 BFG로 히스토리를 정리
- 자동화: `pre-commit` + `detect-secrets` 설치 권장

모니터링·알림
- 단발: `.monitoring/sample_once.py`로 health/predict 한 번 체크(환경변수 `SLACK_WEBHOOK_URL` 필요)
- 자동: `.monitoring/monitor.py`는 주기적으로 health/predict 체크 및 Slack 알림 전송(환경변수 필요)
- 권장 알람 임계값: 메모리 80%, predict 평균 응답 > 10s, 연속 502(3회 이상)

인수인계 체크리스트 (우선순위)
1. Render/Slack 키(노출 여부) 확인 및 rotate(즉시)
2. 24시간 모니터링 결과 확인(메모리/502/재시작 횟수)
3. 모델 파일 관리 정책 결정(로컬 보관 vs Git LFS vs S3)
4. CI에 `detect-secrets` 추가
5. 운영 문서(ERD, 피처 리스트, 테스트 케이스) 추가 작성

자주 쓰는 명령
- 프론트 빌드: `python scripts/build_frontend.py`
- 모델 학습: `python scripts/train_classifiers.py`
- 단일 샘플 체크: `python .monitoring/sample_once.py`
- 서버(개발): `python main.py`

긴급 연락/권한
- 코드·배포 권한: GitHub `main` 브랜치 push 권한자
- 배포/환경변수: Render 계정 소유자
- Slack webhook 관리 권한: Slack 워크스페이스 관리자

---

이 문서는 더 세부적인 항목(ERD, 각 모델의 피처 리스트, 테스트 커버리지, 학습 로그)으로 확장 가능합니다. 우선순위를 알려주시면 차례로 문서를 추가하겠습니다.


