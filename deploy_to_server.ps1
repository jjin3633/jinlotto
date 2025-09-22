# JinLotto 직접 서버 배포 스크립트 (PowerShell)

param(
    [string]$ServerIP = "43.201.75.105",
    [string]$ServerUser = "your_username",  # 실제 사용자명으로 변경
    [string]$ProjectPath = "/path/to/jinlotto",  # 실제 프로젝트 경로로 변경
    [string]$ServiceName = "jinlotto"
)

Write-Host "🚀 JinLotto 서버 배포 시작..." -ForegroundColor Green

try {
    # 1. 로컬에서 최신 코드 푸시
    Write-Host "📤 GitHub에 최신 코드 푸시..." -ForegroundColor Yellow
    git add .
    $commitMessage = "deploy: 서버 배포 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    try {
        git commit -m $commitMessage
    } catch {
        Write-Host "변경사항 없음" -ForegroundColor Gray
    }
    
    git push origin main
    
    # 2. SSH 명령어 생성
    $sshCommands = @"
set -e
cd $ProjectPath

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
sudo systemctl restart $ServiceName

echo "✅ 배포 완료!"
sudo systemctl status $ServiceName
"@

    # 3. SSH 실행
    Write-Host "🔗 서버 접속 및 배포 실행..." -ForegroundColor Yellow
    $sshCommand = "ssh $ServerUser@$ServerIP `"$sshCommands`""
    Invoke-Expression $sshCommand
    
    # 4. 배포 확인
    Write-Host "🔍 배포 확인 중..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    $healthCheck = Invoke-WebRequest -Uri "http://$ServerIP:8000/api/health" -UseBasicParsing
    if ($healthCheck.StatusCode -eq 200) {
        Write-Host "✅ 서버 정상 작동" -ForegroundColor Green
    } else {
        Write-Host "❌ 서버 오류" -ForegroundColor Red
    }
    
    Write-Host "🎉 배포 완료! http://$ServerIP:8000 에서 확인하세요." -ForegroundColor Green
    
} catch {
    Write-Host "❌ 배포 실패: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 사용법:
# .\deploy_to_server.ps1 -ServerUser "ubuntu" -ProjectPath "/home/ubuntu/jinlotto"
