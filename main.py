#!/usr/bin/env python3
"""
로또 번호 추천 서비스 - 메인 애플리케이션
Render 배포를 위한 루트 레벨 진입점
"""

import sys
import os

# backend의 main.py에서 app 객체를 직접 가져오기
if __name__ == "__main__":
    # 프로젝트 루트 기준에서 backend 모듈을 직접 참조하여 실행
    from backend.main import app
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
    )

# Gunicorn을 위한 app 객체 (Render에서 필요)
from backend.main import app
