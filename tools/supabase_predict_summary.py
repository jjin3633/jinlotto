# 파일: tools/supabase_predict_summary.py
# 목적: Supabase에 저장된 최신 회차의 예측 데이터를 기반으로 1~5등 요약을 계산
# 의존성: pip install supabase-py

import os
from typing import List, Dict, Optional
from supabase import create_client


def _extract_draw_numbers(draw_row: dict) -> Optional[List[int]]:
    """로또 추첨 번호 6개를 추출합니다. 여러 스키마를 유연하게 지원합니다."""
    # 기본 형식: number_1 ~ number_6
    nums: List[int] = []
    for i in range(1, 7):
        key = f"number_{i}"
        if key in draw_row and draw_row[key] is not None:
            try:
                nums.append(int(draw_row[key]))
            except ValueError:
                pass
    if len(nums) == 6:
        return nums
    # 대안 형식: drwtNo1 ~ drwtNo6 (한국 로또 API 스타일)
    nums = []
    for i in range(1, 7):
        key = f"drwtNo{i}"
        if key in draw_row and draw_row[key] is not None:
            try:
                nums.append(int(draw_row[key]))
            except ValueError:
                pass
    if len(nums) == 6:
        return nums
    return None


def _compute_rank(user_numbers: List[int], draw_numbers: List[int], bonus_number: int) -> int:
    user_set = set(user_numbers)
    draw_set = set(draw_numbers)
    matched = sorted(list(user_set & draw_set))
    match_count = len(matched)
    bonus_match = int(bonus_number) in user_set

    if match_count == 6:
        return 1
    if match_count == 5 and bonus_match:
        return 2
    if match_count == 5:
        return 3
    if match_count == 4:
        return 4
    if match_count == 3:
        return 5
    return 0


def main() -> None:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("ENV에 SUPABASE_URL 혹은 SUPABASE_ANON_KEY가 설정되지 않았습니다.")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # 최신 회차 조회
    latest_draw_res = supabase.from_('draws').select('*').order('draw_number', desc=True).limit(1).execute()
    if not latest_draw_res.data:
        print("최신 회차 정보를 Supabase에서 찾을 수 없습니다.")
        return
    latest_draw = latest_draw_res.data[0]

    draw_numbers = _extract_draw_numbers(latest_draw)
    if not draw_numbers:
        print("최신 회차 데이터에서 번호를 추출할 수 없습니다.")
        return
    bonus_number = int(latest_draw.get('bonus_number', 0))
    latest_draw_number = int(latest_draw.get('draw_number'))

    # 예측 데이터 조회
    preds_res = supabase.from_('predictions').select('*').execute()
    preds = preds_res.data if preds_res and preds_res.data else []

    counts: Dict[int, int] = {1:0, 2:0, 3:0, 4:0, 5:0}

    for pred in preds:
        nums = pred.get('numbers')
        if isinstance(nums, list) and len(nums) >= 6:
            user_numbers = [int(x) for x in nums[:6]]
            rank = _compute_rank(user_numbers, draw_numbers, bonus_number)
            if rank in counts:
                counts[rank] += 1

    print({
        "latest_draw": latest_draw_number,
        "counts": counts
    })


if __name__ == "__main__":
    main()


