#!/bin/bash
# 직접 서버 자동 배포 스크립트

set -e  # 에러 시 중단

SERVER_IP="43.201.75.105"
SERVER_USER="your_username"  # 실제 사용자명으로 변경
PROJECT_PATH="/path/to/jinlotto"  # 실제 프로젝트 경로로 변경
SERVICE_NAME="jinlotto"

echo "🚀 JinLotto 서버 배포 시작..."

# 1. 로컬에서 최신 코드 푸시
echo "📤 GitHub에 최신 코드 푸시..."
git add .
git commit -m "deploy: 서버 배포 $(date '+%Y-%m-%d %H:%M:%S')" || echo "변경사항 없음"
git push origin main

# 2. 서버에 SSH 접속하여 배포
echo "🔗 서버 접속 및 배포 실행..."
ssh $SERVER_USER@$SERVER_IP << EOF
    set -e
    cd $PROJECT_PATH
    
    echo "📥 최신 코드 가져오기..."
    git pull origin main
    
    echo "📦 의존성 업데이트..."
    pip install -r requirements.txt
    
    echo "🎨 프론트엔드 파일 업데이트..."
    python -c "
import shutil
shutil.copy2('frontend/index.html', 'backend/static/index.html')
shutil.copy2('frontend/script.js', 'backend/static/script.js')
shutil.copy2('frontend/styles.css', 'backend/static/styles.css')
print('✅ Frontend files updated')
"
    
    echo "🔄 서비스 재시작..."
    sudo systemctl restart $SERVICE_NAME
    
    echo "✅ 배포 완료!"
    sudo systemctl status $SERVICE_NAME
EOF

# 3. 배포 확인
echo "🔍 배포 확인 중..."
sleep 5
curl -f http://$SERVER_IP:8000/api/health && echo "✅ 서버 정상 작동" || echo "❌ 서버 오류"

echo "🎉 배포 완료! http://$SERVER_IP:8000 에서 확인하세요."
