import pandas as pd
import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
import time

logger = logging.getLogger(__name__)

class DataService:
    """로또 데이터 수집 및 전처리 서비스"""
    
    def __init__(self):
        self.base_url = "https://www.dhlottery.co.kr/common.do"
        # backend 디렉토리 기준 절대 경로로 고정 (배포/로컬 모두 일관)
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_file = os.path.join(backend_root, "data", "lotto_data.csv")
        
    def collect_lotto_data(self, start_draw: int = 1, end_draw: int = None) -> pd.DataFrame:
        """동행복권 API에서 로또 데이터 수집"""
        try:
            if end_draw is None:
                # 최신 회차 확인
                end_draw = self._get_latest_draw_number()
            
            data = []
            logger.info(f"로또 데이터 수집 시작: {start_draw}회차 ~ {end_draw}회차")
            
            for draw_no in range(start_draw, end_draw + 1):
                try:
                    draw_data = self._fetch_draw_data(draw_no)
                    if draw_data:
                        data.append(draw_data)
                        logger.info(f"{draw_no}회차 데이터 수집 완료")
                    else:
                        logger.warning(f"{draw_no}회차 데이터 없음")
                    
                    # API 호출 간격 조절 (서버 부하 방지)
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"{draw_no}회차 데이터 수집 실패: {e}")
                    continue
            
            if not data:
                logger.warning("수집된 데이터가 없습니다. 샘플 데이터를 생성합니다.")
                return self._generate_sample_data()
            
            df = pd.DataFrame(data)
            logger.info(f"총 {len(df)}회차 데이터 수집 완료")
            return df
            
        except Exception as e:
            logger.error(f"데이터 수집 중 오류 발생: {e}")
            logger.info("샘플 데이터로 대체합니다.")
            return self._generate_sample_data()
    
    def _fetch_draw_data(self, draw_no: int) -> Optional[Dict]:
        """특정 회차의 로또 데이터 가져오기"""
        try:
            url = f"{self.base_url}?method=getLottoNumber&drwNo={draw_no}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('returnValue') == 'success':
                return {
                    'draw_number': data['drwNo'],
                    'draw_date': data['drwNoDate'],
                    'number_1': data['drwtNo1'],
                    'number_2': data['drwtNo2'],
                    'number_3': data['drwtNo3'],
                    'number_4': data['drwtNo4'],
                    'number_5': data['drwtNo5'],
                    'number_6': data['drwtNo6'],
                    'bonus_number': data['bnusNo'],
                    'total_sales': data.get('totSellamnt', 0),
                    'first_prize_amount': data.get('firstWinamnt', 0),
                    'first_prize_winners': data.get('firstPrzwnerCo', 0)
                }
            else:
                logger.warning(f"{draw_no}회차: 유효하지 않은 응답")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"{draw_no}회차 API 호출 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"{draw_no}회차 데이터 파싱 실패: {e}")
            return None
    
    def _get_latest_draw_number(self) -> int:
        """최신 회차 번호 확인"""
        try:
            # 최근 회차부터 역순으로 확인
            for draw_no in range(1200, 1100, -1):  # 1200회차부터 역순 확인
                data = self._fetch_draw_data(draw_no)
                if data:
                    logger.info(f"최신 회차: {draw_no}회차")
                    return draw_no
            
            # 기본값 반환
            logger.warning("최신 회차 확인 실패, 기본값 1000 사용")
            return 1000
            
        except Exception as e:
            logger.error(f"최신 회차 확인 중 오류: {e}")
            return 1000
    
    def _generate_sample_data(self) -> pd.DataFrame:
        """샘플 로또 데이터 생성 (API 실패 시 사용)"""
        import random
        from datetime import datetime, timedelta
        
        logger.info("샘플 데이터 생성 중...")
        data = []
        start_date = datetime(2002, 12, 7)  # 로또 시작일
        
        for i in range(1, 1001):  # 1000회차 샘플 데이터
            draw_date = start_date + timedelta(days=i*7)
            numbers = sorted(random.sample(range(1, 46), 6))
            bonus = random.randint(1, 45)
            
            data.append({
                'draw_number': i,
                'draw_date': draw_date.strftime('%Y-%m-%d'),
                'number_1': numbers[0],
                'number_2': numbers[1],
                'number_3': numbers[2],
                'number_4': numbers[3],
                'number_5': numbers[4],
                'number_6': numbers[5],
                'bonus_number': bonus,
                'total_sales': random.randint(100000000000, 200000000000),
                'first_prize_amount': random.randint(1000000000, 3000000000),
                'first_prize_winners': random.randint(1, 20)
            })
        
        return pd.DataFrame(data)
    
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리"""
        try:
            # 결측치 확인
            missing_data = df.isnull().sum()
            logger.info(f"결측치 현황:\n{missing_data}")
            
            # 중복 확인
            duplicates = df.duplicated().sum()
            logger.info(f"중복 데이터: {duplicates}개")
            
            # 데이터 타입 변환
            # 다양한 포맷 혼재 대비: pandas 2.x의 mixed 포맷 허용 + 안전하게 coerce
            df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
            
            # 이상치 탐지 (1-45 범위 확인)
            for col in ['number_1', 'number_2', 'number_3', 'number_4', 'number_5', 'number_6', 'bonus_number']:
                invalid_numbers = df[(df[col] < 1) | (df[col] > 45)]
                if not invalid_numbers.empty:
                    logger.warning(f"{col}에서 이상치 발견: {len(invalid_numbers)}개")
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류 발생: {e}")
            raise
    
    def save_data(self, df: pd.DataFrame, filename: str = None) -> str:
        """데이터를 CSV 파일로 저장"""
        if filename is None:
            filename = self.data_file
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"데이터가 {filename}에 저장되었습니다.")
        return filename
    
    def load_data(self, filename: str = None) -> pd.DataFrame:
        """CSV 파일에서 데이터 로드"""
        if filename is None:
            filename = self.data_file
        
        if os.path.exists(filename):
            df = pd.read_csv(filename, encoding='utf-8')
            # 다양한 포맷 혼재 대비
            df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
            return df
        else:
            # 초기 배포 등 첫 실행에서는 수집이 매우 오래 걸릴 수 있으므로, 우선 샘플 데이터로 즉시 응답
            logger.warning(f"파일 {filename}이 존재하지 않습니다. 우선 샘플 데이터로 대체합니다.")
            return self._generate_sample_data()
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """데이터 요약 정보 반환"""
        try:
            # draw_date가 문자열로 남아있을 경우 안전 변환
            if not pd.api.types.is_datetime64_any_dtype(df['draw_date']):
                df = df.copy()
                try:
                    df['draw_date'] = pd.to_datetime(df['draw_date'], format='mixed', errors='coerce')
                except Exception:
                    df['draw_date'] = pd.to_datetime(df['draw_date'], errors='coerce')
            latest_row = df.iloc[-1]
            # JSON 직렬화 가능한 기본형으로 캐스팅
            missing_values = {k: int(v) for k, v in df.isnull().sum().to_dict().items()}
            duplicates = int(df.duplicated().sum())

            latest_draw = {
                'draw_number': int(latest_row['draw_number']),
                'draw_date': latest_row['draw_date'].strftime('%Y-%m-%d'),
                'number_1': int(latest_row['number_1']),
                'number_2': int(latest_row['number_2']),
                'number_3': int(latest_row['number_3']),
                'number_4': int(latest_row['number_4']),
                'number_5': int(latest_row['number_5']),
                'number_6': int(latest_row['number_6']),
                'bonus_number': int(latest_row['bonus_number'])
            }

            return {
                'total_draws': int(len(df)),
                'date_range': {
                    'start': df['draw_date'].min().strftime('%Y-%m-%d'),
                    'end': df['draw_date'].max().strftime('%Y-%m-%d')
                },
                'missing_values': missing_values,
                'duplicates': duplicates,
                'latest_draw': latest_draw
            }
        except Exception as e:
            logger.error(f"데이터 요약 생성 중 오류: {e}")
            return {
                'total_draws': len(df),
                'date_range': {'start': 'N/A', 'end': 'N/A'},
                'missing_values': {},
                'duplicates': 0,
                'latest_draw': {}
            }
    
    def update_latest_data(self) -> pd.DataFrame:
        """최신 데이터만 업데이트"""
        try:
            # 기존 데이터 로드
            existing_df = self.load_data()
            latest_draw = existing_df['draw_number'].max()
            
            # 최신 회차 확인
            current_latest = self._get_latest_draw_number()
            
            if current_latest > latest_draw:
                logger.info(f"새로운 데이터 발견: {latest_draw + 1}회차 ~ {current_latest}회차")
                new_data = self.collect_lotto_data(latest_draw + 1, current_latest)
                
                if not new_data.empty:
                    # 기존 데이터와 병합
                    updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                    updated_df = updated_df.sort_values('draw_number').reset_index(drop=True)
                    # 날짜 컬럼 일괄 보정
                    try:
                        updated_df['draw_date'] = pd.to_datetime(updated_df['draw_date'], format='mixed', errors='coerce')
                    except Exception:
                        updated_df['draw_date'] = pd.to_datetime(updated_df['draw_date'], errors='coerce')
                    
                    # 저장
                    self.save_data(updated_df)
                    logger.info(f"데이터 업데이트 완료: {len(new_data)}회차 추가")
                    return updated_df
                else:
                    logger.info("새로운 데이터가 없습니다.")
                    return existing_df
            else:
                logger.info("이미 최신 데이터입니다.")
                return existing_df
                
        except Exception as e:
            logger.error(f"데이터 업데이트 중 오류: {e}")
            return self.load_data()
