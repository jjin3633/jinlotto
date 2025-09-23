from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import uvicorn
from contextlib import asynccontextmanager
import os
from backend.app.routes.api import router as api_router
from backend.app.routes.static import router as static_router
from backend.app.db.session import engine
from backend.app.db.models import Base
from backend.app.routes import api as api_module

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("로또 분석 서비스가 시작되었습니다.")
    # DB 테이블 생성(마이그레이션 도구 없을 때 초기가동)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"DB 초기화 실패: {e}")
    # ML 워밍업을 비활성화하여 배포 시간 단축 (필요시 첫 요청에서 지연 처리)
    try:
        do_warmup = os.getenv("WARMUP_ON_STARTUP", "false").strip().lower() in ("1","true","yes","y","on")
    except Exception:
        do_warmup = False
    if do_warmup:
        try:
            ds = api_module.data_service
            ps = api_module.prediction_service
            df = ds.load_data()
            ps.warmup_today_models(df)
            logger.info("ML 워밍업 완료")
        except Exception as e:
            logger.error(f"ML 워밍업 실패(무시 가능): {e}")
    else:
        logger.info("ML 워밍업 스킵 - 첫 요청 시 지연 발생 가능")
    yield
    # 종료 시 실행
    logger.info("로또 분석 서비스가 종료되었습니다.")

# FastAPI 앱 생성
app = FastAPI(
    title="로또 번호 분석 API",
    description="대한민국 로또(6/45) 데이터 분석 및 번호 추천 서비스",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
def _get_allowed_origins() -> list:
    raw = os.getenv("ALLOWED_ORIGINS")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    # 기본: 프로덕션 도메인 및 로컬 개발 허용
    return [
        "http://stretchinglotto.motiphysio.com/",
        "https://stretchinglotto.motiphysio.com/",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://43.201.75.105:8000",
        "https://43.201.75.105:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS 강제 리다이렉트 (프록시 뒤 HTTPS 환경에서도 안전)
# 개발 환경에서는 기본적으로 비활성화
if os.getenv("ENABLE_HTTPS_REDIRECT", "false").lower() in ("1", "true", "yes", "on"):
    app.add_middleware(HTTPSRedirectMiddleware)

# 신뢰 호스트 제한
def _get_allowed_hosts() -> list:
    raw = os.getenv("ALLOWED_HOSTS")
    if raw:
        return [h.strip() for h in raw.split(",") if h.strip()]
    return [
        "stretchinglotto.motiphysio.com",
        "www.stretchinglotto.motiphysio.com",
        "localhost",
        "127.0.0.1",
        "43.201.75.105"
    ]

app.add_middleware(TrustedHostMiddleware, allowed_hosts=_get_allowed_hosts())


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # 기본 보안 헤더 적용
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # CSP는 보수적으로 적용(유튜브 임베드 허용 필요 시 별도 설정 권장)
        # response.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; img-src 'self' data: https://i.ytimg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self' https://www.youtube.com https://s.ytimg.com https://cdnjs.cloudflare.com")
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 라우터 등록 (정적 라우터는 마지막에 등록해야 API 경로를 가로채지 않음)
app.include_router(api_router, prefix="/api")

@app.get("/api")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "로또 번호 분석 API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/health",
            "data_summary": "/api/data/summary",
            "analysis": "/api/analysis/comprehensive",
            "prediction": "/api/predict",
            "visualization": "/api/visualization/frequency-chart",
            "disclaimer": "/api/disclaimer"
        }
    }

# 정적 라우터는 모든 경로를 포괄하므로 반드시 마지막에 등록
app.include_router(static_router)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"예상치 못한 오류 발생: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "서버 내부 오류가 발생했습니다.",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
