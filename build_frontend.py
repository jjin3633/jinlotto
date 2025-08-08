#!/usr/bin/env python3
"""
프론트엔드 빌드 스크립트
프론트엔드 파일들을 backend/static 디렉토리로 복사합니다.
"""

import os
import shutil
import sys

def build_frontend():
    """프론트엔드 파일들을 backend/static 디렉토리로 복사"""
    
    # 경로 설정
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(project_root, "frontend")
    backend_dir = os.path.join(project_root, "backend")
    static_dir = os.path.join(backend_dir, "static")
    
    print(f"프로젝트 루트: {project_root}")
    print(f"프론트엔드 디렉토리: {frontend_dir}")
    print(f"백엔드 디렉토리: {backend_dir}")
    print(f"정적 파일 디렉토리: {static_dir}")
    
    # static 디렉토리 생성 (Windows 콘솔 인코딩 이슈 방지를 위해 이모지 미사용)
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"static 디렉토리 생성: {static_dir}")
    
    # 프론트엔드 파일들 복사
    frontend_files = [
        "index.html",
        "styles.css", 
        "script.js",
        "favicon.ico",
        "logo.svg",
    ]
    
    copied_files = []
    for file_name in frontend_files:
        src_path = os.path.join(frontend_dir, file_name)
        dst_path = os.path.join(static_dir, file_name)
        
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            copied_files.append(file_name)
            print(f"복사 완료: {file_name}")
        else:
            print(f"파일 없음: {src_path}")
    
    # 프로젝트 루트(배포 저장소 루트)에 위치한 자산도 함께 복사 (요청 사항)
    root_assets = [
        (os.path.join(project_root, 'favicon.png'), os.path.join(static_dir, 'favicon.png')),
        (os.path.join(project_root, 'logo.png'), os.path.join(static_dir, 'logo.png')),
        (os.path.join(project_root, 'logo.svg'), os.path.join(static_dir, 'logo.svg')),
    ]
    for src, dst in root_assets:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            copied_files.append(os.path.basename(dst))
            print(f"복사 완료: {os.path.basename(dst)}")
        else:
            print(f"파일 없음: {src}")

    if copied_files:
        print("\n프론트엔드 빌드 완료")
        print(f"복사된 파일: {', '.join(copied_files)}")
        print(f"정적 파일 위치: {static_dir}")
    else:
        print("\n복사할 파일이 없습니다.")
        sys.exit(1)

if __name__ == "__main__":
    build_frontend()
