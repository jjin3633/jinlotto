from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class LottoNumber(BaseModel):
    """로또 번호 모델"""
    number: int
    frequency: int
    last_appearance: Optional[str] = None
    consecutive_count: int = 0

class LottoDraw(BaseModel):
    """로또 추첨 결과 모델"""
    draw_number: int
    draw_date: str
    numbers: List[int]
    bonus_number: int

class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    total_draws: int
    number_frequency: Dict[int, int]
    hot_numbers: List[int]
    cold_numbers: List[int]
    odd_even_ratio: Dict[str, float]
    number_range_distribution: Dict[str, int]
    consecutive_patterns: List[Dict[str, Any]]

class PredictionRequest(BaseModel):
    """예측 요청 모델"""
    method: str = "statistical"  # statistical, ml, hybrid
    num_sets: int = 5
    include_bonus: bool = False
    nickname: Optional[str] = None  # 닉네임 추가

class PredictionResult(BaseModel):
    """예측 결과 모델"""
    sets: List[List[int]]
    confidence_scores: List[float]
    reasoning: List[str]
    analysis_summary: str
    disclaimer: str

class VisualizationData(BaseModel):
    """시각화 데이터 모델"""
    chart_type: str
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None

class APIResponse(BaseModel):
    """API 응답 기본 모델"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
