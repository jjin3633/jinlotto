from typing import Dict, List, Tuple
from sqlalchemy.orm import Session

from backend.app.db.models import Prediction, Draw, Match


def _compute_rank(user_numbers: List[int], draw_numbers: List[int], bonus_number: int) -> Tuple[int, int, bool, List[int]]:
    user_set = set(int(x) for x in user_numbers)
    draw_set = set(int(x) for x in draw_numbers)
    matched = sorted(list(user_set.intersection(draw_set)))
    match_count = len(matched)
    bonus_match = int(bonus_number) in user_set

    # 6/45 규칙
    if match_count == 6:
        rank = 1
    elif match_count == 5 and bonus_match:
        rank = 2
    elif match_count == 5:
        rank = 3
    elif match_count == 4:
        rank = 4
    elif match_count == 3:
        rank = 5
    else:
        rank = 0

    return rank, match_count, bonus_match, matched


def evaluate_matches_for_draw(db: Session, draw_number: int) -> Dict[int, int]:
    draw = db.query(Draw).filter(Draw.draw_number == draw_number).first()
    if not draw:
        return {1: 0, 2: 0, 3: 0}

    counts = {1: 0, 2: 0, 3: 0}

    # 모든 예측에 대해 평가(생성일 필터가 필요하면 draw.draw_date 기준으로 제한 가능)
    preds = db.query(Prediction).all()
    for p in preds:
        # 중복 저장 방지
        exists = (
            db.query(Match)
            .filter(Match.prediction_id == p.id, Match.draw_number == draw_number)
            .first()
        )
        if exists:
            # 집계에 반영
            if exists.rank in counts:
                counts[exists.rank] += 1
            continue

        rank, match_count, bonus_match, matched = _compute_rank(
            p.numbers or [], draw.numbers or [], draw.bonus_number
        )
        m = Match(
            prediction_id=p.id,
            draw_number=draw_number,
            match_count=match_count,
            bonus_match=bool(bonus_match),
            rank=rank,
            matched_numbers=matched,
        )
        db.add(m)
        if rank in counts:
            counts[rank] += 1

    db.commit()
    return counts


