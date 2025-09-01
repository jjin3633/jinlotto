#!/usr/bin/env python3
"""
프론트엔드 빌드 스크립트
프론트엔드 파일들을 backend/static 디렉토리로 복사합니다.
"""

import os
import shutil
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_frontend():
    """프론트엔드 파일들을 backend/static 디렉토리로 복사"""
    
    # 경로 설정 (이 스크립트는 scripts/ 내부에 있으므로 상위가 프로젝트 루트)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    frontend_dir = os.path.join(project_root, "frontend")
    backend_dir = os.path.join(project_root, "backend")
    static_dir = os.path.join(backend_dir, "static")
    
    logger.info(f"프로젝트 루트: {project_root}")
    logger.info(f"프론트엔드 디렉토리: {frontend_dir}")
    logger.info(f"백엔드 디렉토리: {backend_dir}")
    logger.info(f"정적 파일 디렉토리: {static_dir}")
    
    # static 디렉토리 생성 (Windows 콘솔 인코딩 이슈 방지를 위해 이모지 미사용)
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        logger.info(f"static 디렉토리 생성: {static_dir}")
    
    # 프론트엔드 파일들 복사
    frontend_files = [
        "index.html",
        "styles.css", 
        "script.js",
        "favicon.ico",
        "logo.svg",
        "robots.txt",
        "sitemap.xml",
        "rss.xml",
        "ads.txt",
    ]
    
    copied_files = []
    for file_name in frontend_files:
        src_path = os.path.join(frontend_dir, file_name)
        dst_path = os.path.join(static_dir, file_name)
        
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            copied_files.append(file_name)
            logger.info(f"복사 완료: {file_name}")
        else:
            logger.warning(f"파일 없음: {src_path}")
    
    # 정리된 자산 경로에서 복사
    images_dir = os.path.join(project_root, 'assets', 'images')
    media_dir = os.path.join(project_root, 'assets', 'media')
    root_assets = [
        (os.path.join(images_dir, 'favicon.png'), os.path.join(static_dir, 'favicon.png')),
        (os.path.join(images_dir, 'logo.png'), os.path.join(static_dir, 'logo.png')),
        (os.path.join(images_dir, 'logo.svg'), os.path.join(static_dir, 'logo.svg')),
        (os.path.join(media_dir, 'Main_KR_Home.mp4'), os.path.join(static_dir, 'Main_KR_Home.mp4')),
        # Laurel icons: copy SVG if available, fall back to PNG
        (os.path.join(images_dir, 'laurel1.svg'), os.path.join(static_dir, 'laurel1.svg')),
        (os.path.join(images_dir, 'laurel2.svg'), os.path.join(static_dir, 'laurel2.svg')),
        (os.path.join(images_dir, 'laurel1.png'), os.path.join(static_dir, 'laurel1.png')),
        (os.path.join(images_dir, 'laurel2.png'), os.path.join(static_dir, 'laurel2.png')),
    ]
    for src, dst in root_assets:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_files.append(os.path.basename(dst))
            logger.info(f"복사 완료: {os.path.basename(dst)}")
        else:
            logger.warning(f"파일 없음: {src}")

    if copied_files:
        logger.info("프론트엔드 빌드 완료")
        logger.info(f"복사된 파일: {', '.join(copied_files)}")
        logger.info(f"정적 파일 위치: {static_dir}")
    else:
        logger.warning("복사할 파일이 없습니다.")
        sys.exit(1)

if __name__ == "__main__":
    build_frontend()
