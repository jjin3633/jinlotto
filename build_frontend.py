#!/usr/bin/env python3
"""
호환용 프론트엔드 빌드 래퍼
Render 대시보드가 여전히 `python build_frontend.py`를 호출하는 경우를 위해
`scripts/build_frontend.py`를 실행하도록 위임합니다.
"""

import os
import sys
import runpy


def main() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(project_root, "scripts", "build_frontend.py")
    if not os.path.exists(target):
        print(f"빌드 스크립트를 찾을 수 없습니다: {target}", file=sys.stderr)
        sys.exit(1)
    runpy.run_path(target, run_name="__main__")


if __name__ == "__main__":
    main()


