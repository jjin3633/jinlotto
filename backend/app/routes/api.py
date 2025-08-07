from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging
import pandas as pd

from ..models.lotto_models import (
    PredictionRequest, 
    PredictionResult, 
    AnalysisResult, 
    APIResponse,
    VisualizationData
)
from ..services.data_service import DataService
from ..services.analysis_service import AnalysisService
from ..services.prediction_service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["lotto-analysis"])

# 서비스 인스턴스 생성
data_service = DataService()
analysis_service = AnalysisService()
prediction_service = PredictionService()

@router.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "message": "로또 분석 서비스가 정상 작동 중입니다."}

@router.get("/data/summary")
async def get_data_summary():
    """데이터 요약 정보 조회"""
    try:
        df = data_service.load_data()
        summary = data_service.get_data_summary(df)
        
        return APIResponse(
            success=True,
            message="데이터 요약 정보를 성공적으로 조회했습니다.",
            data=summary
        )
    except Exception as e:
        logger.error(f"데이터 요약 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/collect")
async def collect_lotto_data(start_draw: int = 1, end_draw: int = None):
    """실제 로또 데이터 수집"""
    try:
        logger.info(f"로또 데이터 수집 시작: {start_draw}회차 ~ {end_draw}회차")
        
        df = data_service.collect_lotto_data(start_draw, end_draw)
        data_service.save_data(df)
        
        summary = data_service.get_data_summary(df)
        
        return APIResponse(
            success=True,
            message=f"로또 데이터 수집이 완료되었습니다. (총 {len(df)}회차)",
            data={
                "collected_draws": len(df),
                "date_range": summary.get('date_range', {}),
                "latest_draw": summary.get('latest_draw', {})
            }
        )
    except Exception as e:
        logger.error(f"데이터 수집 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/update")
async def update_latest_data():
    """최신 데이터 업데이트"""
    try:
        logger.info("최신 데이터 업데이트 시작")
        
        df = data_service.update_latest_data()
        summary = data_service.get_data_summary(df)
        
        return APIResponse(
            success=True,
            message="데이터 업데이트가 완료되었습니다.",
            data={
                "total_draws": len(df),
                "latest_draw": summary.get('latest_draw', {})
            }
        )
    except Exception as e:
        logger.error(f"데이터 업데이트 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/latest")
async def get_latest_draw():
    """최신 회차 정보 조회"""
    try:
        latest_draw = data_service._get_latest_draw_number()
        latest_data = data_service._fetch_draw_data(latest_draw)
        
        if latest_data:
            return APIResponse(
                success=True,
                message="최신 회차 정보를 조회했습니다.",
                data=latest_data
            )
        else:
            raise HTTPException(status_code=404, detail="최신 회차 정보를 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"최신 회차 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/comprehensive")
async def get_comprehensive_analysis():
    """종합 분석 결과 조회"""
    try:
        df = data_service.load_data()
        analysis_result = analysis_service.comprehensive_analysis(df)
        
        return APIResponse(
            success=True,
            message="종합 분석이 완료되었습니다.",
            data=analysis_result
        )
    except Exception as e:
        logger.error(f"종합 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/frequency")
async def get_frequency_analysis():
    """번호별 출현 빈도 분석"""
    try:
        df = data_service.load_data()
        frequency = analysis_service.analyze_frequency(df)
        
        return APIResponse(
            success=True,
            message="번호별 출현 빈도 분석이 완료되었습니다.",
            data={"frequency": frequency}
        )
    except Exception as e:
        logger.error(f"빈도 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/hot-cold")
async def get_hot_cold_analysis():
    """핫/콜드 번호 분석"""
    try:
        df = data_service.load_data()
        hot_numbers, cold_numbers = analysis_service.find_hot_cold_numbers(df)
        
        return APIResponse(
            success=True,
            message="핫/콜드 번호 분석이 완료되었습니다.",
            data={
                "hot_numbers": hot_numbers,
                "cold_numbers": cold_numbers
            }
        )
    except Exception as e:
        logger.error(f"핫/콜드 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 새로운 세밀한 분석 API 엔드포인트들
@router.get("/analysis/seasonal")
async def get_seasonal_analysis():
    """계절별 패턴 분석"""
    try:
        df = data_service.load_data()
        seasonal_analysis = analysis_service.analyze_seasonal_patterns(df)
        
        return APIResponse(
            success=True,
            message="계절별 패턴 분석이 완료되었습니다.",
            data=seasonal_analysis
        )
    except Exception as e:
        logger.error(f"계절별 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/monthly")
async def get_monthly_analysis():
    """월별 패턴 분석"""
    try:
        df = data_service.load_data()
        monthly_analysis = analysis_service.analyze_monthly_patterns(df)
        
        return APIResponse(
            success=True,
            message="월별 패턴 분석이 완료되었습니다.",
            data=monthly_analysis
        )
    except Exception as e:
        logger.error(f"월별 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/weekly")
async def get_weekly_analysis():
    """요일별 패턴 분석"""
    try:
        df = data_service.load_data()
        weekly_analysis = analysis_service.analyze_weekly_patterns(df)
        
        return APIResponse(
            success=True,
            message="요일별 패턴 분석이 완료되었습니다.",
            data=weekly_analysis
        )
    except Exception as e:
        logger.error(f"요일별 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/date")
async def get_date_analysis():
    """날짜별 패턴 분석 (1일~31일)"""
    try:
        df = data_service.load_data()
        date_analysis = analysis_service.analyze_date_patterns(df)
        
        return APIResponse(
            success=True,
            message="날짜별 패턴 분석이 완료되었습니다.",
            data=date_analysis
        )
    except Exception as e:
        logger.error(f"날짜별 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/sum")
async def get_sum_analysis():
    """번호 합계 패턴 분석"""
    try:
        df = data_service.load_data()
        sum_analysis = analysis_service.analyze_sum_patterns(df)
        
        return APIResponse(
            success=True,
            message="번호 합계 패턴 분석이 완료되었습니다.",
            data=sum_analysis
        )
    except Exception as e:
        logger.error(f"합계 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/gap")
async def get_gap_analysis():
    """번호 간격 패턴 분석"""
    try:
        df = data_service.load_data()
        gap_analysis = analysis_service.analyze_gap_patterns(df)
        
        return APIResponse(
            success=True,
            message="번호 간격 패턴 분석이 완료되었습니다.",
            data=gap_analysis
        )
    except Exception as e:
        logger.error(f"간격 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/prime")
async def get_prime_analysis():
    """소수 번호 패턴 분석"""
    try:
        df = data_service.load_data()
        prime_analysis = analysis_service.analyze_prime_number_patterns(df)
        
        return APIResponse(
            success=True,
            message="소수 번호 패턴 분석이 완료되었습니다.",
            data=prime_analysis
        )
    except Exception as e:
        logger.error(f"소수 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/ending")
async def get_ending_analysis():
    """끝자리 패턴 분석"""
    try:
        df = data_service.load_data()
        ending_analysis = analysis_service.analyze_ending_patterns(df)
        
        return APIResponse(
            success=True,
            message="끝자리 패턴 분석이 완료되었습니다.",
            data=ending_analysis
        )
    except Exception as e:
        logger.error(f"끝자리 분석 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict")
async def predict_numbers(request: PredictionRequest):
    """로또 번호 예측"""
    try:
        df = data_service.load_data()
        
        # 예측 방법에 따른 번호 생성
        if request.method == "statistical":
            predictions = prediction_service.statistical_prediction(df, request.num_sets)
        elif request.method == "ml":
            predictions = prediction_service.ml_prediction(df, request.num_sets)
        elif request.method == "hybrid":
            predictions = prediction_service.hybrid_prediction(df, request.num_sets)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 예측 방법입니다.")
        
        # 분석 결과 가져오기 (근거 생성용)
        analysis_result = analysis_service.comprehensive_analysis(df)
        
        # 예측 근거 생성
        reasoning = prediction_service.get_prediction_reasoning(request.method, analysis_result)
        
        # 신뢰도 점수 계산
        confidence_scores = prediction_service.calculate_confidence_scores(request.method, request.num_sets)
        
        # 결과 생성
        result = PredictionResult(
            sets=predictions,
            confidence_scores=confidence_scores,
            reasoning=reasoning,
            analysis_summary=f"{request.method} 방법을 사용한 {request.num_sets}세트 예측",
            disclaimer="이 예측은 참고용이며, 실제 당첨을 보장하지 않습니다. 건전한 복권 이용을 권장합니다."
        )
        
        return APIResponse(
            success=True,
            message="번호 예측이 완료되었습니다.",
            data=result.dict()
        )
        
    except Exception as e:
        logger.error(f"번호 예측 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization/frequency-chart")
async def get_frequency_chart():
    """번호별 출현 빈도 차트 데이터"""
    try:
        df = data_service.load_data()
        frequency = analysis_service.analyze_frequency(df)
        
        chart_data = {
            "labels": list(range(1, 46)),
            "datasets": [{
                "label": "출현 빈도",
                "data": [frequency.get(i, 0) for i in range(1, 46)],
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        }
        
        return APIResponse(
            success=True,
            message="빈도 차트 데이터를 생성했습니다.",
            data=chart_data
        )
    except Exception as e:
        logger.error(f"차트 데이터 생성 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization/odd-even-chart")
async def get_odd_even_chart():
    """홀짝 비율 차트 데이터"""
    try:
        df = data_service.load_data()
        odd_even_ratio = analysis_service.analyze_odd_even_ratio(df)
        
        chart_data = {
            "labels": ["홀수", "짝수"],
            "datasets": [{
                "label": "비율",
                "data": [odd_even_ratio["odd_ratio"], odd_even_ratio["even_ratio"]],
                "backgroundColor": ["rgba(255, 99, 132, 0.5)", "rgba(54, 162, 235, 0.5)"],
                "borderColor": ["rgba(255, 99, 132, 1)", "rgba(54, 162, 235, 1)"],
                "borderWidth": 1
            }]
        }
        
        return APIResponse(
            success=True,
            message="홀짝 비율 차트 데이터를 생성했습니다.",
            data=chart_data
        )
    except Exception as e:
        logger.error(f"홀짝 차트 데이터 생성 중 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disclaimer")
async def get_disclaimer():
    """법적 고지사항"""
    disclaimer = {
        "title": "중요한 고지사항",
        "content": [
            "본 서비스는 로또 번호 예측을 위한 참고 도구입니다.",
            "예측 결과는 실제 당첨을 보장하지 않습니다.",
            "로또는 완전한 확률 게임이며, 과학적 예측이 불가능합니다.",
            "건전한 복권 이용을 권장하며, 과도한 구매를 자제해 주세요.",
            "도박 중독 예방을 위해 적절한 금액으로 구매하시기 바랍니다.",
            "본 서비스는 개인정보를 수집하지 않습니다."
        ],
        "contact": "문의사항이 있으시면 개발자에게 연락해 주세요."
    }
    
    return APIResponse(
        success=True,
        message="고지사항을 조회했습니다.",
        data=disclaimer
    )
