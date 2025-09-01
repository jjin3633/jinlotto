#!/bin/bash
# Render 배포용 시작 스크립트

echo "로또 분석 서비스를 시작합니다..."

# Gunicorn으로 서버 시작
gunicorn main:app -c gunicorn_config.py
