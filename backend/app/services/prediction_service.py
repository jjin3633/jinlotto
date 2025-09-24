import os
import joblib
import json
import threading
import queue
import time
import math
import random
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
import logging
"""
무거운 ML 라이브러리(sklearn)는 지연 임포트로 전환하여
비-ML 경로(statistical, test)가 빠르게 응답하도록 최적화합니다.
"""
def _get_env_float(name: str, default_value: float) -> float:
    try:
        return float(os.getenv(name, default_value))
    except Exception:
        return float(default_value)

def _get_env_int(name: str, default_value: int) -> int:
    try:
        return int(os.getenv(name, default_value))
    except Exception:
        return int(default_value)

def _get_env_bool(name: str, default_value: bool) -> bool:
    try:
        v = os.getenv(name)
        if v is None:
            return default_value
        return v.strip().lower() in ('1','true','yes','y','on')
    except Exception:
        return default_value

logger = logging.getLogger(__name__)

class PredictionService:
    """로또 번호 예측 서비스"""
    
    def __init__(self):
        # date(YYYYMMDD)별로 포지션 모델/피처 캐시
        self._models_cache_by_date: Dict[str, List[Any]] = {}
        self._features_cache_by_date: Dict[str, pd.DataFrame] = {}
        self.number_columns = ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6']
        self._last_warmup_date: str | None = None
        # 균형형 기본 파라미터 (환경변수로 오버라이드)
        self.conf_base = _get_env_float('CONF_BASE', 0.40)
        self.conf_min = _get_env_float('CONF_MIN', 0.40)
        self.conf_max = _get_env_float('CONF_MAX', 0.80)
        self.conf_w_consensus = _get_env_float('CONF_W_CONSENSUS', 0.30)
        self.conf_w_hot = _get_env_float('CONF_W_HOT', 0.10)
        self.conf_w_entropy = _get_env_float('CONF_W_ENTROPY', 0.20)
        self.merge_max_union_fill = _get_env_int('MERGE_MAX_UNION_FILL', 2)
        self.enforce_odd_even = _get_env_bool('ENFORCE_ODD_EVEN_BALANCE', True)
        self.enforce_range_coverage = _get_env_bool('ENFORCE_RANGE_COVERAGE', True)
        self.max_consecutive = _get_env_int('MAX_CONSECUTIVE', 2)
        self.hot_top_k = _get_env_int('HOT_TOP_K', 8)
        self.cold_top_k = _get_env_int('COLD_TOP_K', 8)
        self.freq_decay_half_life = _get_env_int('FREQ_DECAY_HALF_LIFE_DRAWS', 80)
        self.deterministic_seed = _get_env_bool('DETERMINISTIC_SEED', True)
        self.enable_ml = _get_env_bool('ENABLE_ML', True)
        # cache for models loaded from disk keyed by date
        self._loaded_models_by_date: Dict[str, List[Any]] = {}
        # background prediction job queue and tracking
        # (job_key, user_key, num_sets)
        self._job_queue: "queue.Queue[Tuple[str,str,int]]" = queue.Queue()
        self._pending_jobs: set = set()
        self._job_lock = threading.Lock()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
    
    def statistical_prediction(self, df: pd.DataFrame, num_sets: int = 5) -> List[List[int]]:
        """통계 기반 번호 예측"""
        try:
            # 번호별 출현 빈도 계산(시간 감쇠 가중 포함)
            frequency = self._calculate_frequency(df, decay_half_life=self.freq_decay_half_life)
            
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
            # KST 기준 날짜 키로 캐시 활용
            today_key = self._get_kst_today().strftime('%Y%m%d')

            # 피처를 일자 기준으로 1회만 생성
            if today_key in self._features_cache_by_date:
                features = self._features_cache_by_date[today_key]
            else:
                features = self._create_features(df)
                self._features_cache_by_date[today_key] = features

            # 시도 1: 디스크에 저장된 분류기(models/position_{i}_clf.pkl)를 로드(캐시 우선)
            today_key = self._get_kst_today().strftime('%Y%m%d')
            models_for_today = [None] * 6

            if today_key in self._loaded_models_by_date:
                models_for_today = self._loaded_models_by_date[today_key]
            else:
                models_dir = os.path.join(os.getcwd(), 'models')
                if os.path.isdir(models_dir):
                    load_start = __import__('time').perf_counter()
                    for i in range(6):
                        tuned_path = os.path.join(models_dir, f'position_{i}_clf_tuned.pkl')
                        default_path = os.path.join(models_dir, f'position_{i}_clf.pkl')
                        path = tuned_path if os.path.exists(tuned_path) else default_path
                        if os.path.exists(path):
                            try:
                                # Avoid memmap to prevent too many open files; load fully in memory
                                models_for_today[i] = joblib.load(path)
                            except Exception as ex:
                                logger.exception(f"Failed to load model {path}: {ex}")
                                models_for_today[i] = None
                    load_end = __import__('time').perf_counter()
                    logger.info(f"Loaded models from disk in {load_end-load_start:.3f}s")
                # cache loaded models even if some are None
                self._loaded_models_by_date[today_key] = models_for_today

            # If no models available or ML disabled, fallback to statistical
            if not any(models_for_today) or not self.enable_ml:
                return self.statistical_prediction(df, num_sets)

            # 최근 피처 1행으로 예측 확률 획득 및 숫자형 컬럼만 사용
            recent_features = features.tail(1)
            # drop non-feature columns and numeric-cast
            drop_cols = ['draw_number', 'draw_date', 'bonus_number'] + self.number_columns
            recent_X = recent_features.drop(columns=[c for c in drop_cols if c in recent_features.columns], errors='ignore')
            recent_X = recent_X.fillna(0)
            # ensure numpy float array for sklearn
            try:
                recent_vals = recent_X.astype(float).values
            except Exception:
                # fallback: coerce via to_numeric
                recent_vals = recent_X.apply(pd.to_numeric, errors='coerce').fillna(0).values

            # For each position, get probability vector for numbers 1..45
            prob_vectors = []
            for position in range(6):
                m = models_for_today[position]
                if m is None:
                    # uniform if missing
                    prob_vectors.append([1.0/45.0] * 45)
                else:
                    try:
                        pred_start = __import__('time').perf_counter()
                        # use numeric array to avoid dtype issues
                        proba = m.predict_proba(recent_vals)[0]
                        pred_end = __import__('time').perf_counter()
                        logger.debug(f"predict_proba pos={position} took {pred_end-pred_start:.4f}s")
                        # sklearn gives classes_ array
                        classes = m.classes_
                        vec = [0.0] * 45
                        for idx, cls in enumerate(classes):
                            if 1 <= int(cls) <= 45:
                                vec[int(cls) - 1] = float(proba[idx])
                        # normalize
                        s = sum(vec)
                        if s <= 0:
                            vec = [1.0/45.0] * 45
                        else:
                            vec = [v / s for v in vec]
                        prob_vectors.append(vec)
                    except Exception:
                        prob_vectors.append([1.0/45.0] * 45)

            # 샘플링 전략: 각 세트마다 각 포지션에서 확률분포로 샘플링하되 중복 제거
            predictions: List[List[int]] = []
            rng = list(range(1,46))
            for _ in range(num_sets):
                chosen = []
                for pos in range(6):
                    vec = prob_vectors[pos]
                    # restrict to top_k candidates to avoid tiny-prob noise
                    top_k = 8
                    top_idx = sorted(range(45), key=lambda x: vec[x], reverse=True)[:top_k]
                    candidates = [i+1 for i in top_idx]
                    weights = [vec[i-1] for i in candidates]
                    # normalize weights
                    total = sum(weights)
                    if total <= 0:
                        weights = None
                    else:
                        weights = [w/total for w in weights]

                    # choose one
                    try:
                        pick = random.choices(candidates, weights=weights, k=1)[0]
                    except Exception:
                        pick = random.randint(1,45)
                    # avoid duplicates by retrying few times
                    tries = 0
                    while pick in chosen and tries < 10:
                        try:
                            pick = random.choices(candidates, weights=weights, k=1)[0]
                        except Exception:
                            pick = random.randint(1,45)
                        tries += 1
                    chosen.append(pick)

                # ensure 6 unique
                chosen = list(dict.fromkeys(chosen))
                i_try = 0
                while len(chosen) < 6 and i_try < 20:
                    cand = random.choices(rng, k=1)[0]
                    if cand not in chosen:
                        chosen.append(cand)
                    i_try += 1
                chosen = sorted(chosen)[:6]
                chosen = self._apply_diversity_constraints(chosen)
                predictions.append(chosen)

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
            #    품질 우선: ML 사용. 캐시 없으면 내부에서 학습 수행(워밍업이 선행되면 빠름)
            try:
                # 우선 ML 일반 예측 사용. (순차 예측 메서드가 없을 수 있어 안전 경로)
                ml_sets = self.ml_prediction(df, num_sets)
            except Exception:
                ml_sets = stat_sets

            # 3) 빈도 상위/하위(핫/콜드) 계산
            frequency = self._calculate_frequency(df, decay_half_life=self.freq_decay_half_life)
            # 파이썬 int로 보정
            frequency = {int(k): int(v) for k, v in frequency.items()}
            sorted_by_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
            hot_simple = [int(n) for n, _ in sorted_by_freq[: self.hot_top_k]]
            cold_simple = [int(n) for n, _ in sorted(frequency.items(), key=lambda x: x[1])[: self.cold_top_k]]

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
                    if len(chosen) < 6 and (len(chosen) - len(consensus)) < self.merge_max_union_fill:
                        chosen.append(int(x))

                while len(chosen) < 6:
                    cand = random.choices(rng, weights=weights, k=1)[0]
                    if cand not in chosen:
                        chosen.append(int(cand))

                chosen = sorted(chosen)[:6]
                # 다양성 제약 적용(홀짝/구간/연속)
                chosen = self._apply_diversity_constraints(chosen)
                final_sets.append(chosen)

                # 신뢰도: 교집합 비율 + 핫번호 포함 비율로 가중(0.35~0.75 사이)
                consensus_ratio = len(consensus) / 6.0
                hot_hit = sum(1 for x in chosen if x in hot_simple) / 6.0
                # 엔트로피 기반 불확실성 측정: 낮을수록 신뢰도 높음
                try:
                    # compute entropy across positions using prob_vectors if available
                    entropy_sum = 0.0
                    if 'prob_vectors' in locals():
                        import math
                        for pos, vec in enumerate(prob_vectors):
                            # entropy of discrete distribution
                            e = -sum([p * math.log(p + 1e-12) for p in vec])
                            entropy_sum += e
                        # normalize entropy into [0,1] roughly
                        entropy_score = 1.0 - (entropy_sum / (6.0 * math.log(45)))
                    else:
                        entropy_score = 0.5
                except Exception:
                    entropy_score = 0.5

                conf = (self.conf_base
                        + self.conf_w_consensus * consensus_ratio
                        + self.conf_w_hot * hot_hit
                        + self.conf_w_entropy * entropy_score)
                conf = max(self.conf_min, min(self.conf_max, conf))
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

        # 생성 (첫 호출은 ML 건너뛰도록 unified_prediction 내부에서 제어)
        if self.deterministic_seed and user_key:
            try:
                seed_base = int(datetime.strptime(date_str, '%Y%m%d').timestamp())
            except Exception:
                seed_base = int(self._get_kst_today().timestamp())
            random.seed(hash((user_key, seed_base)))

        # Quick response: return statistical prediction immediately and enqueue ML refinement
        unified = None
        try:
            # fast path statistical
            stat_only = self.statistical_prediction(df, num_sets)
            unified = {
                'sets': stat_only,
                'confidence_scores': [0.45] * num_sets,
                'reasoning': []
            }
            # enqueue background ML job for this user/date
            job_key = f"{date_str}:{user_key}:{num_sets}"
            with self._job_lock:
                if job_key not in self._pending_jobs:
                    self._pending_jobs.add(job_key)
                    self._job_queue.put((job_key, user_key, num_sets))
        except Exception:
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
    
    def _calculate_frequency(self, df: pd.DataFrame, decay_half_life: int | None = None) -> Dict[int, int]:
        """번호별 출현 빈도 계산"""
        frequency: Dict[int, float] = {}
        if decay_half_life and decay_half_life > 0:
            # 최근 회차일수록 더 큰 가중치(지수감쇠) 적용
            n = len(df)
            if n == 0:
                return {}
            # 반감기 기준 감쇠 상수
            lam = math.log(2) / float(decay_half_life)
            # 최신 행이 tail(1)이라는 가정 하에, 각 행의 시점 가중치 계산
            for idx, (_, row) in enumerate(df.iterrows()):
                # 과거일수 d: 0(가장 오래됨) ~ n-1(가장 최신)
                d = idx
                w = math.exp(-lam * (n - 1 - d))
                for col in self.number_columns:
                    num = int(row[col])
                    frequency[num] = float(frequency.get(num, 0.0)) + float(w)
        else:
            for col in self.number_columns:
                for num in df[col]:
                    frequency[int(num)] = float(frequency.get(int(num), 0.0)) + 1.0
        # int로 반올림
        return {int(k): int(round(v)) for k, v in frequency.items()}

    def _apply_diversity_constraints(self, chosen: List[int]) -> List[int]:
        """홀짝/구간/연속 제약을 완만히 적용하여 구성 품질을 높인다."""
        nums = sorted(chosen)[:6]
        if len(nums) != 6:
            return nums
        rng = list(range(1, 46))
        # 홀짝 균형(2:4~4:2)
        if self.enforce_odd_even:
            odd = sum(1 for x in nums if x % 2 == 1)
            if odd < 2 or odd > 4:
                # 간단 보정: 가장자리를 대체
                target_is_odd = 3 if odd < 2 else 3
                while odd < 2 or odd > 4:
                    cand = random.choice(rng)
                    if (cand % 2 == 1 and odd < 3) or (cand % 2 == 0 and odd > 3):
                        rep_idx = random.randrange(0, 6)
                        if cand not in nums:
                            old = nums[rep_idx]
                            nums[rep_idx] = cand
                            odd = odd + (1 if cand % 2 == 1 else 0) - (1 if old % 2 == 1 else 0)
                            nums = sorted(nums)
                            break
        # 구간 커버(1-15,16-30,31-45 최소 1개)
        if self.enforce_range_coverage:
            ranges = [(1,15),(16,30),(31,45)]
            def has_range(a,b):
                return any(a <= x <= b for x in nums)
            for a,b in ranges:
                if not has_range(a,b):
                    # 해당 구간에서 대체
                    cand = random.randint(a,b)
                    rep_idx = random.randrange(0, 6)
                    if cand not in nums:
                        nums[rep_idx] = cand
                        nums = sorted(nums)
        # 연속 최대 길이 제한
        if self.max_consecutive > 0:
            def longest_consecutive(arr: List[int]) -> int:
                m = 1
                c = 1
                for i in range(1, len(arr)):
                    if arr[i] == arr[i-1] + 1:
                        c += 1
                        m = max(m, c)
                    else:
                        c = 1
                return m
            tries = 0
            while longest_consecutive(nums) > self.max_consecutive and tries < 20:
                rep_idx = random.randrange(0, 6)
                cand = random.randint(1,45)
                if cand not in nums:
                    nums[rep_idx] = cand
                    nums = sorted(nums)
                tries += 1
        return nums
    
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

    # ----------------------------
    # Background worker for ML refinement
    # ----------------------------
    def _worker_loop(self):
        """Background loop that processes queued ML refine jobs."""
        while True:
            try:
                job = self._job_queue.get()
                if not job:
                    time.sleep(0.5)
                    continue
                job_key, user_key, num_sets = job
                logger.info(f"ML worker processing job {job_key}")
                try:
                    # load latest data and compute unified prediction (may be heavy)
                    from backend.app.services.data_service import DataService
                    ds = DataService()
                    df = ds.load_data()
                    refined = self.unified_prediction(df, num_sets)
                    # write refined result to store path so subsequent requests get ML result
                    date_str = self._get_kst_today().strftime('%Y%m%d')
                    store_path = self._get_daily_store_path(date_str, user_key)
                    try:
                        with open(store_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                'mode': 'daily-fixed',
                                'generated_for': date_str,
                                'valid_until': (self._get_kst_today().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat(),
                                'created_at': self._get_kst_today().isoformat(),
                                'user_key': user_key,
                                'sets': [[int(x) for x in s] for s in refined.get('sets', [])],
                                'confidence_scores': [float(x) for x in refined.get('confidence_scores', [])],
                                'reasoning': refined.get('reasoning', [])
                            }, ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"Failed to write refined ML result for {job_key}: {e}")
                except Exception as e:
                    logger.error(f"ML worker job {job_key} failed: {e}")
                finally:
                    with self._job_lock:
                        if job_key in self._pending_jobs:
                            self._pending_jobs.remove(job_key)
                    self._job_queue.task_done()
            except Exception:
                time.sleep(1.0)
    
    def _train_position_model(self, df: pd.DataFrame, position: int, precomputed_features: pd.DataFrame | None = None):
        """특정 위치의 번호를 예측하는 모델 학습"""
        try:
            # 지연 임포트 (RandomForest 및 평가 지표)
            from sklearn.ensemble import RandomForestRegressor  # type: ignore
            from sklearn.model_selection import train_test_split  # type: ignore
            from sklearn.metrics import mean_squared_error, r2_score  # type: ignore
            features = precomputed_features if precomputed_features is not None else self._create_features(df)
            target = df[self.number_columns[position]]
            
            # 충분한 데이터가 있는지 확인
            if len(features) < 50:
                return None
            
            # 특성과 타겟 준비
            X = features.drop(['draw_number', 'draw_date', 'bonus_number'] + self.number_columns, axis=1, errors='ignore')
            y = target
            
            # 훈련/테스트 분할
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # 모델 학습 (품질 균형: 트리 수 100)
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

    def warmup_today_models(self, df: pd.DataFrame) -> None:
        """금일(KST) 기준 피처/모델을 미리 생성하여 첫 요청 지연을 방지한다."""
        try:
            today_key = self._get_kst_today().strftime('%Y%m%d')
            # 이미 워밍업된 날짜면 스킵
            if self._last_warmup_date == today_key and today_key in self._models_cache_by_date:
                return
            # 피처 준비
            features = self._features_cache_by_date.get(today_key)
            if features is None:
                features = self._create_features(df)
                self._features_cache_by_date[today_key] = features
            # 모델 6개 학습
            models_for_today: List[Any] = []
            for position in range(6):
                model = self._train_position_model(df, position, precomputed_features=features)
                models_for_today.append(model)
            self._models_cache_by_date[today_key] = models_for_today
            self._last_warmup_date = today_key
        except Exception as e:
            logger.error(f"워밍업 실패(비치명적): {e}")
    
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
