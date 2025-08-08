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

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 예측 버튼 이벤트 리스너
    predictBtn.addEventListener('click', handlePrediction);
});

// 예측 처리
async function handlePrediction() {
    // 단일 통합 예측으로 고정
    const method = 'unified';
    
    showLoading(true);
    predictBtn.disabled = true;
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30초 타임아웃
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
    const confidenceScores = data.confidence_scores || [];
    
    // 번호 세트 표시
    numberSets.innerHTML = '';
    sets.forEach((set, index) => {
        const confidence = confidenceScores[index] || 0.3;
        const setElement = createNumberSetElement(set, index + 1, confidence);
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
function createNumberSetElement(numbers, setNumber, confidence) {
    const setElement = document.createElement('div');
    setElement.className = 'number-set';
    
    setElement.innerHTML = `
        <h4>세트 ${setNumber}</h4>
        <div class="numbers">
            ${numbers.map(num => `<div class="number">${num}</div>`).join('')}
        </div>
        <div class="confidence">신뢰도: ${(confidence * 100).toFixed(1)}%</div>
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
