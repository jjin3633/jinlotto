from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter()

# 정적 파일 디렉토리 설정
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")

# 정적 파일 경로만 계산(마운트는 애플리케이션 레벨에서 수행)

@router.get("/")
async def serve_frontend():
    """프론트엔드 메인 페이지 서빙"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Frontend files not found. Please build the frontend."}

@router.get("/{path:path}")
async def serve_static_files(path: str):
    """정적 파일 서빙"""
    file_path = os.path.join(static_dir, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        # 파일이 없으면 index.html로 리다이렉트 (SPA 지원)
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        else:
            return {"error": "File not found"}
