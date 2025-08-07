import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import random

logger = logging.getLogger(__name__)

class PredictionService:
    """로또 번호 예측 서비스"""
    
    def __init__(self):
        self.models = {}
        self.number_columns = ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6']
    
    def statistical_prediction(self, df: pd.DataFrame, num_sets: int = 5) -> List[List[int]]:
        """통계 기반 번호 예측"""
        try:
            # 번호별 출현 빈도 계산
            frequency = self._calculate_frequency(df)
            
            # 가중치 기반 선택 (빈도가 높을수록 선택 확률 증가)
            weights = [frequency.get(i, 1) for i in range(1, 46)]
            
            predictions = []
            for _ in range(num_sets):
                # 가중치 기반으로 6개 번호 선택
                selected = random.choices(range(1, 46), weights=weights, k=6)
                # 중복 제거 및 정렬
                selected = sorted(list(set(selected)))
                # 6개가 되지 않으면 추가 선택
                while len(selected) < 6:
                    additional = random.choices(range(1, 46), weights=weights, k=1)[0]
                    if additional not in selected:
                        selected.append(additional)
                selected.sort()
                predictions.append(selected)
            
            return predictions
            
        except Exception as e:
            logger.error(f"통계 예측 중 오류 발생: {e}")
            raise
    
    def ml_prediction(self, df: pd.DataFrame, num_sets: int = 5) -> List[List[int]]:
        """머신러닝 기반 번호 예측"""
        try:
            # 특성 생성
            features = self._create_features(df)
            
            # 각 번호별로 모델 학습
            predictions = []
            for _ in range(num_sets):
                predicted_numbers = []
                
                for position in range(6):
                    # 해당 위치의 번호 예측
                    model = self._train_position_model(df, position)
                    if model is not None:
                        # 최근 데이터로 예측
                        recent_features = features.tail(1)
                        pred = model.predict(recent_features)[0]
                        # 1-45 범위로 제한
                        pred = max(1, min(45, int(round(pred))))
                        predicted_numbers.append(pred)
                    else:
                        # 모델 실패 시 랜덤 선택
                        predicted_numbers.append(random.randint(1, 45))
                
                # 중복 제거 및 정렬
                predicted_numbers = sorted(list(set(predicted_numbers)))
                while len(predicted_numbers) < 6:
                    additional = random.randint(1, 45)
                    if additional not in predicted_numbers:
                        predicted_numbers.append(additional)
                predicted_numbers.sort()
                predictions.append(predicted_numbers)
            
            return predictions
            
        except Exception as e:
            logger.error(f"ML 예측 중 오류 발생: {e}")
            # ML 실패 시 통계 예측으로 대체
            return self.statistical_prediction(df, num_sets)
    
    def hybrid_prediction(self, df: pd.DataFrame, num_sets: int = 5) -> List[List[int]]:
        """하이브리드 예측 (통계 + ML)"""
        try:
            # 통계 예측과 ML 예측을 결합
            statistical_preds = self.statistical_prediction(df, num_sets)
            ml_preds = self.ml_prediction(df, num_sets)
            
            # 두 방법의 결과를 교대로 사용
            hybrid_preds = []
            for i in range(num_sets):
                if i % 2 == 0:
                    hybrid_preds.append(statistical_preds[i // 2])
                else:
                    hybrid_preds.append(ml_preds[i // 2])
            
            return hybrid_preds
            
        except Exception as e:
            logger.error(f"하이브리드 예측 중 오류 발생: {e}")
            return self.statistical_prediction(df, num_sets)
    
    def _calculate_frequency(self, df: pd.DataFrame) -> Dict[int, int]:
        """번호별 출현 빈도 계산"""
        frequency = {}
        for col in self.number_columns:
            for num in df[col]:
                frequency[num] = frequency.get(num, 0) + 1
        return frequency
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """ML 모델을 위한 특성 생성"""
        features = df.copy()
        
        # 이동평균 추가
        for col in self.number_columns:
            features[f'{col}_ma5'] = features[col].rolling(window=5).mean()
            features[f'{col}_ma10'] = features[col].rolling(window=10).mean()
        
        # 번호별 출현 빈도 추가
        for num in range(1, 46):
            features[f'freq_{num}'] = 0
            for col in self.number_columns:
                features[f'freq_{num}'] += (features[col] == num).astype(int)
        
        # 홀짝 비율 추가
        features['odd_count'] = 0
        for col in self.number_columns:
            features['odd_count'] += (features[col] % 2 == 1).astype(int)
        
        # 결측치 처리
        features = features.fillna(0)
        
        return features
    
    def _train_position_model(self, df: pd.DataFrame, position: int) -> RandomForestRegressor:
        """특정 위치의 번호를 예측하는 모델 학습"""
        try:
            features = self._create_features(df)
            target = df[self.number_columns[position]]
            
            # 충분한 데이터가 있는지 확인
            if len(features) < 50:
                return None
            
            # 특성과 타겟 준비
            X = features.drop(['draw_number', 'draw_date', 'bonus_number'] + self.number_columns, axis=1, errors='ignore')
            y = target
            
            # 훈련/테스트 분할
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 모델 학습
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 모델 성능 평가
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"위치 {position} 모델 성능 - MSE: {mse:.2f}, R²: {r2:.2f}")
            
            return model
            
        except Exception as e:
            logger.error(f"위치 {position} 모델 학습 중 오류: {e}")
            return None
    
    def get_prediction_reasoning(self, method: str, analysis_result: Dict[str, Any]) -> List[str]:
        """예측 근거 생성"""
        reasoning = []
        
        if method == "statistical":
            reasoning.append("통계적 빈도 분석을 기반으로 한 예측입니다.")
            reasoning.append(f"가장 자주 출현한 번호: {analysis_result.get('statistics', {}).get('most_frequent', (0, 0))[0]}번")
            reasoning.append(f"최근 핫 번호: {analysis_result.get('hot_numbers', [])[:5]}")
            reasoning.append(f"콜드 번호: {analysis_result.get('cold_numbers', [])[:5]}")
        
        elif method == "ml":
            reasoning.append("머신러닝 모델을 통한 패턴 분석 기반 예측입니다.")
            reasoning.append("과거 데이터의 복잡한 패턴을 학습하여 예측했습니다.")
            reasoning.append("시계열 분석과 특성 엔지니어링을 활용했습니다.")
        
        else:  # hybrid
            reasoning.append("통계적 분석과 머신러닝을 결합한 하이브리드 예측입니다.")
            reasoning.append("두 방법의 장점을 모두 활용하여 예측 정확도를 높였습니다.")
        
        reasoning.append("⚠️ 이는 참고용이며, 실제 당첨을 보장하지 않습니다.")
        
        return reasoning
    
    def calculate_confidence_scores(self, method: str, num_sets: int) -> List[float]:
        """예측 신뢰도 점수 계산"""
        if method == "statistical":
            return [0.3] * num_sets  # 통계적 방법은 낮은 신뢰도
        elif method == "ml":
            return [0.4] * num_sets  # ML 방법은 중간 신뢰도
        else:  # hybrid
            return [0.35] * num_sets  # 하이브리드는 중간 신뢰도
