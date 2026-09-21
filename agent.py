"""
초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
===================================================
팀원 A (AI & 오케스트레이터) - LangGraph 백엔드 [처리부(Processing)] 핵심 모듈

[요구사항 구현 명세]
1. 상태(State) 정의
   - 프론트엔드 입력값: stamina(0~100), companion, region, selected_festival, extra_details
   - data.py 외부 연계 데이터: parking_lots(주차가능대수), model_restaurants, tourist_spots
   - 처리부 내부 상태: activity_level, movement_radius, activity_ratio, intent_analysis, strategy_guideline, custom_route

2. [노드 1] 활동 수준 판정 및 의도 분석 노드 (classify_activity_and_intent)
   - 체력(stamina) 수치 3단계 분할 (30% 이하 / 30~70% / 70% 이상)
   - 이동량(동선 반경) 및 Activity:Healing 비율 제어 기준값 State 추가
   - LLM 시스템 프롬프트로 extra_details 숨은 의도 심층 추출

3. [조건부 라우팅 (Conditional Edges)]
   - 판정된 activity_level에 따라 맞춤 전략 노드로 분기 (low_stamina_strategy / moderate_stamina_strategy / high_stamina_strategy)

4. [노드 2] 맞춤형 루트 제작: 데이터 통합 에이전트 (route_generator_agent)
   - 축제 거점 + 추가 관광지 탐색 + 공영주차장(주차가능대수) + 모범식당 통합
   - "주차 공간 넉넉한 곳과 주변 쉼터 연계, 인파 쏠림 회피 및 동선 최소화" 강력 지시 시스템 프롬프트 탑재
"""

import os
import sys
import re
import json
from typing import Dict, Any, List
from typing_extensions import TypedDict
from dotenv import load_dotenv

# Windows 터미널 유니코드 인코딩 대응
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 환경 변수 로드 (.env의 OPENAI_API_KEY)
load_dotenv()


# ==============================================================================
# 1. 상태(State) 정의
# ==============================================================================
class ProcessingState(TypedDict):
    """
    [처리부 핵심 State 구조체]
    프론트엔드 입력 5종과 data.py 외부 API 데이터 3종, 
    그리고 처리부 내부 노드 간 전달되는 분석/기준값 및 최종 맞춤형 루트를 관리합니다.
    """
    # ── [1] 프론트엔드 입력값 ──────────────────────────────────────────
    stamina: int                                # 체력 퍼센트 (0 ~ 100 정수)
    companion: str                              # 동반자 유형 ('나홀로', '커플', '가족', '반려견' 등)
    region: str                                 # 행정구역 ('서울특별시', '강원도', '전라남도' 등)
    selected_festival: Dict[str, Any]           # 선택된 축제 세부 정보 (name, lat, lng, address, description 등)
    extra_details: str                          # 사용자 자유 작성 세부 요구사항

    # ── [2] data.py 외부 API 연계 데이터 ───────────────────────────────
    parking_lots: List[Dict[str, Any]]          # 주변 공영주차장 (name, lat, lng, available_spaces, total_spaces, fee 등)
    model_restaurants: List[Dict[str, Any]]     # 모범식당/착한가격업소 (name, lat, lng, menu, price, is_good_price 등)
    tourist_spots: List[Dict[str, Any]]         # 추가 검색된 주변 관광지/쉼터 (name, lat, lng, category, description 등)

    # ── [3] [노드 1] 및 전략 분기에서 도출되는 제어 기준값 ──────────────
    activity_level: str                         # 활동 수준 ("Low" | "Moderate" | "High")
    movement_radius: str                        # 하루 권장 이동량/반경 (예: "도보 500m 이내", "반경 2~3km")
    activity_ratio: str                         # Activity(참여) 대비 Healing(휴식) 비율 (예: "20:80", "50:50", "80:20")
    intent_analysis: Dict[str, Any]             # LLM이 파악한 extra_details 숨은 의도 분석 데이터
    strategy_guideline: str                     # 조건부 분기에서 확정된 전략 지침

    # ── [4] [노드 2] 데이터 통합 에이전트가 제작한 맞춤형 루트 ─────────
    custom_route: Dict[str, Any]                # 타임테이블, 쉼터 연계, 주차장/식당 최적 매칭 결과 JSON


# ==============================================================================
# 2. [노드 1] 활동 수준 판정 및 의도 분석 노드
# ==============================================================================
INTENT_ANALYSIS_SYSTEM_PROMPT = """너는 여행자의 자유 작성 요구사항(extra_details) 속에 숨겨진 신체 컨디션, 
보행 제약 및 잠재적 스트레스 요인을 꿰뚫어 보는 전문 여행 심리 분석가야.

고객의 체력(stamina: {stamina}%), 동반자({companion}), 세부 요구사항을 종합 분석하여
현장 이동과 쉼터 선정에서 '절대 놓쳐선 안 될 핵심 우선순위'를 파악해 줘.

[분석 가이드]
1. "다리가 아파", "오래 못 걸어", "유모차/휠체어", "부모님/아이" 언급 시:
   -> 계단 없는 평지 코스, 이동 거리 최소화, 축제장 도보 2~3분 내 최단거리 주차장 최우선.
2. "조용한 곳", "사람 많은 거 싫어", "휴식", "힐링" 언급 시:
   -> 소음 차단, 인파가 적은 외곽 그늘 쉼터, 한적한 티하우스 중심.
3. "맛집", "바가지 싫어", "현지인 식당" 언급 시:
   -> 지자체 인증 착한가격업소 및 가성비 모범식당 우선 매칭.

반드시 아래 JSON 포맷으로만 응답해 (추가 마크다운 코드블록이나 불필요한 설명 금지):
{{
    "core_needs": "핵심 니즈 요약 (한 줄)",
    "mobility_constraint": "보행 제약 사항 (없음, 경미, 보통, 심각 중 택1)",
    "key_care_points": ["케어 포인트 1", "케어 포인트 2"],
    "parking_strategy": "최근접 주차장 우선" | "만차 회피 외곽 주차장 우선"
}}
"""

def classify_activity_and_intent(state: ProcessingState) -> Dict[str, Any]:
    """
    [노드 1]:
    1. 체력(stamina: 0~100)을 3단계로 분할하여 활동 수준(Low, Moderate, High)을 판정
    2. 단계에 맞춰 동선 반경(movement_radius)과 Activity:Healing 비율을 동적으로 설정
    3. LLM을 통해 extra_details에 담긴 숨은 의도를 분석
    """
    stamina = state.get("stamina", 50)

    # 1) 체력 3단계 분할 및 동적 제어 기준값 설정
    if stamina <= 30:
        # [30% 이하: 저강도 쉼터 집중형]
        activity_level = "Low"
        movement_radius = "축제장 거점 도보 500m 이내 (동선 극소화)"
        activity_ratio = "Activity 20% : Healing 80% (쉼터 집중형)"
    elif stamina <= 70:
        # [30% ~ 70%: 중강도 황금 밸런스형]
        activity_level = "Moderate"
        movement_radius = "축제장 및 인근 권역 반경 2~3km"
        activity_ratio = "Activity 50% : Healing 50% (황금 밸런스형)"
    else:
        # [70% 이상: 고강도 풀코스 액티비티형]
        activity_level = "High"
        movement_radius = "축제장 전역 및 주변 명소 반경 5km 이상"
        activity_ratio = "Activity 80% : Healing 20% (풀코스 액티비티형)"

    # 2) LLM extra_details 숨은 의도 분석
    extra_details = state.get("extra_details", "").strip() or "특별한 요청 없음 (쾌적하고 여유로운 여행 선호)"
    companion = state.get("companion", "일반")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"), temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", INTENT_ANALYSIS_SYSTEM_PROMPT)
    ])
    chain = prompt | llm | StrOutputParser()

    try:
        raw_output = chain.invoke({
            "stamina": stamina,
            "companion": companion,
            "extra_details": extra_details
        })
        cleaned_json = re.sub(r"```json|```", "", raw_output).strip()
        intent_data = json.loads(cleaned_json)
    except Exception:
        intent_data = {
            "core_needs": "무리 없는 안전하고 편안한 쉼표 중심 여행",
            "mobility_constraint": "보통" if stamina <= 30 else "경미",
            "key_care_points": ["도보 이동 최소화", "그늘 쉼터 우선"],
            "parking_strategy": "최근접 주차장 우선" if stamina <= 30 else "만차 회피 외곽 주차장 우선"
        }

    return {
        "activity_level": activity_level,
        "movement_radius": movement_radius,
        "activity_ratio": activity_ratio,
        "intent_analysis": intent_data
    }


# ==============================================================================
# 3. [조건부 분기 노드] 체력 및 활동 수준별 라우팅 전략 노드
# ==============================================================================
def route_by_activity_level(state: ProcessingState) -> str:
    """
    [조건부 라우터 함수]:
    활동 수준(Low, Moderate, High)에 따라 적합한 세부 전략 노드로 분기합니다.
    """
    level = state.get("activity_level", "Moderate")
    if level == "Low":
        return "low_stamina_strategy"
    elif level == "High":
        return "high_stamina_strategy"
    else:
        return "moderate_stamina_strategy"


def low_stamina_strategy(state: ProcessingState) -> Dict[str, Any]:
    """[30% 이하 분기]: 도보 500m 이내, 쉼터 80%, 최근접 주차장 최우선 가이드라인"""
    intent = state.get("intent_analysis", {})
    return {
        "strategy_guideline": (
            "- [이동 제한]: 총 도보 거리를 500m 이내로 극소화하고 평지/무장애 동선만 채택할 것.\n"
            "- [주차 매칭]: 만차 대기가 발생하더라도 축제장 매표소와 가장 가까운 주차장을 최우선 배치.\n"
            "- [쉼터 배치]: 축제 핵심 30분 관람 후 즉시 외곽 그늘 정원/티하우스 쉼터로 이동하여 80% 이상의 시간을 휴식에 할애할 것.\n"
            f"- [숨은 의도 반영]: {intent.get('core_needs', '무리 없는 힐링')} 철저 준수."
        )
    }


def moderate_stamina_strategy(state: ProcessingState) -> Dict[str, Any]:
    """[30~70% 분기]: 반경 2~3km, Activity 50% : Healing 50% 황금 밸런스 가이드라인"""
    intent = state.get("intent_analysis", {})
    return {
        "strategy_guideline": (
            "- [이동 권역]: 축제장과 인근 쉼터를 아우르는 반경 2~3km 권역 설정.\n"
            "- [주차 매칭]: 축제장 정문의 극심한 정체를 피해 출차가 빠르고 주차 잔여 대수가 넉넉한 외곽/임시 주차장 권장.\n"
            "- [쉼터 배치]: 축제 하이라이트 관람(1~1.5시간)과 감성 로컬 카페/피크닉 존(1시간)을 50:50으로 교차 배치.\n"
            f"- [숨은 의도 반영]: {intent.get('core_needs', '알짜 관람과 충전')} 충실 반영."
        )
    }


def high_stamina_strategy(state: ProcessingState) -> Dict[str, Any]:
    """[70% 이상 분기]: 반경 5km 이상, Activity 80% : Healing 20% 풀코스 액티비티 가이드라인"""
    intent = state.get("intent_analysis", {})
    return {
        "strategy_guideline": (
            "- [이동 권역]: 축제장 전역 및 인근 추가 명소까지 포함하는 반경 5km 이상의 광폭 동선.\n"
            "- [주차 매칭]: 늦은 야간 퇴장까지 고려한 대규모 공영주차장 매칭.\n"
            "- [코스 배치]: 메인 공연, 체험 부스, 로컬 명소를 80% 비율로 적극 탐방하고 중간 숏브레이크만 배치.\n"
            f"- [숨은 의도 반영]: {intent.get('core_needs', '다채로운 볼거리와 활기찬 체험')} 극대화."
        )
    }


# ==============================================================================
# 4. [노드 2] 맞춤형 루트 제작 (데이터 통합 에이전트)
# ==============================================================================
DATA_INTEGRATION_AGENT_PROMPT = """너는 로컬 축제 거점과 주변 데이터(주차장, 모범식당, 관광지/쉼터)를 융합하여 
최적의 여행 동선을 설계하는 'Fest & Rest 데이터 통합 라우팅 에이전트'야.

너의 임무는 확정된 [활동 수준], [동선 반경 및 비율], [숨은 의도], [전략 지침]을 엄격히 따라,
외부에서 제공된 실제 데이터만을 활용하여 인파 피로가 없는 **'초개인화 여행 루트(타임테이블)'**를 완성하는 것이다.

---
### ⚡ [필수 제약 조건 (강력 지시)]
1. **주차장 데이터(주차 가능 대수) 최우선 반영**:
   - 제공된 [공영주차장 목록]에서 **주차 가능 대수가 가장 넉넉한 곳** 또는 **보행 제약에 맞춰 가장 가까운 곳**을 콕 짚어 시작 지점으로 지정하라.
   - 메인 주차장의 만차 스트레스를 회피하고 진출입이 수월한 주차 꿀팁을 반드시 포함하라.

2. **인파 쏠림 방지 및 주변 쉼터/관광지 연계**:
   - 축제장 메인에만 머물지 말고, 제공된 [주변 관광지/쉼터 목록]에서 인파를 피할 수 있는 한적한 쉼터를 일정 중간에 배치하여 동선을 분산시켜라.
   - [Activity : Healing 비율: {activity_ratio}]과 [이동 반경: {movement_radius}]을 철저히 준수하라.

3. **바가지 없는 착한가격 모범식당 필수 매칭**:
   - 제공된 [모범식당 목록] 중 적합한 식당의 실제 상호명, 대표메뉴, 착한가격을 식사 시간대에 반드시 명시하라.

---
### 📋 [출력 포맷: 반드시 JSON 객체만 응답 (Markdown 백틱 제외)]
{{
    "route_theme": "루트 테마 슬로건 (한 줄)",
    "activity_summary": {{
        "level": "{activity_level}",
        "radius": "{movement_radius}",
        "ratio": "{activity_ratio}"
    }},
    "selected_parking": {{
        "name": "선정된 주차장명",
        "available_spaces": 120,
        "reason": "주차 여유도 및 동선 관점의 선정 사유"
    }},
    "selected_restaurant": {{
        "name": "선정된 모범식당명",
        "menu": "대표 메뉴",
        "price": "가격",
        "reason": "바가지 없는 안심 모범식당 추천 사유"
    }},
    "timeline": [
        {{
            "time": "10:00 - 10:30",
            "spot_name": "장소명 (주차장 / 축제장 / 쉼터 / 식당)",
            "type": "Parking" | "Festival" | "Rest" | "Food" | "Attraction",
            "description": "활동 상세 및 인파 회피 팁"
        }}
    ],
    "crowd_avoidance_golden_time": "가장 한적하게 즐길 수 있는 추천 골든타임"
}}
"""

def route_generator_agent(state: ProcessingState) -> Dict[str, Any]:
    """
    [노드 2]:
    활동 수준 결과, 축제 거점, 추가 관광지, 공영주차장(주차가능대수), 모범식당을 
    종합 결합하여 인파 회피형 타임테이블 루트를 제작합니다.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

    model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.4)

    fest = state.get("selected_festival", {})
    intent = state.get("intent_analysis", {})

    # 외부 주차장 데이터 문자열화
    parking_lines = []
    for p in state.get("parking_lots", []):
        avail = p.get("available_spaces", 0)
        total = p.get("total_spaces", 0)
        dist = p.get("distance", "축제장 인근")
        fee = p.get("fee", "무료")
        parking_lines.append(f"- {p.get('name')}: 주차가능 {avail}대 / 총 {total}대 (거리: {dist}, 요금: {fee})")
    parking_str = "\n".join(parking_lines) if parking_lines else "주차장 데이터 없음"

    # 외부 모범식당 데이터 문자열화
    restaurant_lines = []
    for r in state.get("model_restaurants", []):
        name = r.get("name")
        menu = r.get("menu", "로컬 메뉴")
        price = r.get("price", "착한가격")
        desc = r.get("desc", "착한가격업소")
        restaurant_lines.append(f"- {name}: 대표메뉴 [{menu}] ({price}) - {desc}")
    restaurant_str = "\n".join(restaurant_lines) if restaurant_lines else "모범식당 데이터 없음"

    # 추가 주변 관광지/쉼터 데이터 문자열화
    spot_lines = []
    for s in state.get("tourist_spots", []):
        s_name = s.get("name")
        s_cat = s.get("category", "쉼터/관광지")
        s_desc = s.get("description", "한적한 휴식 공간")
        spot_lines.append(f"- {s_name} ({s_cat}): {s_desc}")
    tourist_str = "\n".join(spot_lines) if spot_lines else "주변 추가 쉼터/관광지 정보 없음"

    prompt = ChatPromptTemplate.from_messages([
        ("system", DATA_INTEGRATION_AGENT_PROMPT),
        ("human", """[사용자 활동 조건 및 전략 지침]
- 활동 수준: {activity_level}
- 이동량 반경: {movement_radius}
- 설계 비율: {activity_ratio}
- 숨은 니즈 분석: {core_needs} (보행 제약: {mobility_constraint})
- 주차 전략: {parking_strategy}
- 동반자: {companion}
- [확정된 전략 지침]:
{strategy_guideline}

[중심 거점 축제]
- 축제명: {fest_name}
- 위치: {fest_address}
- 축제 소개: {fest_desc}

[data.py 연계 외부 데이터]
■ 공영주차장 현황 (주차 가능 대수 포함):
{parking_str}

■ 착한가격 모범식당 현황 (바가지 안심 업소):
{restaurant_str}

■ 추가 탐색된 주변 관광지 및 숨은 쉼터:
{tourist_str}

위 지침과 데이터를 바탕으로, 인파 쏠림을 회피하고 동선을 최적화한 JSON 여행 루트를 완성하라.""")
    ])

    chain = prompt | llm | StrOutputParser()

    raw_output = chain.invoke({
        "activity_level": state.get("activity_level", "Moderate"),
        "movement_radius": state.get("movement_radius", "반경 2km"),
        "activity_ratio": state.get("activity_ratio", "50:50"),
        "core_needs": intent.get("core_needs", "편안한 여행"),
        "mobility_constraint": intent.get("mobility_constraint", "보통"),
        "parking_strategy": intent.get("parking_strategy", "여유 주차장 우선"),
        "companion": state.get("companion", "일반"),
        "strategy_guideline": state.get("strategy_guideline", ""),
        "fest_name": fest.get("name", "로컬 축제"),
        "fest_address": fest.get("address", state.get("region", "")),
        "fest_desc": fest.get("description", "지역 대표 축제"),
        "parking_str": parking_str,
        "restaurant_str": restaurant_str,
        "tourist_str": tourist_str
    })

    try:
        cleaned_json = re.sub(r"```json|```", "", raw_output).strip()
        custom_route = json.loads(cleaned_json)
    except Exception:
        custom_route = {
            "route_theme": f"{fest.get('name', '축제')} 안심 Fest & Rest 힐링 루트",
            "activity_summary": {
                "level": state.get("activity_level", "Moderate"),
                "radius": state.get("movement_radius", "도보 500m 이내"),
                "ratio": state.get("activity_ratio", "50:50")
            },
            "selected_parking": {"name": "인근 공영주차장", "available_spaces": 50, "reason": "접근성 고려"},
            "selected_restaurant": {"name": "착한가격 모범식당", "menu": "로컬 정식", "price": "10,000원", "reason": "바가지 없는 안심 식당"},
            "timeline": [
                {"time": "10:00", "spot_name": "추천 주차장", "type": "Parking", "description": "주차 후 축제장 이동"},
                {"time": "10:30", "spot_name": fest.get("name", "축제장"), "type": "Festival", "description": "오전 시간대 여유로운 관람"},
                {"time": "12:00", "spot_name": "모범식당", "type": "Food", "description": "바가지 없는 안심 식사"},
                {"time": "13:30", "spot_name": "주변 쉼터", "type": "Rest", "description": "인파 피크타임 회피 휴식"}
            ],
            "crowd_avoidance_golden_time": "10:00 - 12:00 (오전 골든타임)"
        }

    return {"custom_route": custom_route}


# ==============================================================================
# 5. LangGraph 워크플로우 뼈대 (Conditional Edges & Edges)
# ==============================================================================
def build_processing_workflow():
    """
    [처리부 워크플로우 뼈대 구성]
    
    [START] 
       │
       ▼
    [노드 1: classify_activity_and_intent] (활동 수준 판정 & 의도 분석)
       │
       ├─ (Conditional Edge: route_by_activity_level)
       │    ├─ "low_stamina_strategy"      ──┐ (체력 30% 이하: 쉼터 80%, 동선 500m)
       │    ├─ "moderate_stamina_strategy" ──┼─ (체력 30~70%: 50:50 밸런스)
       │    └─ "high_stamina_strategy"     ──┘ (체력 70% 이상: 풀코스 액티비티)
       │
       ▼
    [노드 2: route_generator_agent] (데이터 통합 에이전트: 주차장/식당/쉼터 결합)
       │
       ▼
     [END]
    """
    workflow = StateGraph(ProcessingState)

    # 1. 노드 등록
    workflow.add_node("classify_activity_and_intent", classify_activity_and_intent)
    workflow.add_node("low_stamina_strategy", low_stamina_strategy)
    workflow.add_node("moderate_stamina_strategy", moderate_stamina_strategy)
    workflow.add_node("high_stamina_strategy", high_stamina_strategy)
    workflow.add_node("route_generator_agent", route_generator_agent)

    # 2. 엣지 연결
    workflow.add_edge(START, "classify_activity_and_intent")

    # 3. 분기점 (Conditional Edges)
    workflow.add_conditional_edges(
        "classify_activity_and_intent",
        route_by_activity_level,
        {
            "low_stamina_strategy": "low_stamina_strategy",
            "moderate_stamina_strategy": "moderate_stamina_strategy",
            "high_stamina_strategy": "high_stamina_strategy",
        }
    )

    # 4. 전략 노드 -> 데이터 통합 에이전트 수렴
    workflow.add_edge("low_stamina_strategy", "route_generator_agent")
    workflow.add_edge("moderate_stamina_strategy", "route_generator_agent")
    workflow.add_edge("high_stamina_strategy", "route_generator_agent")

    # 5. 종료
    workflow.add_edge("route_generator_agent", END)

    return workflow.compile()


# 워크플로우 인스턴스 컴파일
processing_workflow = build_processing_workflow()


# ==============================================================================
# 6. [처리부 단독 테스트 블록] (개발 및 디버깅용)
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("🎪 Fest & Rest AI [처리부] Conditional Edges 워크플로우 검증")
    print("=" * 70)

    # 프론트엔드 입력 테스트 데이터
    sample_frontend_inputs = {
        "stamina": 25,  # 30% 이하 -> low_stamina_strategy 분기
        "companion": "부모님 (연로하심)",
        "region": "전라남도",
        "selected_festival": {
            "name": "순천만 갈대축제",
            "lat": 34.8845,
            "lng": 127.5090,
            "address": "전남 순천시 순천만길 513-25",
            "description": "광활한 황금빛 갈대밭과 흑두루미가 반겨주는 가을 힐링 축제"
        },
        "extra_details": "부모님이 무릎이 안 좋으셔서 계단은 못 가고 오래 못 걸어요. 차는 축제장과 제일 가까운 곳에 대고 싶습니다."
    }

    # data.py 연계 외부 테스트 데이터
    sample_external_data = {
        "parking_lots": [
            {
                "name": "순천만습지 정문 제1주차장 (최근접)",
                "lat": 34.8842,
                "lng": 127.5085,
                "available_spaces": 16,
                "total_spaces": 180,
                "fee": "3,000원",
                "distance": "축제장 매표소 도보 1분 (무장애 평지)"
            },
            {
                "name": "순천만 에코촌 외곽 공영주차장 (여유)",
                "lat": 34.8810,
                "lng": 127.5040,
                "available_spaces": 175,
                "total_spaces": 300,
                "fee": "무료",
                "distance": "축제장 도보 8분 / 갈대열차 탑승"
            }
        ],
        "model_restaurants": [
            {
                "name": "갈대골 착한 남도식당",
                "lat": 34.8835,
                "lng": 127.5075,
                "menu": "순천만 꼬막정식",
                "price": "12,000원",
                "is_good_price": True,
                "desc": "순천시 공인 모범식당, 바가지요금 없는 정직한 로컬 맛집 (1층 입식 테이블 완비)"
            }
        ],
        "tourist_spots": [
            {
                "name": "순천만 자연소리 쉼터 (그늘 정원)",
                "lat": 34.8850,
                "lng": 127.5100,
                "category": "쉼터",
                "description": "축제장 외곽 도보 5분 거리, 인파 소음 없이 바람 소리를 들으며 쉴 수 있는 평지 벤치존"
            }
        ]
    }

    # 초기 상태 구성
    initial_state: ProcessingState = {
        **sample_frontend_inputs,
        **sample_external_data,
        "activity_level": "",
        "movement_radius": "",
        "activity_ratio": "",
        "intent_analysis": {},
        "strategy_guideline": "",
        "custom_route": {}
    }

    print("\n▶ [LangGraph 워크플로우 실행: START -> 노드 1 -> Conditional Edge -> 전략 분기 -> 노드 2 -> END]")
    result_state = processing_workflow.invoke(initial_state)

    print("\n[1. 노드 1 분석 & 조건부 분기 결과]")
    print(f"- 판정 활동 수준: {result_state['activity_level']}")
    print(f"- 이동량 반경 기준: {result_state['movement_radius']}")
    print(f"- Activity:Healing 비율: {result_state['activity_ratio']}")
    print(f"- 추출된 숨은 니즈: {result_state['intent_analysis']}")
    print(f"- 확정된 전략 지침:\n{result_state['strategy_guideline']}")

    print("\n[2. 노드 2 데이터 통합 맞춤형 루트 (custom_route)]")
    print(json.dumps(result_state["custom_route"], indent=2, ensure_ascii=False))
    print("=" * 70)
