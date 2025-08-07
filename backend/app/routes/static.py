from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

# 정적 파일 디렉토리 설정
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")

# 정적 파일 마운트
try:
    from fastapi.staticfiles import StaticFiles
    static_files = StaticFiles(directory=static_dir)
except Exception as e:
    print(f"Static files setup error: {e}")

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
