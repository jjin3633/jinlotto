from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from contextlib import asynccontextmanager

from app.routes.api import router as api_router
from app.routes.static import router as static_router

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(api_router, prefix="/api")
app.include_router(static_router)

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
