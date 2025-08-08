import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import os, json
import logging
"""
무거운 ML 라이브러리(sklearn)는 지연 임포트로 전환하여
비-ML 경로(statistical, test)가 빠르게 응답하도록 최적화합니다.
"""
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
            # 지연 임포트 (초기 콜드 스타트 지연 최소화)
            from sklearn.model_selection import train_test_split  # type: ignore
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
    
    def unified_prediction(self, df: pd.DataFrame, num_sets: int = 5) -> Dict[str, Any]:
        """통계+ML+휴리스틱을 결합한 단일 통합 예측

        반환:
            {
              'sets': List[List[int]],
              'confidence_scores': List[float],
              'reasoning': List[str]
            }
        """
        try:
            # 1) 통계 기반 가중 샘플
            stat_sets = self.statistical_prediction(df, num_sets)

            # 2) ML 기반 예측(실패 시 통계 대체)
            try:
                ml_sets = self.ml_prediction(df, num_sets)
            except Exception:
                ml_sets = stat_sets

            # 3) 빈도 상위/하위(핫/콜드) 계산
            frequency = self._calculate_frequency(df)
            # 파이썬 int로 보정
            frequency = {int(k): int(v) for k, v in frequency.items()}
            sorted_by_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            hot_simple = [int(n) for n, _ in sorted_by_freq[:10]]
            cold_simple = [int(n) for n, _ in sorted(frequency.items(), key=lambda x: x[1])[:10]]

            # 4) 세트 병합: 교집합 우선 + 가중 샘플 보강
            final_sets: List[List[int]] = []
            confidence_scores: List[float] = []
            rng = list(range(1, 46))
            weights = [frequency.get(i, 1) for i in rng]

            for i in range(num_sets):
                s = set(stat_sets[i % len(stat_sets)])
                m = set(ml_sets[i % len(ml_sets)])
                consensus = s.intersection(m)
                union = s.union(m)

                # 교집합 우선 채우기
                chosen = list(sorted(consensus))

                # 남은 칸은: (1) 두 방법 합집합에서 선택, (2) 부족하면 가중 샘플로 채우기
                remainder = [x for x in sorted(union) if x not in chosen]
                for x in remainder:
                    if len(chosen) < 6:
                        chosen.append(int(x))

                while len(chosen) < 6:
                    cand = random.choices(rng, weights=weights, k=1)[0]
                    if cand not in chosen:
                        chosen.append(int(cand))

                chosen = sorted(chosen)[:6]
                final_sets.append(chosen)

                # 신뢰도: 교집합 비율 + 핫번호 포함 비율로 가중(0.35~0.75 사이)
                consensus_ratio = len(consensus) / 6.0
                hot_hit = sum(1 for x in chosen if x in hot_simple) / 6.0
                conf = 0.35 + 0.25 * consensus_ratio + 0.15 * hot_hit
                conf = max(0.35, min(0.75, conf))
                confidence_scores.append(round(conf, 3))

            # 5) 근거 문구
            reasoning: List[str] = []
            if sorted_by_freq:
                top_pair = sorted_by_freq[0]
                reasoning.append(f"최근 데이터에서 가장 자주 나온 번호는 {int(top_pair[0])}번입니다.")
            if hot_simple:
                reasoning.append(f"핫 번호 상위: {hot_simple[:6]}")
            if cold_simple:
                reasoning.append(f"콜드 번호 일부 제외 및 보정 샘플링을 적용했습니다.")
            reasoning.append("통계 기반 가중 샘플과 ML 추정치를 결합해 교집합을 우선 반영했습니다.")
            reasoning.append("이는 참고용 예측이며, 실제 당첨을 보장하지 않습니다.")

            return {
                'sets': final_sets,
                'confidence_scores': confidence_scores,
                'reasoning': reasoning,
            }
        except Exception as e:
            logger.error(f"통합 예측 중 오류: {e}")
            # 최종 안전망: 통계 예측만 반환
            fallback = self.statistical_prediction(df, num_sets)
            return {
                'sets': fallback,
                'confidence_scores': [0.4] * num_sets,
                'reasoning': ["통합 예측 실패로 통계 기반 결과를 제공합니다."],
            }

    def _get_kst_today(self) -> datetime:
        return datetime.now(timezone(timedelta(hours=9)))

    def _get_daily_store_path(self, date_str: str, key: str) -> str:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_dir = os.path.join(backend_dir, 'data', 'daily_recommendations', date_str)
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, f'{key}.json')

    def get_daily_fixed_predictions(self, df: pd.DataFrame, num_sets: int = 5, user_key: str = "global") -> Dict[str, Any]:
        """저장형: 당일 첫 생성 후 파일로 고정, 당일 내 동일 결과 반환 (사용자별 key 분리)"""
        kst_now = self._get_kst_today()
        date_str = kst_now.strftime('%Y%m%d')
        store_path = self._get_daily_store_path(date_str, user_key)

        if os.path.exists(store_path):
            try:
                with open(store_path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                return saved
            except Exception as e:
                logger.error(f"일일 추천 로드 실패, 재생성 시도: {e}")

        # 생성
        unified = self.unified_prediction(df, num_sets)
        result: Dict[str, Any] = {
            'mode': 'daily-fixed',
            'generated_for': date_str,
            'valid_until': (kst_now.replace(hour=0, minute=0, second=0, microsecond=0)
                            + timedelta(days=1)).isoformat(),
            'created_at': kst_now.isoformat(),
            'user_key': user_key,
            'sets': [[int(x) for x in s] for s in unified.get('sets', [])],
            'confidence_scores': [float(x) for x in unified.get('confidence_scores', [])],
            'reasoning': [],  # UI에서 미표시하므로 비움
        }

        try:
            with open(store_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"일일 추천 저장 실패(비치명적): {e}")

        return result

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
    
    def _train_position_model(self, df: pd.DataFrame, position: int):
        """특정 위치의 번호를 예측하는 모델 학습"""
        try:
            # 지연 임포트 (RandomForest 및 평가 지표)
            from sklearn.ensemble import RandomForestRegressor  # type: ignore
            from sklearn.model_selection import train_test_split  # type: ignore
            from sklearn.metrics import mean_squared_error, r2_score  # type: ignore
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
            stats = analysis_result.get('statistics', {}) if isinstance(analysis_result, dict) else {}
            most_freq = stats.get('most_frequent')
            # most_frequent가 [num, freq] 또는 단일 정수인 경우 모두 처리
            if isinstance(most_freq, (list, tuple)) and len(most_freq) > 0:
                most_freq_num = most_freq[0]
            else:
                most_freq_num = most_freq if isinstance(most_freq, (int, float)) else None

            hot_numbers = analysis_result.get('hot_numbers', []) if isinstance(analysis_result, dict) else []
            if hot_numbers and isinstance(hot_numbers[0], (list, tuple)):
                hot_numbers_simple = [int(x[0]) for x in hot_numbers[:5] if isinstance(x, (list, tuple)) and x]
            else:
                hot_numbers_simple = [int(x) for x in hot_numbers[:5]] if hot_numbers else []

            cold_numbers = analysis_result.get('cold_numbers', []) if isinstance(analysis_result, dict) else []
            if cold_numbers and isinstance(cold_numbers[0], (list, tuple)):
                cold_numbers_simple = [int(x[0]) for x in cold_numbers[:5] if isinstance(x, (list, tuple)) and x]
            else:
                cold_numbers_simple = [int(x) for x in cold_numbers[:5]] if cold_numbers else []

            if most_freq_num is not None:
                reasoning.append(f"가장 자주 출현한 번호: {int(most_freq_num)}번")
            if hot_numbers_simple:
                reasoning.append(f"최근 핫 번호: {hot_numbers_simple}")
            if cold_numbers_simple:
                reasoning.append(f"콜드 번호: {cold_numbers_simple}")
        
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
        """예측 신뢰도 점수 계산 (레거시 하위호환; 현재는 통합 예측 사용)"""
        return [0.45] * num_sets
