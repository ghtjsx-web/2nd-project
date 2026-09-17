"""
core/extractor.py
자연어 대화 입력에서 여행 조건 및 슬롯(출발지, 에너지, 테마, 이동시간)을 자동 추출하는 모듈
- 1차: LangChain LLM (OpenAI) 기반 구조화 JSON 추출
- 2차(Fallback): 규칙 및 키워드 기반 고성능 규칙 추출기 (API 키 없거나 네트워크 장애 시에도 100% 안정 작동)
"""

import os
import re
import json
from typing import Dict, Any, List

try:
    from core.prompts import SLOT_EXTRACTION_PROMPT
except ImportError:
    from hollo_test.core.prompts import SLOT_EXTRACTION_PROMPT


def _rule_based_extract(query: str) -> Dict[str, Any]:
    """
    규칙 및 키워드 사전을 활용한 신속하고 안정적인 슬롯 추출 (Fallback)
    """
    q = query.lower()
    
    # 1. 에너지 상태 판별
    energy = "LOW"
    if any(k in q for k in ["방전", "너무 피곤", "힘들", "지쳤", "쉬고만", "아무것도", "기절", "번아웃"]):
        energy = "EMPTY"
    elif any(k in q for k in ["가볍게", "조금 쉼", "산책", "바람 쐬", "잔잔", "천천히"]):
        energy = "LOW"
    elif any(k in q for k in ["둘러보", "전시", "카페", "서점", "골목", "책", "미술관"]):
        energy = "MEDIUM"
    elif any(k in q for k in ["많이", "알차게", "탐방", "에너지", "돌아다니"]):
        energy = "HIGH"

    # 2. 선호 테마 추출
    themes: List[str] = []
    theme_keywords = {
        "바다": ["바다", "해변", "동해", "서해", "파도", "오션"],
        "호수": ["호수", "수변", "물멍", "강변", "강"],
        "숲": ["숲", "자연", "나무", "피톤치드", "휴양림", "둘레길", "공원"],
        "문화": ["문화", "미술관", "전시", "역사", "성곽", "박물관"],
        "책": ["책", "서점", "도서관", "독서"],
        "카페": ["카페", "커피", "디저트", "티하우스"],
        "사찰": ["사찰", "절", "산사", "명상"],
        "골목": ["골목", "마을", "레트로", "노포"],
    }
    for theme_label, kws in theme_keywords.items():
        if any(kw in q for kw in kws):
            themes.append(theme_label)

    # 3. 최대 이동시간 추출 (예: "1시간", "2시간 반", "90분")
    max_transit = 120
    if "1시간" in q or "한시간" in q:
        max_transit = 60
    elif "1시간 반" in q or "90분" in q:
        max_transit = 90
    elif "2시간" in q or "두시간" in q:
        max_transit = 120
    elif "3시간" in q or "세시간" in q:
        max_transit = 180

    # 4. 인파 허용도
    crowd_tolerance = "적은 게 좋아요"
    if any(k in q for k in ["사람 없는", "사람 적은", "조용한", "한적한", "혼자만", "피하고"]):
        crowd_tolerance = "최대한 피하고 싶어요"

    # 5. 출발지
    departure = "서울/수도권"
    for dep in ["서울", "용산", "청량리", "강남", "수원", "인천", "대전", "부산"]:
        if dep in q:
            departure = dep
            break

    return {
        "departure": departure,
        "travel_date": "이번 주말",
        "energy_level": energy,
        "crowd_tolerance": crowd_tolerance,
        "preferred_themes": themes if themes else ["자연", "산책"],
        "max_transit_minutes": max_transit,
    }


def extract_preferences(user_query: str) -> Dict[str, Any]:
    """
    사용자의 자연어 질의에서 여행 선호 조건을 추출합니다.
    """
    if not user_query or not user_query.strip():
        return _rule_based_extract("")

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and not api_key.startswith("your_"):
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=api_key,
                timeout=5,
            )
            prompt = SLOT_EXTRACTION_PROMPT.format(user_query=user_query)
            response = llm.invoke([
                SystemMessage(content="You are a strict JSON extractor for travel preferences."),
                HumanMessage(content=prompt)
            ])
            text = response.content.strip()
            # 마크다운 코드블록 제거
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text)
            # 기본값 보정
            if not parsed.get("preferred_themes"):
                parsed["preferred_themes"] = ["자연", "산책"]
            return parsed
        except Exception:
            # LLM 호출 실패 시 안전하게 규칙 기반으로 폴백
            return _rule_based_extract(user_query)

    return _rule_based_extract(user_query)
