"""
core/curator.py
Hollo [홀로] 종합 큐레이터 오케스트레이터
1) 사용자 자연어 질의에서 슬롯/선호도 추출 (extractor)
2) 에너지 기반 4단계 추천 알고리즘 실행 (recommender)
3) 큐레이터 감성 맞춤 설명 및 브리핑 리포트 합성 (Explanation AI)
"""

import os
from typing import Dict, Any, Optional

try:
    from config import ENERGY_LEVELS
    from core.extractor import extract_preferences
    from core.recommender import recommender_engine
    from core.prompts import CURATOR_SYSTEM_PROMPT, EXPLANATION_PROMPT
except ImportError:
    from hollo_test.config import ENERGY_LEVELS
    from hollo_test.core.extractor import extract_preferences
    from hollo_test.core.recommender import recommender_engine
    from hollo_test.core.prompts import CURATOR_SYSTEM_PROMPT, EXPLANATION_PROMPT


class HolloCurator:
    def __init__(self):
        self.recommender = recommender_engine

    def generate_explanation(
        self,
        preferences: Dict[str, Any],
        top3_places: list,
    ) -> str:
        """
        선정된 3곳 여행지에 대해 사용자의 현재 에너지 상태를 보듬어주는 감성 브리핑 생성
        """
        if not top3_places:
            return "현재 조건에 부합하는 장소를 찾지 못했습니다. 이동 시간이나 테마 조건을 조금 더 여유롭게 설정해 보세요."

        energy_key = preferences.get("energy_level", "LOW")
        energy_name = ENERGY_LEVELS.get(energy_key, {}).get("name", "조금 쉼")
        themes_str = ", ".join(preferences.get("preferred_themes", ["자연"]))

        p1 = top3_places[0]["place"]
        p2 = top3_places[1]["place"] if len(top3_places) > 1 else p1
        p3 = top3_places[2]["place"] if len(top3_places) > 2 else p2

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and not api_key.startswith("your_"):
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import SystemMessage, HumanMessage

                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=api_key, timeout=6)
                prompt = EXPLANATION_PROMPT.format(
                    energy_name=energy_name,
                    themes=themes_str,
                    departure=preferences.get("departure", "서울"),
                    max_transit=preferences.get("max_transit_minutes", 120),
                    place1_name=p1.get("name"),
                    place1_theme=p1.get("theme"),
                    place1_reason=p1.get("curator_note"),
                    place2_name=p2.get("name"),
                    place2_theme=p2.get("theme"),
                    place2_reason=p2.get("curator_note"),
                    place3_name=p3.get("name"),
                    place3_theme=p3.get("theme"),
                    place3_reason=p3.get("curator_note"),
                )
                res = llm.invoke([
                    SystemMessage(content=CURATOR_SYSTEM_PROMPT),
                    HumanMessage(content=prompt)
                ])
                return res.content.strip()
            except Exception:
                pass

        # LLM 미호출 시 따뜻한 규칙 기반 템플릿 반환
        return (
            f"안녕하세요. 이번 주말, **{energy_name}** 상태이신 당신을 위해 "
            f"인파의 소음에서 벗어나 조용히 숨을 고를 수 있는 **세 곳의 저자극 쉼터**를 골라보았습니다.\n\n"
            f"무리한 환승이나 바쁜 관광 대신, **{p1.get('name')}**의 잔잔한 풍경부터 "
            f"가만히 머물기 좋은 **{p2.get('name')}**, 고즈넉한 **{p3.get('name')}**까지 "
            f"혼자만의 호흡으로 여유롭게 머물다 오실 수 있는 곳들입니다."
        )

    def curate(
        self,
        query: str,
        energy_override: Optional[str] = None,
        max_transit_override: Optional[int] = None,
        theme_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        전체 큐레이션 워크플로우 실행
        """
        # 1. 선호도 추출
        prefs = extract_preferences(query)

        # UI 수동 조작 오버라이드 반영
        if energy_override:
            prefs["energy_level"] = energy_override
        if max_transit_override:
            prefs["max_transit_minutes"] = max_transit_override
        if theme_override and theme_override != "전체":
            prefs["preferred_themes"] = [theme_override]

        # 2. 4단계 추천 엔진 구동
        recommendations = self.recommender.recommend(
            energy_key=prefs.get("energy_level", "LOW"),
            max_transit_minutes=prefs.get("max_transit_minutes", 120),
            preferred_themes=prefs.get("preferred_themes", []),
            crowd_tolerance=prefs.get("crowd_tolerance", "적은 게 좋아요"),
        )

        # 3. 큐레이터 브리핑 생성
        briefing = self.generate_explanation(
            preferences=prefs,
            top3_places=recommendations,
        )

        return {
            "query": query,
            "preferences": prefs,
            "briefing": briefing,
            "recommendations": recommendations,
        }


# 싱글톤 인스턴스
hollo_curator = HolloCurator()
