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

@router.get("/static/{path:path}")
async def serve_static_files(path: str):
    """정적 파일 서빙 (/static 경로 하위만)"""
    file_path = os.path.join(static_dir, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    else:
        return {"error": "File not found"}


# 편의 라우트: /assets/* 요청을 backend static 디렉터리로 바로 매핑
@router.get("/assets/{path:path}")
async def serve_assets(path: str):
    """Serve files requested under /assets/... from the backend static directory."""
    file_path = os.path.join(static_dir, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

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


@router.get("/laurel1.png")
async def serve_laurel1_png():
    file_path = os.path.join(static_dir, "laurel1.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}


@router.get("/laurel2.png")
async def serve_laurel2_png():
    file_path = os.path.join(static_dir, "laurel2.png")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}


@router.get("/Main_KR_Home.mp4")
async def serve_main_video():
    file_path = os.path.join(static_dir, "Main_KR_Home.mp4")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# SEO: robots.txt, sitemap.xml 루트 제공
@router.get("/robots.txt")
async def serve_robots():
    file_path = os.path.join(static_dir, "robots.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

@router.get("/sitemap.xml")
async def serve_sitemap():
    """사이트맵 최적화 서빙 - Google Search Console 호환성 향상"""
    file_path = os.path.join(static_dir, "sitemap.xml")
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            media_type="application/xml; charset=utf-8",  # UTF-8 인코딩 명시
            headers={
                "Cache-Control": "public, max-age=3600",  # 1시간 캐시
                "X-Robots-Tag": "noindex",  # 사이트맵 자체는 색인하지 않음
                "Content-Type": "application/xml; charset=utf-8"  # 추가 보장
            }
        )
    return {"error": "File not found"}

@router.get("/rss.xml")
async def serve_rss():
    """RSS 피드 최적화 서빙 - Google Search Console 호환성 향상"""
    file_path = os.path.join(static_dir, "rss.xml")
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            media_type="application/rss+xml; charset=utf-8",  # UTF-8 인코딩 명시
            headers={
                "Cache-Control": "public, max-age=1800",  # 30분 캐시
                "X-Robots-Tag": "noindex",  # RSS 자체는 색인하지 않음
                "Content-Type": "application/rss+xml; charset=utf-8"  # 추가 보장
            }
        )
    return {"error": "File not found"}

@router.get("/ads.txt")
async def serve_ads():
    file_path = os.path.join(static_dir, "ads.txt")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}
