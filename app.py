"""
app.py - 초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
===================================================
팀원 A의 백엔드 LangGraph 모듈(agent.py)을 연동하는 Streamlit 웹 애플리케이션

※ 주의: agent.py 파일은 절대 수정하지 않으며, agent.py의 핵심 워크플로우를 그대로 임포트하여 구동합니다.
"""

import os
import sys
import json
import streamlit as st
import folium
from streamlit_folium import st_folium

# agent.py의 핵심 워크플로우 및 상태 구조체 임포트 (agent.py 수정 없음)
try:
    from agent import processing_workflow, ProcessingState
except ImportError as e:
    st.error(f"agent.py 임포트 오류: {e}")
    st.stop()


# ==============================================================================
# 1. 프리셋 축제 및 data.py 연계 샘플 데이터
# ==============================================================================
FESTIVAL_PRESETS = {
    "순천만 갈대축제": {
        "name": "순천만 갈대축제",
        "region": "전라남도",
        "lat": 34.8845,
        "lng": 127.5090,
        "address": "전남 순천시 순천만길 513-25",
        "description": "광활한 황금빛 갈대밭과 흑두루미가 반겨주는 대한민국 대표 가을 생태 힐링 축제",
        "default_extra": "부모님이 무릎이 안 좋으셔서 계단은 못 가고 오래 못 걸어요. 차는 축제장과 제일 가까운 곳에 대고 싶습니다.",
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
    },
    "금산 세계인삼축제": {
        "name": "금산 세계인삼축제",
        "region": "충청남도",
        "lat": 36.1032,
        "lng": 127.4891,
        "address": "충남 금산군 금산읍 인삼광장로 30",
        "description": "생명의 고향 금산에서 펼쳐지는 건강 힐링 & 활력 충전 전통 축제",
        "default_extra": "아이들과 함께 체험 부스 위주로 둘러보고, 주차 공간 넉넉한 곳을 선호합니다.",
        "parking_lots": [
            {
                "name": "금산인삼관 지하공영주차장",
                "lat": 36.1030,
                "lng": 127.4888,
                "available_spaces": 85,
                "total_spaces": 200,
                "fee": "무료",
                "distance": "행사장 도보 2분"
            },
            {
                "name": "금산천 둔치 하상 임시주차장",
                "lat": 36.1015,
                "lng": 127.4920,
                "available_spaces": 230,
                "total_spaces": 350,
                "fee": "무료",
                "distance": "행사장 도보 7분 (셔틀버스 운행)"
            }
        ],
        "model_restaurants": [
            {
                "name": "금산 착한 삼계탕",
                "lat": 36.1040,
                "lng": 127.4880,
                "menu": "원조 인삼 삼계탕",
                "price": "13,000원",
                "is_good_price": True,
                "desc": "금산군 지정 모범음식점, 국산 수삼 듬뿍 보양식"
            }
        ],
        "tourist_spots": [
            {
                "name": "남이자연휴양림 피톤치드 숲길",
                "lat": 36.0820,
                "lng": 127.4520,
                "category": "힐링 숲",
                "description": "축제 인파를 벗어나 편백나무 숲에서 즐기는 조용한 산림욕 명소"
            }
        ]
    },
    "안동 국제탈춤페스티벌": {
        "name": "안동 국제탈춤페스티벌",
        "region": "경상북도",
        "lat": 36.5684,
        "lng": 128.7296,
        "address": "경북 안동시 육사로 239 탈춤공원",
        "description": "신명나는 탈과 춤으로 일상의 스트레스를 날려버리는 한국 대표 문화 축제",
        "default_extra": "공연과 축제 하이라이트를 즐긴 뒤, 조용한 야경 쉼터와 착한 안동찜닭을 맛보고 싶어요.",
        "parking_lots": [
            {
                "name": "탈춤공원 제1공영주차장",
                "lat": 36.5680,
                "lng": 128.7300,
                "available_spaces": 42,
                "total_spaces": 250,
                "fee": "무료",
                "distance": "축제장 매표소 도보 3분"
            },
            {
                "name": "낙동강 둔치 대형 공영주차장",
                "lat": 36.5650,
                "lng": 128.7280,
                "available_spaces": 310,
                "total_spaces": 500,
                "fee": "무료",
                "distance": "축제장 도보 6분 (진출입 편리)"
            }
        ],
        "model_restaurants": [
            {
                "name": "안동 착한 안동찜닭",
                "lat": 36.5670,
                "lng": 128.7310,
                "menu": "정통 안동찜닭 (중)",
                "price": "28,000원",
                "is_good_price": True,
                "desc": "지자체 인증 착한가격업소, 정직한 원재료의 푸짐한 찜닭"
            }
        ],
        "tourist_spots": [
            {
                "name": "월영교 수변 산책로 & 문보트",
                "lat": 36.5770,
                "lng": 128.7590,
                "category": "수변 쉼터",
                "description": "국내 최장 목책교에서 즐기는 잔잔한 낙동강 수변 힐링"
            }
        ]
    }
}


# ==============================================================================
# 2. Streamlit 기본 페이지 설정 및 스타일
# ==============================================================================
st.set_page_config(
    page_title="Fest & Rest AI - 초개인화 로컬 축제 & 쉼터 큐레이션",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 딥그린 테마 & 모던 UI 스타일
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif; }

.hero-banner {
    background: linear-gradient(135deg, #056608 0%, #0d8212 50%, #174219 100%);
    color: #ffffff;
    padding: 24px 30px;
    border-radius: 16px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px rgba(5, 102, 8, 0.15);
}
.hero-title {
    font-size: 1.8rem;
    font-weight: 800;
    margin-bottom: 6px;
}
.hero-desc {
    font-size: 0.95rem;
    opacity: 0.92;
    line-height: 1.5;
}
.engine-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.22);
    padding: 3px 12px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 700;
    margin-top: 8px;
}
.card-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}
.node-badge {
    background: #eaf5ea;
    color: #056608;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.8rem;
}
.tag-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.76rem;
    font-weight: 700;
}
.tag-parking { background: #e0f2fe; color: #0369a1; }
.tag-festival { background: #fef3c7; color: #b45309; }
.tag-rest { background: #dcfce7; color: #15803d; }
.tag-food { background: #ffe4e6; color: #be123c; }
.tag-attraction { background: #f3e8ff; color: #7e22ce; }
</style>
""", unsafe_allow_html=True)

# GNB 헤더 배너
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🎪 Fest & Rest AI 오케스트레이터</div>
    <div class="hero-desc">
        체력(Stamina)에 기반한 3단계 전략 분기 & LangGraph 오케스트레이션으로 인파 피로 없는 맞춤 축제·쉼터 여정을 완성합니다.
    </div>
    <div class="engine-badge">⚡ agent.py LangGraph Engine Connected · GPT-4o-mini Ready</div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. 사이드바: 프론트엔드 입력 제어 덱
# ==============================================================================
with st.sidebar:
    st.header("⚙️ 여행자 조건 설정")

    # 체력(stamina) 슬라이더
    stamina = st.slider(
        "🪫 내 체력 배터리 (Stamina)",
        min_value=0,
        max_value=100,
        value=25,
        step=5,
        help="30% 이하: 쉼터 80% 집중형 (도보 500m) | 30~70%: 황금 밸런스형 | 70% 이상: 풀코스 액티비티"
    )

    if stamina <= 30:
        st.error(f"🪫 체력 {stamina}%: [Low 분기] 도보 500m 이내 / 쉼터 80% 집중")
    elif stamina <= 70:
        st.warning(f"🔋 체력 {stamina}%: [Moderate 분기] 반경 2~3km / 50:50 황금 밸런스")
    else:
        st.success(f"⚡ 체력 {stamina}%: [High 분기] 반경 5km+ / 80% 풀코스 액티비티")

    st.markdown("---")

    # 동반자 선택
    companion = st.selectbox(
        "👥 동반자 유형",
        options=["부모님 (연로하심)", "나홀로 힐링", "연인/커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"],
        index=0
    )

    # 방문할 축제 선택
    fest_key = st.selectbox(
        "📍 방문할 로컬 축제",
        options=list(FESTIVAL_PRESETS.keys()),
        index=0
    )
    fest_data = FESTIVAL_PRESETS[fest_key]

    # 세부 요구사항 텍스트
    st.markdown("💬 **세부 요청사항**")
    extra_details = st.text_area(
        "자유 작성 요구사항 (LLM 심층 분석 대상)",
        value=fest_data.get("default_extra", "무리 없이 편안하게 즐기고 싶어요."),
        height=85,
        help="보행 제약, 쉼터 선호도, 주차 희망사항 등을 자연어로 작성하면 LLM이 숨은 의도를 추출합니다."
    )

    # 외부 연계 데이터 확인 패널
    with st.expander("🗄️ 외부 연계 데이터 (주차/식당/쉼터)", expanded=False):
        st.caption("축제장 주변의 공영주차장, 착한가격 모범식당, 쉼터 데이터셋입니다.")
        st.json({
            "parking_lots": fest_data["parking_lots"],
            "model_restaurants": fest_data["model_restaurants"],
            "tourist_spots": fest_data["tourist_spots"]
        })

    # AI 맞춤 여정 생성 버튼
    run_button = st.button("🚀 AI 맞춤 여정 생성 (LangGraph 가동)", type="primary", use_container_width=True)


# ==============================================================================
# 4. 세션 상태 관리 및 LangGraph 실행
# ==============================================================================
if "curation_state" not in st.session_state:
    st.session_state.curation_state = None

if run_button or st.session_state.curation_state is None:
    with st.spinner("🤖 agent.py [노드 1 의도 분석 ➔ 조건부 분기 전략 ➔ 노드 2 데이터 통합 에이전트] 파이프라인 연산 중..."):
        initial_input: ProcessingState = {
            "stamina": stamina,
            "companion": companion,
            "region": fest_data["region"],
            "selected_festival": {
                "name": fest_data["name"],
                "lat": fest_data["lat"],
                "lng": fest_data["lng"],
                "address": fest_data["address"],
                "description": fest_data["description"]
            },
            "extra_details": extra_details,
            "parking_lots": fest_data["parking_lots"],
            "model_restaurants": fest_data["model_restaurants"],
            "tourist_spots": fest_data["tourist_spots"],
            "activity_level": "",
            "movement_radius": "",
            "activity_ratio": "",
            "intent_analysis": {},
            "strategy_guideline": "",
            "custom_route": {}
        }
        try:
            # agent.py의 processing_workflow 실행
            result_state = processing_workflow.invoke(initial_input)
            st.session_state.curation_state = result_state
            st.session_state.active_fest = fest_data
        except Exception as e:
            st.error(f"❌ LangGraph 워크플로우 실행 오류: {str(e)}")


# ==============================================================================
# 5. 결과 큐레이션 쇼케이스 표출
# ==============================================================================
res = st.session_state.get("curation_state")
active_fest = st.session_state.get("active_fest", fest_data)

if res:
    custom_route = res.get("custom_route", {})
    intent = res.get("intent_analysis", {})

    theme_slogan = custom_route.get("route_theme", "Fest & Rest 안심 맞춤 여정")
    golden_time = custom_route.get("crowd_avoidance_golden_time", "오전 골든타임")

    # 상단 요약 슬로건 배너
    st.markdown(f"""
    <div style="background:#f4f9f4; border-left:5px solid #056608; border-radius:8px; padding:16px 20px; margin-bottom:20px;">
        <div style="font-size:1.25rem; font-weight:800; color:#056608; margin-bottom:4px;">✨ {theme_slogan}</div>
        <div style="font-size:0.92rem; color:#2b2b2b;">
            ⏰ <b>인파 회피 추천 골든타임:</b> {golden_time} &nbsp;|&nbsp; 
            🎯 <b>설계 비율:</b> {res.get('activity_ratio')} &nbsp;|&nbsp; 
            🚶 <b>권장 반경:</b> {res.get('movement_radius')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2단 레이아웃
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown("### 🧠 1. AI 심층 분석 & 분기 전략")
        st.markdown(f"""
        <div class="card-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span class="node-badge">노드 1 : 의도 & 컨디션 분석</span>
                <span style="font-weight:700; color:#056608;">활동 수준: {res.get('activity_level')}</span>
            </div>
            <div style="font-size:0.9rem; margin-bottom:6px;">
                <b>🔍 추출된 핵심 니즈:</b> {intent.get('core_needs', '무리 없는 편안한 힐링')}
            </div>
            <div style="font-size:0.86rem; color:#475569; margin-bottom:4px;">
                • <b>보행 제약:</b> {intent.get('mobility_constraint', '보통')} &nbsp;|&nbsp; 
                <b>주차 전략:</b> {intent.get('parking_strategy', '최근접 주차장 우선')}
            </div>
            <div style="font-size:0.86rem; color:#475569;">
                • <b>집중 케어 포인트:</b> {", ".join(intent.get('key_care_points', ['도보 이동 최소화', '휴식 안배']))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🧭 확정된 전략 지침 (Conditional Edge 산출물)", expanded=False):
            st.info(res.get("strategy_guideline", "전략 지침 없음"))

        st.markdown("### 🚗 & 🍱 데이터 통합 매칭 결과")
        col_p, col_r = st.columns(2)
        
        with col_p:
            parking = custom_route.get("selected_parking", {})
            st.markdown(f"""
            <div class="card-box" style="border-top:4px solid #0284c7;">
                <div style="font-size:0.8rem; font-weight:700; color:#0284c7;">🅿️ 추천 공영주차장</div>
                <div style="font-size:1.02rem; font-weight:800; margin:4px 0;">{parking.get('name', '추천 주차장')}</div>
                <div style="font-size:0.85rem; color:#0369a1; margin-bottom:4px;">
                    <b>잔여:</b> {parking.get('available_spaces', 0)}대 주차 가능
                </div>
                <div style="font-size:0.82rem; color:#64748b;">{parking.get('reason', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_r:
            restaurant = custom_route.get("selected_restaurant", {})
            st.markdown(f"""
            <div class="card-box" style="border-top:4px solid #e11d48;">
                <div style="font-size:0.8rem; font-weight:700; color:#e11d48;">🍱 안심 착한 모범식당</div>
                <div style="font-size:1.02rem; font-weight:800; margin:4px 0;">{restaurant.get('name', '모범식당')}</div>
                <div style="font-size:0.85rem; color:#be123c; margin-bottom:4px;">
                    <b>메뉴:</b> {restaurant.get('menu', '대표 정식')} ({restaurant.get('price', '착한가격')})
                </div>
                <div style="font-size:0.82rem; color:#64748b;">{restaurant.get('reason', '')}</div>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("🛠️ LangGraph ProcessingState 원본 JSON 보기"):
            st.json(res)

    with col_right:
        st.markdown("### 🗺️ 맞춤 동선 시각화 지도")
        fest_lat = active_fest.get("lat", 34.8845)
        fest_lng = active_fest.get("lng", 127.5090)

        m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="cartodbpositron")

        # 축제장 (Red Star)
        folium.Marker(
            [fest_lat, fest_lng],
            popup=f"<b>🎪 {active_fest.get('name')}</b><br>{active_fest.get('address')}",
            tooltip=f"축제장: {active_fest.get('name')}",
            icon=folium.Icon(color="red", icon="star")
        ).add_to(m)

        # 주차장 (Blue Info)
        for p in active_fest.get("parking_lots", []):
            folium.Marker(
                [p.get("lat", fest_lat), p.get("lng", fest_lng)],
                popup=f"<b>🅿️ {p.get('name')}</b><br>주차가능: {p.get('available_spaces')}대<br>요금: {p.get('fee')}",
                tooltip=f"주차장: {p.get('name')}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        # 모범식당 (Orange Cutlery)
        for r in active_fest.get("model_restaurants", []):
            folium.Marker(
                [r.get("lat", fest_lat), r.get("lng", fest_lng)],
                popup=f"<b>🍱 {r.get('name')}</b><br>{r.get('menu')} ({r.get('price')})",
                tooltip=f"모범식당: {r.get('name')}",
                icon=folium.Icon(color="orange", icon="cutlery")
            ).add_to(m)

        # 쉼터 (Green Leaf)
        for s in active_fest.get("tourist_spots", []):
            folium.Marker(
                [s.get("lat", fest_lat), s.get("lng", fest_lng)],
                popup=f"<b>🌿 {s.get('name')}</b><br>{s.get('description')}",
                tooltip=f"쉼터: {s.get('name')}",
                icon=folium.Icon(color="green", icon="leaf")
            ).add_to(m)

        st_folium(m, width="100%", height=320)

        st.markdown("### ⏱️ 시간대별 맞춤 여정 타임테이블")
        timeline = custom_route.get("timeline", [])

        type_map = {
            "Parking": ("🅿️ 주차", "tag-parking"),
            "Festival": ("🎪 축제", "tag-festival"),
            "Rest": ("🌿 쉼터", "tag-rest"),
            "Food": ("🍽️ 식사", "tag-food"),
            "Attraction": ("✨ 명소", "tag-attraction")
        }

        for item in timeline:
            t_type = item.get("type", "Attraction")
            t_label, t_class = type_map.get(t_type, ("📍 일정", "tag-attraction"))

            st.markdown(f"""
            <div style="display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-bottom:1px solid #f1f5f9;">
                <div style="min-width:85px; font-weight:700; color:#475569; font-size:0.85rem; padding-top:2px;">
                    {item.get('time', '시간')}
                </div>
                <div style="flex-grow:1;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">
                        <span class="tag-badge {t_class}">{t_label}</span>
                        <span style="font-weight:700; font-size:0.93rem; color:#1e293b;">{item.get('spot_name')}</span>
                    </div>
                    <div style="font-size:0.84rem; color:#64748b; line-height:1.4;">
                        {item.get('description')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
