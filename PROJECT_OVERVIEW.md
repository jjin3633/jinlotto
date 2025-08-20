# JinLotto 프로젝트 요약 (한 문서로 전체 이해)

이 문서는 새 대화를 시작할 때 매번 프롬프트로 설명할 필요 없이, **이 저장소(번호추첨)** 의 구조·동작·운영 포인트를 빠르게 파악하도록 만든 단일 참조 문서입니다. 로컬 개발자, 운영자, 또는 자동화 도구가 한 번 읽으면 전체를 이해할 수 있게 핵심만 정리했습니다.

---

## 1) 프로젝트 개요
- 목적: 대한민국 로또(6/45) 과거 데이터 기반으로 통계·머신러닝 혼합 예측을 제공하는 웹 서비스
- 스택: FastAPI(Python) 백엔드, 정적 프론트엔드(HTML/CSS/JS), scikit-learn 모델, Render 배포

## 2) 주요 경로(중요 파일)
- 루트
  - `main.py` : 애플리케이션 진입점(uvicorn/gunicorn 실행 대상)
  - `Procfile`, `render.yaml` : 배포/Start 명령(현재 gunicorn --timeout 300, workers 2)
- 백엔드
  - `backend/app/routes/api.py` : REST API 라우트(예: `/api/predict`, `/api/data/*`, `/api/health`)
  - `backend/app/services/data_service.py` : 데이터 로드/수집/전처리
  - `backend/app/services/prediction_service.py` : 예측 엔진(통계, ML, 통합 로직 — 핵심 변경점: predict_proba 안전화, 모델 캐시, 백그라운드 큐)
  - `backend/app/db/` : DB 모델 및 세션
- 스크립트/모델
  - `scripts/train_classifiers.py`, `scripts/tune_classifiers.py`, `scripts/train_sequential_models.py` : 모델 학습/튜닝 스크립트
  - `scripts/show_proba_shap.py` : 포지션별 predict_proba 및 SHAP 요약 출력용 디버그 스크립트
  - `models/` : 학습된 모델 파일(대형 바이너리, 일부는 Git에서 언트랙 처리됨)
- 프론트엔드
  - `frontend/index.html`, `frontend/styles.css`, `frontend/script.js` : UI 및 정적 자원(빌드 시 `scripts/build_frontend.py`가 `backend/static/`로 복사)
- 모니터링(추가)
  - `.monitoring/monitor.py` : Render + Slack 연동 모니터 스크립트
  - `.monitoring/sample_once.py` : 한 번 샘플 체크

## 3) 로컬 실행(개발자용 빠른 가이드)
1. 가상환경
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
```
2. 의존성
```bash
pip install -r requirements.txt
```
3. 프론트 빌드(정적 파일 복사)
```bash
python scripts/build_frontend.py
```
4. 서버 실행(개발)
```bash
python main.py   # 내부적으로 uvicorn.run 사용
```
5. 엔드포인트 테스트
```bash
POST http://localhost:8000/api/predict  {"num_sets":3}
GET  http://localhost:8000/api/health
```

## 4) 배포·운영 핵심 환경변수
- `ENABLE_ML` (true/false): ML 경로 사용 여부(운영 장애 시 false로 전환 가능)
- `WARMUP_ON_STARTUP` (true/false): 시작 시 모델 워밍업 수행 여부
- `CONF_*`, `HOT_TOP_K` 등: 예측 가중치/파라미터
- `SLACK_WEBHOOK_URL`: 모니터 알람용
- `COOKIE_SECURE`: 쿠키 보안 옵션

## 5) 예측 플로우 요약
1. `/api/predict` 호출 → `PredictionService.get_daily_fixed_predictions`
2. 로컬에 동일 날짜·사용자 키로 고정 결과 파일(`backend/data/daily_recommendations/{date}/{user_key}.json`) 존재하면 반환
3. 없으면 통계 기반 빠른 응답을 먼저 반환하고(백그라운드에 ML refine job 큐잉), 백그라운드 작업이 끝나면 store_path에 덮어써 다음 호출부터 ML 결과 사용
4. ML 경로는 position별 분류기(`models/position_{i}_clf.pkl`)의 `predict_proba`를 사용해서 후보 샘플링

## 6) 최근 수정·핵심 안정화 작업(요약)
- predict_proba 호출 전에 feature 정리(비숫자 제거 및 float 변환)로 dtype 충돌 방지
- 모델 로딩 시 날짜별 캐시 도입으로 매요청 디스크 I/O 감소
- `joblib.load(..., mmap_mode='r')` 시도하여 메모리 피크 완화
- ML 연산을 백그라운드 큐로 비동기화(요청 경로의 메모리·시간 부담 최소화)
- Git: 큰 모델 파일 일부 언트랙 처리 및 `.gitignore` 반영
- 배포: Gunicorn timeout ↑(120→300)

## 7) 문제 발생 시 우선 점검 체크리스트
1. Render 로그: OOM/worker restart/traceback 시간 확인
2. `/api/health` 상태(200) 확인
3. `/api/predict` 응답 시간/상태(200/5xx) 확인 — 로컬 테스트로 재현
4. 환경변수: `ENABLE_ML=false`로 임시 전환하여 ML이 원인인지 분리
5. 모니터: `.monitoring/samples.jsonl` 및 Slack 알림 기록 확인

## 8) 운영 권장(우선순위)
1. 단기: 현재 백그라운드 큐 + mmap + timeout 변경으로 안정화 관찰(24시간 모니터링 권장)
2. 중기: 모델 경량화, ML을 비동기 작업으로 완전 분리, 모델을 외부 스토리지(S3)로 이동
3. 장기: Git LFS 도입 또는 대형 데이터 아티팩트 아카이빙, 자동 알람(메모리/5xx) 설정

## 9) 자주 쓰는 명령 모음
- 프론트 빌드: `python scripts/build_frontend.py`
- 모델 학습(예): `python scripts/train_classifiers.py`
- SHAP/확률 디버그: `python scripts/show_proba_shap.py`
- 모니터링 1회: `python .monitoring/sample_once.py` (환경변수 `SLACK_WEBHOOK_URL` 설정)

---
부가: 이 문서를 `PROJECT_OVERVIEW.md`로 프로젝트 루트에 추가했습니다. 새 채팅을 열 때 이 파일을 읽도록 전달하면 프로젝트 전체를 바로 이해할 수 있습니다.


