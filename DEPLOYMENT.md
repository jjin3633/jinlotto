# 🚀 Render 배포 가이드

## 📋 개요

로또 번호 추천 서비스를 Render에 배포하는 방법을 안내합니다.

## 🎯 배포 구조

```
프로젝트/
├── backend/           # FastAPI 백엔드
│   ├── main.py       # 메인 애플리케이션
│   ├── requirements.txt
│   ├── runtime.txt   # Python 버전
│   ├── Procfile      # Render 프로세스 설정
│   ├── build_frontend.py  # 프론트엔드 빌드 스크립트
│   └── static/       # 정적 파일 (빌드 시 생성)
└── frontend/         # HTML/CSS/JS 프론트엔드
    ├── index.html
    ├── styles.css
    └── script.js
```

## 🔧 배포 준비

### 1. 로컬 테스트

```bash
# 백엔드 실행
cd backend
python main.py

# 프론트엔드 빌드
python build_frontend.py

# 브라우저에서 확인
# http://localhost:8000
```

### 2. Git 저장소 준비

```bash
# Git 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit for Render deployment"
```

## 🌐 Render 배포

### 1. Render 계정 생성
- [render.com](https://render.com)에서 계정 생성
- GitHub 계정 연동

### 2. 새 Web Service 생성

1. **Render Dashboard**에서 "New +" 클릭
2. **Web Service** 선택
3. **GitHub 저장소 연결** 선택

### 3. 서비스 설정

#### 기본 설정
- **Name**: `lotto-prediction-service`
- **Environment**: `Python 3`
- **Region**: `Oregon (US West)` 또는 가까운 지역
- **Branch**: `main`

#### 빌드 설정
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && python build_frontend.py
  ```
- **Start Command**: 
  ```bash
  gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120
  ```

#### 환경 변수 (선택사항)
```
PYTHON_VERSION=3.11.7
```

### 4. 배포 실행

1. **Create Web Service** 클릭
2. 배포 진행 상황 모니터링
3. 배포 완료 후 제공된 URL 확인

## 🔍 배포 확인

### 1. 서비스 상태 확인
- Render Dashboard에서 서비스 상태 확인
- 로그 확인 (Logs 탭)

### 2. 기능 테스트
- 메인 페이지 접속: `https://your-app-name.onrender.com`
- API 테스트: `https://your-app-name.onrender.com/api/health`
- 프론트엔드 테스트: 번호 추천 기능 사용

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. 빌드 실패
```bash
# 로컬에서 테스트
cd backend
pip install -r requirements.txt
python build_frontend.py
```

#### 2. 정적 파일 404
- `build_frontend.py`가 실행되었는지 확인
- `static/` 디렉토리에 파일들이 있는지 확인

#### 3. API 연결 실패
- CORS 설정 확인
- 프론트엔드의 API URL 설정 확인

#### 4. 메모리 부족
- `requirements.txt`에서 불필요한 패키지 제거
- Gunicorn 워커 수 조정

### 로그 확인
```bash
# Render Dashboard > Logs 탭에서 확인
# 또는 Render CLI 사용
render logs --service lotto-prediction-service
```

## 📊 모니터링

### Render Dashboard에서 확인 가능한 정보
- **Uptime**: 서비스 가동 시간
- **Response Time**: 응답 시간
- **Error Rate**: 오류율
- **Logs**: 실시간 로그

### 알림 설정
- **Slack Integration**: 오류 알림
- **Email Notifications**: 상태 변경 알림

## 🔄 업데이트

### 코드 업데이트
```bash
# 로컬에서 변경사항 커밋
git add .
git commit -m "Update feature"
git push origin main

# Render에서 자동 배포됨
```

### 수동 배포
- Render Dashboard > Manual Deploy
- 특정 커밋으로 배포 가능

## 💰 비용 관리

### 무료 티어 제한
- **월 750시간** (약 31일)
- **512MB RAM**
- **CPU 공유**

### 유료 업그레이드
- **Pro**: $7/월
- **Custom**: 맞춤형 설정

## 🔒 보안 고려사항

### 프로덕션 환경
- CORS 설정 제한
- API 키 관리
- HTTPS 강제

### 환경 변수
```bash
# 민감한 정보는 환경 변수로 관리
DATABASE_URL=your_database_url
API_KEY=your_api_key
```

## 📞 지원

### 문제 발생 시
1. **Render Logs** 확인
2. **로컬 테스트**로 문제 격리
3. **GitHub Issues** 생성
4. **Render Support** 문의

---

**🎉 배포 완료 후 서비스 URL을 공유하세요!**
