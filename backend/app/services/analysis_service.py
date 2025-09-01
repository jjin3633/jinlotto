import os
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import calendar

logger = logging.getLogger(__name__)

class AnalysisService:
    """로또 데이터 통계 분석 서비스"""
    
    def __init__(self):
        self.number_columns = ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6']
        # 균형형 기본값(환경변수로 조정 가능)
        try:
            self.hot_cold_window = int(os.getenv('HOT_COLD_WINDOW', '40'))
        except Exception:
            self.hot_cold_window = 40
    
    def analyze_frequency(self, df: pd.DataFrame) -> Dict[int, int]:
        """번호별 출현 빈도 분석"""
        all_numbers = []
        for col in self.number_columns:
            all_numbers.extend(df[col].tolist())
        
        # Counter는 키/값에 numpy 타입이 포함될 수 있으므로 모두 파이썬 int로 캐스팅
        frequency = Counter(all_numbers)
        return {int(k): int(v) for k, v in frequency.items()}
    
    def find_hot_cold_numbers(self, df: pd.DataFrame, recent_draws: int = None) -> Tuple[List[int], List[int]]:
        """최근 회차 기준 핫/콜드 번호 분석"""
        if recent_draws is None:
            recent_draws = self.hot_cold_window
        recent_df = df.tail(recent_draws)
        recent_frequency = self.analyze_frequency(recent_df)
        
        # 전체 기간 빈도
        total_frequency = self.analyze_frequency(df)
        
        # 최근 출현 빈도가 높은 번호 (핫 번호)
        hot_numbers = sorted(recent_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
        hot_numbers = [num for num, freq in hot_numbers]
        
        # 최근 출현 빈도가 낮은 번호 (콜드 번호)
        cold_numbers = []
        for num in range(1, 46):
            if num not in recent_frequency:
                cold_numbers.append(num)
        
        return hot_numbers, cold_numbers
    
    def analyze_odd_even_ratio(self, df: pd.DataFrame) -> Dict[str, float]:
        """홀짝 비율 분석"""
        odd_count = 0
        even_count = 0
        total_numbers = 0
        
        for col in self.number_columns:
            odd_count += len(df[df[col] % 2 == 1])
            even_count += len(df[df[col] % 2 == 0])
            total_numbers += len(df)
        
        return {
            'odd_ratio': odd_count / total_numbers,
            'even_ratio': even_count / total_numbers
        }
    
    def analyze_number_ranges(self, df: pd.DataFrame) -> Dict[str, int]:
        """번호 구간별 분포 분석"""
        range_counts = defaultdict(int)
        
        for col in self.number_columns:
            for num in df[col]:
                if 1 <= num <= 10:
                    range_counts['1-10'] += 1
                elif 11 <= num <= 20:
                    range_counts['11-20'] += 1
                elif 21 <= num <= 30:
                    range_counts['21-30'] += 1
                elif 31 <= num <= 40:
                    range_counts['31-40'] += 1
                else:
                    range_counts['41-45'] += 1
        
        return dict(range_counts)
    
    def analyze_consecutive_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """연속 번호 패턴 분석"""
        patterns = []
        
        for _, row in df.iterrows():
            numbers = sorted([row[col] for col in self.number_columns])
            consecutive_count = 0
            max_consecutive = 0
            
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] == 1:
                    consecutive_count += 1
                else:
                    max_consecutive = max(max_consecutive, consecutive_count)
                    consecutive_count = 0
            
            max_consecutive = max(max_consecutive, consecutive_count)
            
            if max_consecutive > 0:
                patterns.append({
                    'draw_number': row['draw_number'],
                    'consecutive_count': max_consecutive,
                    'numbers': numbers
                })
        
        return patterns
    
    def analyze_missing_periods(self, df: pd.DataFrame) -> Dict[int, int]:
        """번호별 미출현 기간 분석"""
        missing_periods = {}
        
        for num in range(1, 46):
            last_appearance = None
            max_missing = 0
            current_missing = 0
            
            for _, row in df.iterrows():
                numbers = [row[col] for col in self.number_columns]
                if num in numbers:
                    if last_appearance is not None:
                        max_missing = max(max_missing, current_missing)
                    current_missing = 0
                    last_appearance = row['draw_number']
                else:
                    current_missing += 1
            
            missing_periods[num] = max_missing
        
        return missing_periods
    
    def analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """계절별 패턴 분석"""
        # 날짜 컬럼을 datetime으로 변환
        df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
        df['month'] = df['draw_date'].dt.month
        df['season'] = df['month'].apply(self._get_season)
        
        seasonal_analysis = {}
        
        for season in ['봄', '여름', '가을', '겨울']:
            season_df = df[df['season'] == season]
            if len(season_df) > 0:
                seasonal_analysis[season] = {
                    'draw_count': len(season_df),
                    'frequency': self.analyze_frequency(season_df),
                    'hot_numbers': self._get_top_numbers(season_df, 5),
                    'cold_numbers': self._get_cold_numbers(season_df, 5),
                    'odd_even_ratio': self.analyze_odd_even_ratio(season_df),
                    'range_distribution': self.analyze_number_ranges(season_df)
                }
        
        return seasonal_analysis
    
    def _get_season(self, month: int) -> str:
        """월을 계절로 변환"""
        if month in [3, 4, 5]:
            return '봄'
        elif month in [6, 7, 8]:
            return '여름'
        elif month in [9, 10, 11]:
            return '가을'
        else:
            return '겨울'
    
    def analyze_monthly_patterns(self, df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        """월별 패턴 분석"""
        df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
        df['month'] = df['draw_date'].dt.month
        
        monthly_analysis = {}
        
        for month in range(1, 13):
            month_df = df[df['month'] == month]
            if len(month_df) > 0:
                monthly_analysis[month] = {
                    'draw_count': len(month_df),
                    'frequency': self.analyze_frequency(month_df),
                    'hot_numbers': self._get_top_numbers(month_df, 5),
                    'cold_numbers': self._get_cold_numbers(month_df, 5),
                    'odd_even_ratio': self.analyze_odd_even_ratio(month_df),
                    'range_distribution': self.analyze_number_ranges(month_df)
                }
        
        return monthly_analysis
    
    def analyze_weekly_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """요일별 패턴 분석"""
        df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
        df['weekday'] = df['draw_date'].dt.day_name()
        
        weekly_analysis = {}
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for weekday in weekday_names:
            weekday_df = df[df['weekday'] == weekday]
            if len(weekday_df) > 0:
                weekly_analysis[weekday] = {
                    'draw_count': len(weekday_df),
                    'frequency': self.analyze_frequency(weekday_df),
                    'hot_numbers': self._get_top_numbers(weekday_df, 5),
                    'cold_numbers': self._get_cold_numbers(weekday_df, 5),
                    'odd_even_ratio': self.analyze_odd_even_ratio(weekday_df),
                    'range_distribution': self.analyze_number_ranges(weekday_df)
                }
        
        return weekly_analysis
    
    def analyze_date_patterns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """날짜별 패턴 분석 (1일~31일)"""
        df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
        df['day'] = df['draw_date'].dt.day
        
        date_analysis = {}
        
        for day in range(1, 32):
            day_df = df[df['day'] == day]
            if len(day_df) > 0:
                date_analysis[day] = {
                    'draw_count': len(day_df),
                    'frequency': self.analyze_frequency(day_df),
                    'hot_numbers': self._get_top_numbers(day_df, 3),
                    'cold_numbers': self._get_cold_numbers(day_df, 3),
                    'odd_even_ratio': self.analyze_odd_even_ratio(day_df)
                }
        
        return date_analysis
    
    def analyze_sum_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """번호 합계 패턴 분석"""
        sums = []
        for _, row in df.iterrows():
            numbers = [row[col] for col in self.number_columns]
            sums.append(sum(numbers))
        
        sum_counter = Counter(sums)
        return {
            'min_sum': int(min(sums)),
            'max_sum': int(max(sums)),
            'avg_sum': float(np.mean(sums)),
            'std_sum': float(np.std(sums)),
            'sum_distribution': {int(k): int(v) for k, v in sum_counter.items()},
            'most_common_sums': [(int(s), int(c)) for s, c in sum_counter.most_common(10)]
        }
    
    def analyze_gap_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """번호 간격 패턴 분석"""
        all_gaps = []
        
        for _, row in df.iterrows():
            numbers = sorted([row[col] for col in self.number_columns])
            gaps = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
            all_gaps.extend(gaps)
        
        gap_counter = Counter(all_gaps)
        return {
            'min_gap': int(min(all_gaps)),
            'max_gap': int(max(all_gaps)),
            'avg_gap': float(np.mean(all_gaps)),
            'std_gap': float(np.std(all_gaps)),
            'gap_distribution': {int(k): int(v) for k, v in gap_counter.items()},
            'most_common_gaps': [(int(g), int(c)) for g, c in gap_counter.most_common(10)]
        }
    
    def analyze_prime_number_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """소수 번호 패턴 분석"""
        prime_numbers = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]
        
        prime_counts = []
        for _, row in df.iterrows():
            numbers = [row[col] for col in self.number_columns]
            prime_count = len([n for n in numbers if n in prime_numbers])
            prime_counts.append(prime_count)
        
        prime_counter = Counter(prime_counts)
        return {
            'prime_numbers': [int(n) for n in prime_numbers],
            'avg_prime_count': float(np.mean(prime_counts)),
            'prime_count_distribution': {int(k): int(v) for k, v in prime_counter.items()},
            'most_common_prime_count': [(int(k), int(v)) for k, v in prime_counter.most_common()]
        }
    
    def analyze_ending_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """끝자리 패턴 분석"""
        ending_counts = Counter()
        
        for _, row in df.iterrows():
            numbers = [row[col] for col in self.number_columns]
            endings = [n % 10 for n in numbers]
            ending_counts.update(endings)
        
        return {
            'ending_distribution': dict(ending_counts),
            'most_common_endings': sorted(ending_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _get_top_numbers(self, df: pd.DataFrame, top_n: int = 5) -> List[int]:
        """가장 자주 나온 번호들 반환"""
        frequency = self.analyze_frequency(df)
        return [num for num, _ in sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:top_n]]
    
    def _get_cold_numbers(self, df: pd.DataFrame, top_n: int = 5) -> List[int]:
        """가장 적게 나온 번호들 반환"""
        frequency = self.analyze_frequency(df)
        return [num for num, _ in sorted(frequency.items(), key=lambda x: x[1])[:top_n]]
    
    def get_recent_trends(self, df: pd.DataFrame, recent_draws: int = 20) -> Dict[str, Any]:
        """최근 트렌드 분석"""
        recent_df = df.tail(recent_draws)
        
        trends = {
            'recent_frequency': self.analyze_frequency(recent_df),
            'recent_odd_even': self.analyze_odd_even_ratio(recent_df),
            'recent_ranges': self.analyze_number_ranges(recent_df),
            'avg_numbers_per_draw': recent_df[self.number_columns].mean().to_dict()
        }
        
        return trends
    
    def comprehensive_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """종합 분석 수행"""
        try:
            # 기본 분석
            frequency = self.analyze_frequency(df)
            hot_numbers, cold_numbers = self.find_hot_cold_numbers(df)
            odd_even_ratio = self.analyze_odd_even_ratio(df)
            range_distribution = self.analyze_number_ranges(df)
            consecutive_patterns = self.analyze_consecutive_patterns(df)
            missing_periods = self.analyze_missing_periods(df)
            recent_trends = self.get_recent_trends(df)
            
            # 새로운 세밀한 분석
            seasonal_patterns = self.analyze_seasonal_patterns(df)
            monthly_patterns = self.analyze_monthly_patterns(df)
            weekly_patterns = self.analyze_weekly_patterns(df)
            date_patterns = self.analyze_date_patterns(df)
            sum_patterns = self.analyze_sum_patterns(df)
            gap_patterns = self.analyze_gap_patterns(df)
            prime_patterns = self.analyze_prime_number_patterns(df)
            ending_patterns = self.analyze_ending_patterns(df)
            
            analysis_result = {
                'total_draws': len(df),
                'number_frequency': frequency,
                'hot_numbers': hot_numbers,
                'cold_numbers': cold_numbers,
                'odd_even_ratio': odd_even_ratio,
                'number_range_distribution': range_distribution,
                'consecutive_patterns': consecutive_patterns,
                'missing_periods': missing_periods,
            'recent_trends': recent_trends,
                
                # 새로운 세밀한 분석 결과
                'seasonal_analysis': seasonal_patterns,
                'monthly_analysis': monthly_patterns,
                'weekly_analysis': weekly_patterns,
                'date_analysis': date_patterns,
                'sum_analysis': sum_patterns,
                'gap_analysis': gap_patterns,
                'prime_analysis': prime_patterns,
                'ending_analysis': ending_patterns,
                
                'statistics': {
                    'most_frequent': list(max(frequency.items(), key=lambda x: x[1])),
                    'least_frequent': list(min(frequency.items(), key=lambda x: x[1])),
                    'avg_frequency': float(np.mean(list(frequency.values()))),
                    'std_frequency': float(np.std(list(frequency.values())))
                }
            }
            
            logger.info("강화된 종합 분석이 완료되었습니다.")
            return analysis_result
            
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {e}")
            raise
