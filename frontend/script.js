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

let ytPlayer = null;
let watchTimer = null;
let secondsWatched = 0;
let playerReady = false;
let warmedUp = false;
// 피드백 모달 관련
const feedbackOpenBtn = document.getElementById('feedback-open');
const feedbackModal = document.getElementById('feedback-modal');
const feedbackCloseBtn = document.getElementById('feedback-close');
const feedbackSendBtn = document.getElementById('feedback-send');
const feedbackInput = document.getElementById('feedback-input');
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

// 접근성/포커스 관리 상태 및 유틸리티
let lastFocusedBeforeStretch = null;
let lastFocusedBeforeFeedback = null;

function setSiblingsInert(parent, exceptions, makeInert) {
	try {
		if (!parent) return;
		const exc = new Set((exceptions || []).filter(Boolean));
		Array.from(parent.children || []).forEach((child) => {
			if (!exc.has(child)) {
				if (makeInert) child.setAttribute('inert', '');
				else child.removeAttribute('inert');
			}
		});
	} catch (e) {}
}

function focusFirstInModal(modal) {
	const selectors = [
		'button:not([disabled])',
		'a[href]',
		'input:not([disabled])',
		'select:not([disabled])',
		'textarea:not([disabled])',
		'[tabindex]:not([tabindex="-1"])'
	];
	const first = modal && modal.querySelector(selectors.join(','));
	if (first && first.focus) first.focus();
	else if (modal && modal.focus) modal.focus();
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 예측 버튼 이벤트 리스너
    predictBtn.addEventListener('click', openStretchModal);
    if (stretchCloseBtn) stretchCloseBtn.addEventListener('click', handleStretchClose);
    if (stretchDoneBtn) stretchDoneBtn.addEventListener('click', handleStretchDone);
    if (feedbackOpenBtn) feedbackOpenBtn.addEventListener('click', openFeedbackModal);
    if (feedbackCloseBtn) feedbackCloseBtn.addEventListener('click', closeFeedbackModal);
    if (feedbackSendBtn) feedbackSendBtn.addEventListener('click', sendFeedback);
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
        // 배경 비활성화(inert) 및 포커스 이동
        lastFocusedBeforeStretch = document.activeElement;
        const container = document.querySelector('.container');
        setSiblingsInert(container, [stretchModal], true);

        stretchModal.classList.remove('hidden');
        stretchModal.removeAttribute('aria-hidden');
        stretchModal.setAttribute('aria-modal', 'true');
        setTimeout(() => {
            focusFirstInModal(stretchModal);
        }, 0);
    }
    initPlayerOrFallback();
}

function handleStretchClose() {
    // 닫기 시에는 번호를 받지 않음
    cleanupPlayerAndTimer();
    if (stretchModal) {
        // aria-hidden 적용 전에 포커스 복원
        try {
            if (lastFocusedBeforeStretch && document.contains(lastFocusedBeforeStretch)) {
                lastFocusedBeforeStretch.focus();
            } else if (predictBtn) {
                predictBtn.focus();
            }
        } catch (e) {}

        stretchModal.setAttribute('aria-hidden', 'true');
        stretchModal.removeAttribute('aria-modal');
        stretchModal.classList.add('hidden');

        // 배경 inert 해제
        const container = document.querySelector('.container');
        setSiblingsInert(container, [stretchModal], false);
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
    warmedUp = false;
}

function initPlayerOrFallback() {
    // 유튜브 사용 시: 준비된 리스트에서 무작위 선택
    const YT_VIDEO_ID = pickRandomVideoId();
    if (window.YT && window.YT.Player && playerReady && ytContainer) {
        ytPlayer = new YT.Player('yt-player', {
            videoId: YT_VIDEO_ID,
            height: '390',
            width: '640',
            playerVars: { 'autoplay': 1, 'controls': 1, 'playsinline': 1 },
            events: {
                'onStateChange': onPlayerStateChange
            }
        });
    } else {
        // IFrame API가 아직 준비 전이면 1분 타이머만 진행
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
        // 40초 경과(남은 20초) 시점에 1회만 워밍업: 서버/DB 콜드스타트 방지
        if (!warmedUp && secondsWatched >= 40) {
            warmedUp = true;
            warmUpServer();
        }
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

// 경량 워밍업 호출: /api/health 를 짧은 타임아웃으로 호출
function warmUpServer() {
    try {
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 5000);
        fetch(`${API_BASE_URL}/health`, { method: 'GET', signal: controller.signal })
            .then(() => clearTimeout(t))
            .catch(() => clearTimeout(t));
    } catch (e) {
        // 무시: 워밍업 실패해도 플로우에는 영향 없음
    }
}

// 피드백 모달
function openFeedbackModal() {
    if (feedbackModal) {
        lastFocusedBeforeFeedback = document.activeElement;
        const container = document.querySelector('.container');
        setSiblingsInert(container, [feedbackModal], true);

        feedbackModal.classList.remove('hidden');
        feedbackModal.removeAttribute('aria-hidden');
        feedbackModal.setAttribute('aria-modal', 'true');
        if (feedbackInput) feedbackInput.value = '';
        setTimeout(() => {
            focusFirstInModal(feedbackModal);
        }, 0);
    }
}
function closeFeedbackModal() {
    if (feedbackModal) {
        try {
            if (lastFocusedBeforeFeedback && document.contains(lastFocusedBeforeFeedback)) {
                lastFocusedBeforeFeedback.focus();
            } else if (predictBtn) {
                predictBtn.focus();
            }
        } catch (e) {}

        feedbackModal.setAttribute('aria-hidden', 'true');
        feedbackModal.removeAttribute('aria-modal');
        feedbackModal.classList.add('hidden');

        const container = document.querySelector('.container');
        setSiblingsInert(container, [feedbackModal], false);
    }
}
async function sendFeedback() {
    const msg = (feedbackInput && feedbackInput.value ? feedbackInput.value.trim() : '');
    if (!msg) { alert('의견을 입력해 주세요.'); return; }
    try {
        const res = await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg }),
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert('의견이 접수되었습니다. 감사합니다!');
            closeFeedbackModal();
        } else {
            alert('전송에 실패했습니다. 잠시 후 다시 시도해 주세요.');
        }
    } catch (e) {
        alert('네트워크 오류로 전송에 실패했습니다.');
    }
}

// 예측 처리
async function handlePrediction() {
    // 단일 통합 예측으로 고정
    const method = 'unified';
    
    showLoading(true);
    predictBtn.disabled = true;
    let predictionSucceeded = false;
    
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
                num_sets: 1,
                include_bonus: false
            }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayPredictionResults(data.data);
            predictionSucceeded = true;
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
        // 성공 시에는 버튼을 비활성화 상태로 유지(하루 1회)
        // 실패 시에만 다시 시도할 수 있도록 활성화
        predictBtn.disabled = predictionSucceeded ? true : false;
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