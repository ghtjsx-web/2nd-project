"""
초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
팀원 A (AI & 오케스트레이터) - 백엔드 AI 파이프라인 (agent.py)
"""

import os
import sys
import re
import json
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

# ==============================================================================
# 1. 상태(State) 정의
# ==============================================================================
class PipelineState(TypedDict):
    stamina: int
    companion: str
    region: str
    selected_festival: Dict[str, Any]
    extra_details: str
    parking_lots: List[Dict[str, Any]]
    model_restaurants: List[Dict[str, Any]]
    tourist_spots: List[Dict[str, Any]]
    activity_level: str
    movement_radius: str
    activity_ratio: str
    intent_analysis: Dict[str, Any]
    strategy_guideline: str
    event_info: Dict[str, List[Dict[str, Any]]]
    article_content: str
    map_markers: List[Dict[str, Any]]


# ==============================================================================
# 2. 프롬프트 중앙 관리
# ==============================================================================
INTENT_ANALYSIS_PROMPT = """너는 여행자의 요구사항을 심층 분석하는 여행 심리 분석가야.
고객의 체력(stamina: {stamina}%), 동반자({companion}), 세부 요구사항을 분석하여
현장에서 가장 배려해야 할 **핵심 우선순위와 이동 제약 사항**을 도출해 줘.

■ 사용자의 자유 세부 요구사항: "{extra_details}"

[분석 지침]
- "다리가 아파", "오래 못 걸어", "유모차", "휠체어", "부모님" 등: 계단 없는 평지 코스, 이동 동선 최소화, 쉼터 우선 연계.
- "조용한 곳", "사람 많은 거 싫어", "힐링": 소음 차단, 한적한 외곽 쉼터 우선.
- "맛집", "바가지 싫어": 제공된 모범식당 집중 연계.

반드시 아래 JSON 포맷으로만 응답해:
{{
    "core_needs": "핵심 니즈 요약 (한 줄)",
    "mobility_constraint": "보행 제약 사항 (없음, 경미, 보통, 심각 중 택1)",
    "parking_focus": "대규모 주차면수 우선 (총 주차면수 기반 진입 및 주차 안정성 중심)"
}}"""

MAGAZINE_EDITOR_SYSTEM_PROMPT = """너는 감각적이고 트렌디한 로컬 라이프스타일 매거진의 수석 여행 에디터야.
축제의 설렘과 쉼터의 평온함을 완벽한 밸런스로 조율하는 'Fest & Rest' 기사를 작성해 줘.

[반드시 지켜야 할 엄격한 데이터 원칙]
1. 가짜 데이터(할루시네이션) 생성 절대 금지. 없으면 없다고 정직하게 안내.
2. 공영주차장 데이터 제한 (실시간 빈자리 언급 절대 금지). 오직 총 주차면수 정보만 인용.
3. 오직 제공된 [착한가격업소/모범식당 목록] 명단 내에서만 추천.

[매거진 기사 필수 구성]
# 🌿 [헤드라인: 감각적인 메인 타이틀 & 서브헤드]
### 🖋️ Editor's Letter: [오늘의 여정을 시작하며]
### 🗺️ Fest & Rest Curated Timeline: [시간이 머무는 맞춤 동선]
### 📌 Event Guide: [프로그램 체크리스트]
### 🛡️ Safe & Relax Tips: [현장 안심 꿀팁 브리핑 (주차 및 쉼터 위주)]
"""


# ==============================================================================
# 3. 유틸리티 (위/경도 분리 및 Boolean 파싱)
# ==============================================================================
def _get_llm(temperature: float = 0.2):
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"), temperature=temperature)

def _safe_lat(val: Any) -> Optional[float]:
    """위도(Latitude) 범위를 엄격하게 검사 (-90 ~ 90)"""
    try:
        f = float(val)
        return f if -90.0 <= f <= 90.0 else None
    except (ValueError, TypeError):
        return None

def _safe_lng(val: Any) -> Optional[float]:
    """경도(Longitude) 범위를 엄격하게 검사 (-180 ~ 180)"""
    try:
        f = float(val)
        return f if -180.0 <= f <= 180.0 else None
    except (ValueError, TypeError):
        return None

def _parse_bool(val: Any) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    str_val = str(val).strip().lower()
    if str_val in ("y", "yes", "true", "1", "예약필수", "사전예약"):
        return True
    if str_val in ("n", "no", "false", "0", "자유입장", "제한없음", "무료입장", "상시"):
        return False
    return None


# ==============================================================================
# 4. LangGraph 노드
# ==============================================================================
def analyze_stamina_and_intent(state: PipelineState) -> Dict[str, Any]:
    stamina = state.get("stamina", 50)
    extra = state.get("extra_details", "").strip() or "특별한 요청 없음"
    
    if stamina <= 30:
        level, radius, ratio = "Low", "도보 500m 이내", "Activity 20% : Healing 80%"
        guide = "- 총 도보 이동 극소화, 축제 핵심 30분 관람 후 쉼터/카페에서 80% 휴식."
    elif stamina <= 70:
        level, radius, ratio = "Moderate", "반경 2~3km", "Activity 50% : Healing 50%"
        guide = "- 하이라이트 관람(1~1.5시간)과 여유로운 쉼터(1시간)를 50:50으로 교차 배치."
    else:
        level, radius, ratio = "High", "반경 5km 이상", "Activity 80% : Healing 20%"
        guide = "- 축제 메인 프로그램, 체험 부스, 명소를 80% 비율로 활발히 탐방하는 풀코스."

    chain = ChatPromptTemplate.from_messages([("system", INTENT_ANALYSIS_PROMPT)]) | _get_llm(0.2) | StrOutputParser()
    try:
        raw_output = chain.invoke({
            "stamina": stamina,
            "companion": state.get("companion", "일반"),
            "extra_details": extra
        })
        intent_data = json.loads(re.sub(r"```json|```", "", raw_output).strip())
    except Exception:
        intent_data = {
            "core_needs": "안전하고 편안한 쉼표 중심 여행",
            "mobility_constraint": "보통" if stamina <= 30 else "경미",
            "parking_focus": "대규모 주차면수 우선 (진입 및 주차 안정성 중심)"
        }

    return {
        "activity_level": level, "movement_radius": radius,
        "activity_ratio": ratio, "strategy_guideline": guide,
        "intent_analysis": intent_data
    }


def classify_events_node(state: PipelineState) -> Dict[str, Any]:
    fest_programs = state.get("selected_festival", {}).get("programs", [])
    tourist_spots = state.get("tourist_spots", [])
    reservation_keywords = ["예약", "사전", "예매", "신청", "티켓", "선착순", "정원제", "도슨트", "클래스", "체험교실"]

    req, walk = [], []

    def classify_item(item_data, default_category):
        name = item_data.get("name", "프로그램")
        desc = item_data.get("description", "")
        category = item_data.get("category", default_category)
        target_text = f"{name} {desc} {category}"
        
        parsed_res = _parse_bool(item_data.get("reservation_required"))
        if parsed_res is not None:
            is_reserved = parsed_res
        else:
            is_reserved = any(k in target_text for k in reservation_keywords)
        
        default_tip = "공식 누리집 사전 예약 필수" if is_reserved else "현장 자유 참여 가능"
        booking_tip = item_data.get("booking_tip", default_tip)
        
        item = {"name": name, "category": category, "description": desc or "세부 정보 없음", "booking_tip": booking_tip}
        (req if is_reserved else walk).append(item)

    for p in fest_programs: classify_item(p, "축제 프로그램")
    for s in tourist_spots: classify_item(s, "쉼터")

    return {"event_info": {"reservation_required": req, "walk_in": walk}}


def generate_magazine_article_node(state: PipelineState) -> Dict[str, Any]:
    fest = state.get("selected_festival", {})
    
    def get_parking_size(p):
        try: return int(p.get("total_spaces") or p.get("capacity") or 0)
        except (ValueError, TypeError): return 0

    sorted_parking = sorted(state.get("parking_lots", []), key=get_parking_size, reverse=True)
    
    parking_str = "\n".join([f"- {p.get('name')}: 총 주차면수 {get_parking_size(p)}면 ({p.get('fee', '요금 정보 없음')})" for p in sorted_parking]) if sorted_parking else "현재 등록된 공영주차장 정보가 없습니다."
    rest_str = "\n".join([f"- {r.get('name')}: {r.get('menu', '대표식')} ({r.get('price', '가격 정보 없음')})" for r in state.get("model_restaurants", [])]) if state.get("model_restaurants") else "인근에 등록된 모범식당 정보가 없습니다."
    
    events = state.get("event_info", {})
    req_str = "\n".join([f"- **{e['name']}**: {e['description']} *(Tip: {e['booking_tip']})*" for e in events.get("reservation_required", [])]) or "등록된 사전 예약 필수 프로그램 없음"
    walk_str = "\n".join([f"- **{e['name']}**: {e['description']} *(Tip: {e['booking_tip']})*" for e in events.get("walk_in", [])]) or "등록된 상설 자유 이벤트 없음"

    prompt = ChatPromptTemplate.from_messages([
        ("system", MAGAZINE_EDITOR_SYSTEM_PROMPT),
        ("human", """[사용자 여행 정보]
- 선택 축제: {fest_name} ({fest_addr})
- 축제 소개: {fest_desc}
- 체력 수치: {stamina}% (활동 수준: {activity_level})
- 동반자: {companion}
- 자유 세부사항: "{extra_details}" (의도 분석: {intent_analysis})
- 전략 지침: {strategy_guideline}

■ 주차장: {parking_str}
■ 모범식당: {rest_str}
■ 예약 필수: {req_str}
■ 자유 입장: {walk_str}""")
    ])
    
    chain = prompt | _get_llm(0.3) | StrOutputParser()
    
    article_text = chain.invoke({
        "fest_name": fest.get("name", "로컬 축제"),
        "fest_addr": fest.get("address", state.get("region", "")),
        "fest_desc": fest.get("description", "지역 대표 축제"),
        "stamina": state.get("stamina", 50),
        "activity_level": state.get("activity_level", ""),
        "companion": state.get("companion", "일반"),
        "extra_details": state.get("extra_details", ""),
        "intent_analysis": str(state.get("intent_analysis", {})),
        "strategy_guideline": state.get("strategy_guideline", ""),
        "parking_str": parking_str, "rest_str": rest_str,
        "req_str": req_str, "walk_str": walk_str
    })

    return {"article_content": article_text}


def format_folium_pins_node(state: PipelineState) -> Dict[str, Any]:
    markers = []
    fest = state.get("selected_festival", {})
    
    # 1. 축제 핀 (위도, 경도 독립적 안전 검사 적용)
    f_lat, f_lng = _safe_lat(fest.get("lat")), _safe_lng(fest.get("lng"))
    if f_lat is not None and f_lng is not None:
        markers.append({
            "name": fest.get("name", "축제장"), "category": "festival",
            "lat": f_lat, "lng": f_lng,
            "icon": "flag", "color": "red",
            "desc": fest.get("description", "메인 축제 행사장"),
            "popup_title": f"🎪 {fest.get('name', '축제장')}"
        })

    # 2. 공영주차장 핀 (total_spaces 강제 int 형변환 적용)
    for p in state.get("parking_lots", []):
        lat, lng = _safe_lat(p.get("lat")), _safe_lng(p.get("lng"))
        if lat is not None and lng is not None:
            try:
                total = int(p.get("total_spaces") or p.get("capacity") or 0)
            except (ValueError, TypeError):
                total = 0
            
            fee = p.get('fee', '요금 정보 없음')
            markers.append({
                "name": p.get("name", "공영주차장"), "category": "parking",
                "lat": lat, "lng": lng,
                "icon": "car", "color": "blue", 
                "total_spaces": total,  # 프론트엔드 연동을 위한 순수 정수화
                "desc": f"총 {total}면 주차 공간 ({fee})",
                "popup_title": f"🅿️ {p.get('name')}"
            })

    # 3. 모범식당 핀
    for r in state.get("model_restaurants", []):
        lat, lng = _safe_lat(r.get("lat")), _safe_lng(r.get("lng"))
        if lat is not None and lng is not None:
            price = r.get("price", "가격 정보 없음")
            markers.append({
                "name": r.get("name", "모범식당"), "category": "restaurant",
                "lat": lat, "lng": lng,
                "icon": "cutlery", "color": "green",
                "menu": r.get("menu", "대표메뉴"), "price": price,
                "desc": f"대표메뉴: {r.get('menu', '')} ({price})",
                "popup_title": f"🍲 [모범식당] {r.get('name')}"
            })

    # 4. 쉼터 핀
    for s in state.get("tourist_spots", []):
        lat, lng = _safe_lat(s.get("lat")), _safe_lng(s.get("lng"))
        if lat is not None and lng is not None:
            markers.append({
                "name": s.get("name", "쉼터"), "category": "rest_spot",
                "lat": lat, "lng": lng,
                "icon": "leaf", "color": "orange",
                "desc": s.get("description", "한적한 힐링 쉼터"),
                "popup_title": f"🌿 [쉼터] {s.get('name')}"
            })

    return {"map_markers": markers}


# ==============================================================================
# 5. 워크플로우 조립 및 메인 함수
# ==============================================================================
def build_pipeline():
    wf = StateGraph(PipelineState)
    wf.add_node("analyze", analyze_stamina_and_intent)
    wf.add_node("classify", classify_events_node)
    wf.add_node("editor", generate_magazine_article_node)
    wf.add_node("format_pins", format_folium_pins_node)
    
    wf.add_edge(START, "analyze")
    wf.add_edge("analyze", "classify")
    wf.add_edge("classify", "editor")
    wf.add_edge("editor", "format_pins")
    wf.add_edge("format_pins", END)
    return wf.compile()

fest_and_rest_pipeline = build_pipeline()

def run_processing_pipeline(user_inputs: Dict[str, Any], api_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    api = api_data or {}
    
    raw_stamina = user_inputs.get("stamina", 50)
    try:
        stamina_val = int(raw_stamina)
    except (ValueError, TypeError):
        numbers = re.findall(r"\d+", str(raw_stamina))
        stamina_val = int(numbers[0]) if numbers else 50
    stamina_val = max(0, min(100, stamina_val))

    fest = user_inputs.get("selected_festival")
    
    initial_state = {
        "stamina": stamina_val,
        "companion": str(user_inputs.get("companion", "나홀로")),
        "region": str(user_inputs.get("region", "전국")),
        "selected_festival": fest if isinstance(fest, dict) else {"name": str(fest or "지역 축제")},
        "extra_details": str(user_inputs.get("extra_details", "")),
        "parking_lots": api.get("parking_lots", []),
        "model_restaurants": api.get("model_restaurants", []),
        "tourist_spots": api.get("tourist_spots", [])
    }
    
    final_state = fest_and_rest_pipeline.invoke(initial_state)

    return {
        "article_content": final_state.get("article_content", "매거진 기사를 작성하지 못했습니다."),
        "event_info": final_state.get("event_info", {"reservation_required": [], "walk_in": []}),
        "map_markers": final_state.get("map_markers", [])
    }
