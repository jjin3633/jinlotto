#!/usr/bin/env python3
"""
로또 번호 추천 서비스 - 메인 애플리케이션
Render 배포를 위한 루트 레벨 진입점
"""

import sys
import os

# backend 디렉토리를 Python 경로에 추가
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

# backend의 main.py에서 app 객체를 직접 가져오기
if __name__ == "__main__":
    # backend 디렉토리로 이동
    os.chdir(backend_path)
    
    # backend의 main.py 임포트
    from main import app
    
    # uvicorn으로 실행
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )

# Gunicorn을 위한 app 객체 (Render에서 필요)
from backend.main import app
