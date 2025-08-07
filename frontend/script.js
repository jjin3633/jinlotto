// API 기본 URL (배포 환경 감지)
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:8000/api' 
    : '/api';

// DOM 요소들
const serviceStatus = document.getElementById('service-status');
const predictBtn = document.getElementById('predict-btn');
const predictionResults = document.getElementById('prediction-results');
const numberSets = document.getElementById('number-sets');
const predictionReasoning = document.getElementById('prediction-reasoning');
const hotNumbers = document.getElementById('hot-numbers');
const coldNumbers = document.getElementById('cold-numbers');
const oddEvenRatio = document.getElementById('odd-even-ratio');
const seasonalAnalysis = document.getElementById('seasonal-analysis');
const loadingOverlay = document.getElementById('loading-overlay');

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    checkServiceStatus();
    loadAnalysisData();
    
    // 예측 버튼 이벤트 리스너
    predictBtn.addEventListener('click', handlePrediction);
});

// 서비스 상태 확인
async function checkServiceStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok) {
            updateServiceStatus(true, '서비스 정상');
        } else {
            updateServiceStatus(false, '서비스 오류');
        }
    } catch (error) {
        console.error('서비스 상태 확인 실패:', error);
        updateServiceStatus(false, '연결 실패');
    }
}

// 서비스 상태 업데이트
function updateServiceStatus(isOnline, message) {
    const statusDot = serviceStatus.querySelector('.status-dot');
    const statusText = serviceStatus.querySelector('.status-text');
    
    if (isOnline) {
        statusDot.classList.add('online');
        statusText.textContent = message;
    } else {
        statusDot.classList.remove('online');
        statusText.textContent = message;
    }
}

// 예측 처리
async function handlePrediction() {
    const method = document.querySelector('input[name="method"]:checked').value;
    
    showLoading(true);
    predictBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                method: method,
                num_sets: 5,
                include_bonus: false
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayPredictionResults(data.data);
        } else {
            showError('예측에 실패했습니다. 다시 시도해주세요.');
        }
    } catch (error) {
        console.error('예측 요청 실패:', error);
        showError('서버 연결에 실패했습니다.');
    } finally {
        showLoading(false);
        predictBtn.disabled = false;
    }
}

// 예측 결과 표시
function displayPredictionResults(data) {
    const sets = data.sets || [];
    const confidenceScores = data.confidence_scores || [];
    const reasoning = data.reasoning || [];
    
    // 번호 세트 표시
    numberSets.innerHTML = '';
    sets.forEach((set, index) => {
        const confidence = confidenceScores[index] || 0.3;
        const setElement = createNumberSetElement(set, index + 1, confidence);
        numberSets.appendChild(setElement);
    });
    
    // 예측 근거 표시
    predictionReasoning.innerHTML = `
        <h4><i class="fas fa-lightbulb"></i> 예측 근거</h4>
        <ul>
            ${reasoning.map(reason => `<li>${reason}</li>`).join('')}
        </ul>
    `;
    
    // 결과 표시
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

// 분석 데이터 로드
async function loadAnalysisData() {
    try {
        // 종합 분석 데이터 가져오기
        const response = await fetch(`${API_BASE_URL}/analysis/comprehensive`);
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayAnalysisData(data.data);
        }
    } catch (error) {
        console.error('분석 데이터 로드 실패:', error);
    }
}

// 분석 데이터 표시
function displayAnalysisData(data) {
    // 핫 번호 표시
    const hotNumbersList = data.hot_numbers || [];
    hotNumbers.innerHTML = hotNumbersList.slice(0, 10).map(num => 
        `<span class="number-item">${num}</span>`
    ).join('');
    
    // 콜드 번호 표시
    const coldNumbersList = data.cold_numbers || [];
    coldNumbers.innerHTML = coldNumbersList.slice(0, 10).map(num => 
        `<span class="number-item">${num}</span>`
    ).join('');
    
    // 홀짝 비율 표시
    const oddEven = data.odd_even_ratio || {};
    oddEvenRatio.innerHTML = `
        <div class="ratio-item">
            <div class="ratio-value">${(oddEven.odd_ratio * 100 || 0).toFixed(1)}%</div>
            <div class="ratio-label">홀수</div>
        </div>
        <div class="ratio-item">
            <div class="ratio-value">${(oddEven.even_ratio * 100 || 0).toFixed(1)}%</div>
            <div class="ratio-label">짝수</div>
        </div>
    `;
    
    // 계절별 분석 표시
    const seasonal = data.seasonal_analysis || {};
    seasonalAnalysis.innerHTML = Object.entries(seasonal).map(([season, data]) => {
        const hotNums = data.hot_numbers ? data.hot_numbers.slice(0, 3).map(item => item[0]).join(', ') : '';
        return `
            <div class="season-item">
                <span>${season}</span>
                <span>${data.draw_count}회, 핫번호: ${hotNums}</span>
            </div>
        `;
    }).join('');
}

// 로딩 표시/숨김
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 에러 메시지 표시
function showError(message) {
    alert(message);
}

// 샘플 데이터로 테스트 (API 실패 시)
function loadSampleData() {
    // 핫 번호 샘플
    hotNumbers.innerHTML = [37, 8, 17, 2, 19, 33, 15, 41, 1, 44].map(num => 
        `<span class="number-item">${num}</span>`
    ).join('');
    
    // 콜드 번호 샘플
    coldNumbers.innerHTML = [9, 41, 42, 4, 22, 15, 28, 6, 32, 23].map(num => 
        `<span class="number-item">${num}</span>`
    ).join('');
    
    // 홀짝 비율 샘플
    oddEvenRatio.innerHTML = `
        <div class="ratio-item">
            <div class="ratio-value">52.3%</div>
            <div class="ratio-label">홀수</div>
        </div>
        <div class="ratio-item">
            <div class="ratio-value">47.7%</div>
            <div class="ratio-label">짝수</div>
        </div>
    `;
    
    // 계절별 분석 샘플
    seasonalAnalysis.innerHTML = `
        <div class="season-item">
            <span>봄</span>
            <span>303회, 핫번호: 13, 38, 3</span>
        </div>
        <div class="season-item">
            <span>여름</span>
            <span>298회, 핫번호: 1, 20, 34</span>
        </div>
        <div class="season-item">
            <span>가을</span>
            <span>286회, 핫번호: 21, 45, 14</span>
        </div>
        <div class="season-item">
            <span>겨울</span>
            <span>296회, 핫번호: 33, 39, 27</span>
        </div>
    `;
}

// API 실패 시 샘플 데이터 사용
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // 로컬 환경에서는 샘플 데이터도 로드
    setTimeout(() => {
        if (hotNumbers.children.length === 0) {
            loadSampleData();
        }
    }, 2000);
}
