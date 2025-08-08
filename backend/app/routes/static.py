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

# /static 경로는 애플리케이션 레벨에서 StaticFiles로 마운트되므로 제거

# 루트 최상위 경로로 접근하는 정적 자산에 대한 편의 라우트
@router.get("/styles.css")
async def serve_root_styles():
    file_path = os.path.join(static_dir, "styles.css")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/script.js")
async def serve_root_script():
    file_path = os.path.join(static_dir, "script.js")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/favicon.ico")
async def serve_favicon():
    # frontend에 favicon.ico가 존재하면 빌드 시 static으로 복사됨
    ico_path = os.path.join(static_dir, "favicon.ico")
    png_path = os.path.join(static_dir, "favicon.png")
    if os.path.exists(ico_path):
        return FileResponse(ico_path)
    if os.path.exists(png_path):
        return FileResponse(png_path)
    return {"error": "File not found"}

@router.get("/favicon.png")
async def serve_favicon_png():
    file_path = os.path.join(static_dir, "favicon.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/logo.png")
async def serve_logo_png():
    file_path = os.path.join(static_dir, "logo.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/logo.svg")
async def serve_logo_svg():
    file_path = os.path.join(static_dir, "logo.svg")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/Main_KR_Home.mp4")
async def serve_main_video():
    file_path = os.path.join(static_dir, "Main_KR_Home.mp4")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}
