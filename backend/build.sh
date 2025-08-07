#!/bin/bash
# Render 배포용 빌드 스크립트

echo "로또 분석 서비스 빌드를 시작합니다..."

# Python 가상환경 생성 (필요시)
# python -m venv venv
# source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 데이터 디렉토리 생성
mkdir -p data

echo "빌드가 완료되었습니다."
