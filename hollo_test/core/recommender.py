"""
core/recommender.py
4단계 추천 알고리즘 엔진:
1) Hard Filter (제약조건 필터링)
2) Dynamic Scoring (에너지 상태 및 취향에 따른 가중치 동적 계산)
3) Diversity Selection (상위 3곳 테마 다양성 확보)
4) Course Adapter (에너지 레벨에 따른 코스 압축/확장)
"""

from typing import List, Dict, Optional, Any
from copy import deepcopy

try:
    from config import ENERGY_LEVELS
    from services.place_service import place_service
except ImportError:
    from hollo_test.config import ENERGY_LEVELS
    from hollo_test.services.place_service import place_service


class RecommenderEngine:
    def __init__(self):
        self.place_service = place_service

    def calculate_score(
        self,
        place: Dict,
        energy_key: str = "LOW",
        preferred_themes: Optional[List[str]] = None,
        crowd_tolerance: str = "적은 게 좋아요",
    ) -> float:
        """
        Step 2. Candidate Scoring (동적 가중치 계산)
        사용자의 현재 에너지 레벨과 취향에 따라 가중치를 유동적으로 부여합니다.
        """
        scores = place.get("scores", {})
        energy_cfg = ENERGY_LEVELS.get(energy_key, ENERGY_LEVELS["LOW"])
        w = energy_cfg.get("weights", {})

        # 기본 Feature (1~5점)
        quietness = scores.get("quietness", 3.0)
        transit = scores.get("public_transport", 3.0)
        walking = scores.get("walking", 3.0)
        stayability = scores.get("stayability", 3.0)
        solo_cafe = scores.get("solo_cafe", 3.0)
        solo_dining = scores.get("solo_dining", 3.0)
        nature = scores.get("nature", 3.0)
        culture = scores.get("culture", 3.0)
        
        # 저자극 지표 (상호작용 및 피로도는 낮을수록 좋은 점수로 반전)
        low_interaction = 5.0 - scores.get("interaction_need", 2.0)
        low_fatigue = 5.0 - scores.get("fatigue", 2.0)

        # 1. 에너지 상태 기반 기본 점수 산출
        base_score = (
            quietness * w.get("quietness", 0.25)
            + transit * w.get("transit", 0.20)
            + walking * w.get("walking", 0.20)
            + stayability * w.get("stayability", 0.15)
            + solo_cafe * w.get("solo_cafe", 0.10)
            + solo_dining * w.get("solo_dining", 0.10)
            + nature * w.get("nature", 0.10)
            + culture * w.get("culture", 0.05)
            + low_interaction * 0.15
            + low_fatigue * 0.15
        )

        # 2. 인파 민감도(crowd_tolerance) 보정
        if "최대한 피하고" in crowd_tolerance or "MINIMAL" in crowd_tolerance:
            # 한적함 점수(quietness)가 4.5 이상이면 대폭 가산, 4.0 미만이면 감점
            if quietness >= 4.5:
                base_score += 0.8
            elif quietness < 4.0:
                base_score -= 1.0
        elif "적은 게 좋아요" in crowd_tolerance:
            if quietness >= 4.0:
                base_score += 0.3

        # 3. 사용자 선호 테마 매칭 보너스
        if preferred_themes:
            p_theme = place.get("theme", "")
            p_name = place.get("name", "")
            p_desc = place.get("summary", "")
            for theme in preferred_themes:
                if (theme in p_theme) or (theme in p_name) or (theme in p_desc):
                    base_score += 0.6  # 선호 테마 일치 보너스

        return round(base_score, 2)

    def select_diverse_top3(self, scored_candidates: List[Dict]) -> List[Dict]:
        """
        Step 3. Diversity Filter (다양성 보장)
        상위 3곳이 모두 똑같은 테마(예: 모두 숲, 모두 바다)가 되지 않도록
        서로 다른 테마와 매력을 가진 여행지 3곳을 선별합니다.
        """
        if len(scored_candidates) <= 3:
            return scored_candidates

        # 점수 내림차순 정렬
        sorted_candidates = sorted(scored_candidates, key=lambda x: x["final_score"], reverse=True)

        selected = []
        used_themes = set()

        # 1등 장소는 무조건 선정
        top1 = sorted_candidates[0]
        selected.append(top1)
        used_themes.add(top1["place"]["theme"])

        # 2등 및 3등은 가능한 한 다른 테마에서 높은 점수를 받은 곳 우선 선별
        for cand in sorted_candidates[1:]:
            cand_theme = cand["place"]["theme"]
            if cand_theme not in used_themes:
                selected.append(cand)
                used_themes.add(cand_theme)
                if len(selected) == 3:
                    break

        # 만약 테마가 겹쳐서 3곳을 다 못 채웠다면 나머지 중 점수 높은 순으로 채움
        if len(selected) < 3:
            for cand in sorted_candidates:
                if cand not in selected:
                    selected.append(cand)
                    if len(selected) == 3:
                        break

        return selected

    def adapt_itinerary_to_energy(self, itinerary: List[Dict], energy_key: str) -> List[Dict]:
        """
        Step 4. Course Adapter:
        사용자의 에너지 레벨에 맞춰 코스의 개수와 강도를 조절합니다.
        - EMPTY: 무리한 이동 제외, 2개 핵심 스팟 (도착/자연멍 + 조용한카페)
        - LOW: 3개 스팟 (도착/산책 + 혼밥 + 통창카페)
        - MEDIUM / HIGH: 4~5개 풀코스
        """
        max_spots = ENERGY_LEVELS.get(energy_key, {}).get("max_spots", 3)
        if len(itinerary) <= max_spots:
            return itinerary

        # EMPTY인 경우 중간 이동과 활동을 쳐내고 가장 저자극 스팟만 남김
        if energy_key == "EMPTY":
            # 첫 번째 스팟 + 멍때리기 좋은 스팟 1개만 유지
            return [itinerary[1], itinerary[3]] if len(itinerary) > 3 else itinerary[:2]

        return itinerary[:max_spots]

    def recommend(
        self,
        energy_key: str = "LOW",
        max_transit_minutes: Optional[int] = 150,
        preferred_themes: Optional[List[str]] = None,
        crowd_tolerance: str = "적은 게 좋아요",
        persona: Optional[str] = None,
    ) -> List[Dict]:
        """
        전체 4단계 추천 파이프라인 통합 실행
        """
        # 1. Hard Filter
        raw_candidates = self.place_service.filter_candidates(
            max_transit_minutes=max_transit_minutes,
            persona=persona,
        )

        # 2. Candidate Scoring
        scored_candidates = []
        for p in raw_candidates:
            score = self.calculate_score(
                place=p,
                energy_key=energy_key,
                preferred_themes=preferred_themes,
                crowd_tolerance=crowd_tolerance,
            )
            
            # 에너지 상태 맞춤형 코스 조절
            adapted_itinerary = self.adapt_itinerary_to_energy(
                itinerary=deepcopy(p.get("itinerary", [])),
                energy_key=energy_key,
            )

            # 강조 포인트 태그 생성 (별점 및 특징)
            scores = p.get("scores", {})
            quiet_star = "★" * int(round(scores.get("quietness", 3))) + "☆" * (5 - int(round(scores.get("quietness", 3))))
            transit_star = "★" * int(round(scores.get("public_transport", 3))) + "☆" * (5 - int(round(scores.get("public_transport", 3))))
            
            scored_candidates.append({
                "place": p,
                "final_score": score,
                "adapted_itinerary": adapted_itinerary,
                "highlight_tags": [
                    f"한적함 {quiet_star}",
                    f"대중교통 {transit_star}",
                    f"소요시간 {p.get('transit', {}).get('total_minutes')}분",
                    f"환승 {p.get('transit', {}).get('transfers')}회",
                ],
                "energy_match_note": ENERGY_LEVELS.get(energy_key, {}).get("name", "") + " 상태에 맞춘 저자극 코스",
            })

        # 3. Diversity Top 3 Selection
        final_top3 = self.select_diverse_top3(scored_candidates)
        return final_top3


# 싱글톤 추천 엔진 인스턴스
recommender_engine = RecommenderEngine()
