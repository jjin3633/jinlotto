# API 스펙

이 문서는 서비스에서 제공하는 주요 API 엔드포인트의 요청/응답 스펙을 정리합니다.

## 공통
- 모든 엔드포인트는 `/api` 프리픽스를 가집니다(앱 레벨 라우터 설정).
- 응답 포맷: `APIResponse` 래퍼 (성공 여부/메시지/데이터 포함)

## POST /api/predict
- 목적: 사용자별 하루 고정 추천 번호 반환
- 요청(JSON):
```json
{
  "num_sets": 3
}
```
- 응답(200):
```json
{
  "success": true,
  "message": "오늘의 고정 추천을 반환했습니다.",
  "data": {
    "mode": "daily-fixed",
    "generated_for": "20250819",
    "valid_until": "2025-08-20T00:00:00+09:00",
    "created_at": "2025-08-19T16:35:24.981614+09:00",
    "user_key": "<uuid>",
    "sets": [[3,6,14,19,26,31],[3,10,12,15,28,42],[1,5,6,10,21,34]],
    "confidence_scores": [0.533,0.467,0.483],
    "reasoning": [],
    "analysis_summary": "오늘(20250819)의 고정 추천 세트"
  }
}
```
- 오류: 500 반환 시 `message` 에러 문자열 포함

## GET /api/health
- 목적: 서비스 상태 (경량 헬스체크)
- 응답(200): `{ "status": "healthy", "message": "로또 분석 서비스가 정상 작동 중입니다." }`

## 데이터 관련
- `POST /api/data/collect` : 외부 API에서 회차 데이터를 수집해 CSV로 저장
- `POST /api/data/update` : 최신 회차만 갱신
- `POST /api/data/sync-db` : CSV → DB 업서트

## 디버그/관리
- `GET /api/debug/db-stats` : DB 테이블 카운트 (운영 시 비활성 권장)

---
참고: 위 스펙은 라우트 구현(`backend/app/routes/api.py`)에 근거합니다. API 변경 시 해당 파일과 동기화하세요.


