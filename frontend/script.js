// API 기본 URL (배포 환경 감지)
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000/api' 
    : '/api';

// DOM 요소들
const predictBtn = document.getElementById('predict-btn');
const predictionSection = document.getElementById('prediction-section');
const predictionResults = document.getElementById('prediction-results');
const numberSets = document.getElementById('number-sets');
const predictionReasoning = document.getElementById('prediction-reasoning');
// 분석 섹션 제거로 관련 DOM 요소 제거
const loadingOverlay = document.getElementById('loading-overlay');

// 스트레칭 모달 관련 요소
const stretchModal = document.getElementById('stretch-modal');
const stretchCloseBtn = document.getElementById('stretch-close');
const stretchDoneBtn = document.getElementById('stretch-done');
const watchRemaining = document.getElementById('watch-remaining');
const ytContainer = document.getElementById('yt-player');
const fallbackVideo = document.getElementById('fallback-video');

let ytPlayer = null;
let watchTimer = null;
let secondsWatched = 0;
let playerReady = false;
// 사용할 유튜브 영상 목록(무작위 선택)
const YT_VIDEO_IDS = [
    'RUGuHL0-Yug', // https://www.youtube.com/watch?v=RUGuHL0-Yug
    'TK-svYT9Qqg', // https://www.youtube.com/watch?v=TK-svYT9Qqg
    'WXtLkFVS2QY', // https://www.youtube.com/watch?v=WXtLkFVS2QY
    'XvG6EZTGYjs', // https://www.youtube.com/watch?v=XvG6EZTGYjs
    'Qm1Q8YYop18', // https://www.youtube.com/watch?v=Qm1Q8YYop18
];
function pickRandomVideoId() {
    return YT_VIDEO_IDS[Math.floor(Math.random() * YT_VIDEO_IDS.length)];
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 예측 버튼 이벤트 리스너
    predictBtn.addEventListener('click', openStretchModal);
    if (stretchCloseBtn) stretchCloseBtn.addEventListener('click', handleStretchClose);
    if (stretchDoneBtn) stretchDoneBtn.addEventListener('click', handleStretchDone);
});

// 유튜브 API 로드 콜백 (전역 요구)
window.onYouTubeIframeAPIReady = function() {
    // 유튜브 API 준비됐을 때만 생성하도록 지연 생성
    playerReady = true;
};

// 모달 열기: 비디오/타이머 초기화
function openStretchModal() {
    resetStretchState();
    if (stretchModal) {
        stretchModal.classList.remove('hidden');
        stretchModal.setAttribute('aria-hidden', 'false');
    }
    initPlayerOrFallback();
}

function handleStretchClose() {
    // 닫기 시에는 번호를 받지 않음
    cleanupPlayerAndTimer();
    if (stretchModal) {
        stretchModal.classList.add('hidden');
        stretchModal.setAttribute('aria-hidden', 'true');
    }
}

function handleStretchDone() {
    // 1분 시청 완료 시에만 예측 수행
    if (stretchDoneBtn && !stretchDoneBtn.disabled) {
        handlePrediction();
        // 완료 후 모달 닫기
        handleStretchClose();
    }
}

function resetStretchState() {
    secondsWatched = 0;
    if (watchRemaining) watchRemaining.textContent = `남은 시청 시간: 60초`;
    if (stretchDoneBtn) stretchDoneBtn.disabled = true;
}

function initPlayerOrFallback() {
    // 유튜브 사용 시: 준비된 리스트에서 무작위 선택
    const YT_VIDEO_ID = pickRandomVideoId();
    if (window.YT && window.YT.Player && playerReady && ytContainer) {
        ytPlayer = new YT.Player('yt-player', {
            videoId: YT_VIDEO_ID,
            playerVars: { 'autoplay': 1, 'controls': 1, 'playsinline': 1 },
            events: {
                'onStateChange': onPlayerStateChange
            }
        });
        if (fallbackVideo) fallbackVideo.style.display = 'none';
    } else {
        // 폴백: 로컬/빈 비디오로 1분 타이머만 진행
        if (fallbackVideo) {
            fallbackVideo.src = '';
            fallbackVideo.style.display = 'block';
        }
        startWatchTimer();
    }
}

function onPlayerStateChange(event) {
    // 재생 중일 때만 시청 시간 카운트
    const YT_PLAYING = 1;
    const YT_PAUSED = 2;
    const YT_ENDED = 0;
    if (event.data === YT_PLAYING) {
        startWatchTimer();
    } else if (event.data === YT_PAUSED) {
        stopWatchTimer();
    } else if (event.data === YT_ENDED) {
        // 끝났으면 남은 시간이 0이 아니면 맞춰줌
        secondsWatched = Math.max(secondsWatched, 60);
        updateWatchUI();
        checkEnableDone();
        stopWatchTimer();
    }
}

function startWatchTimer() {
    if (watchTimer) return;
    watchTimer = setInterval(() => {
        secondsWatched += 1;
        updateWatchUI();
        checkEnableDone();
        if (secondsWatched >= 60) {
            stopWatchTimer();
        }
    }, 1000);
}

function stopWatchTimer() {
    if (watchTimer) {
        clearInterval(watchTimer);
        watchTimer = null;
    }
}

function updateWatchUI() {
    const remaining = Math.max(0, 60 - secondsWatched);
    if (watchRemaining) watchRemaining.textContent = `남은 시청 시간: ${remaining}초`;
}

function checkEnableDone() {
    if (secondsWatched >= 60 && stretchDoneBtn) {
        stretchDoneBtn.disabled = false;
    }
}

function cleanupPlayerAndTimer() {
    stopWatchTimer();
    if (ytPlayer && ytPlayer.destroy) {
        try { ytPlayer.destroy(); } catch (e) {}
    }
    ytPlayer = null;
}

// 예측 처리
async function handlePrediction() {
    // 단일 통합 예측으로 고정
    const method = 'unified';
    
    showLoading(true);
    predictBtn.disabled = true;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 90000); // 90초 타임아웃 (초기 콜드스타트 대비)
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                method: method,
                num_sets: 5,
                include_bonus: false
            }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayPredictionResults(data.data);
        } else {
            showError('예측에 실패했습니다. 다시 시도해주세요.');
        }
    } catch (error) {
        console.error('예측 요청 실패:', error);
        if (error.name === 'AbortError') {
            showError('요청이 지연되어 취소되었습니다. 잠시 후 다시 시도해주세요.');
        } else {
            showError('서버 연결에 실패했습니다.');
        }
    } finally {
        showLoading(false);
        predictBtn.disabled = false;
    }
}

// 예측 결과 표시
function displayPredictionResults(data) {
    const sets = data.sets || [];
    
    // 번호 세트 표시
    numberSets.innerHTML = '';
    sets.forEach((set, index) => {
        const setElement = createNumberSetElement(set, index + 1);
        numberSets.appendChild(setElement);
    });
    
    // 근거 영역 제거
    if (predictionReasoning) {
        predictionReasoning.innerHTML = '';
        predictionReasoning.style.display = 'none';
    }
    // 결과 표시
    if (predictionSection) predictionSection.style.display = 'block';
    predictionResults.style.display = 'block';
}

// 번호 세트 요소 생성
function createNumberSetElement(numbers, setNumber) {
    const setElement = document.createElement('div');
    setElement.className = 'number-set';
    
    setElement.innerHTML = `
        <h4>세트 ${setNumber}</h4>
        <div class="numbers">
            ${numbers.map(num => `<div class="number">${num}</div>`).join('')}
        </div>
    `;
    
    return setElement;
}

// 분석 섹션 제거로 분석 데이터 로드/표시 로직 삭제

// 로딩 표시/숨김
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 에러 메시지 표시
function showError(message) {
    alert(message);
}

// 샘플 데이터로 테스트 (API 실패 시)
// 분석 섹션 제거로 샘플 데이터 표시 로직 삭제

// API 실패 시 샘플 데이터 사용
// 분석 샘플 데이터 로직 제거
