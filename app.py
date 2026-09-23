"""
app.py - 초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
===================================================
팀원 A의 백엔드 LangGraph 모듈(agent.py)을 연동하는 Streamlit 웹 애플리케이션

※ agent.py의 공식 인터페이스(run_processing_pipeline)를 호출하여
  1. Fest & Rest 감각적인 매거진 기사 (article_content)
  2. 사전 예약 필수 vs 자유 참여 이벤트 분류 (event_info)
  3. Folium 지도 핀 메타데이터 (map_markers)
를 완벽히 렌더링합니다.
"""

import os
import sys
import json
import streamlit as st
import folium
from streamlit_folium import st_folium

# agent.py 백엔드 파이프라인 정식 인터페이스 임포트
try:
    from agent import run_processing_pipeline, PipelineState
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
        "default_extra": "부모님이 무릎이 안 좋으셔서 계단은 피하고 싶고 오래 못 걸어요. 차는 주차하기 편하고 넓은 곳이 좋겠습니다.",
        "programs": [
            {
                "name": "순천만 생태 해설사와 함께하는 갈대숲 도슨트 투어",
                "category": "체험/투어",
                "description": "전문 해설사의 설명과 함께하는 15인 정원제 생태 투어",
                "reservation_required": "Y",
                "booking_tip": "공식 누리집 사전 예약 필수"
            },
            {
                "name": "갈대 바람소리 야외 포토존 산책길",
                "category": "상설 관람",
                "description": "무장애 데크길을 따라 여유롭게 거니는 평지 자유 산책 코스",
                "reservation_required": "False",
                "booking_tip": "예약 없이 상시 자유 입장"
            },
            {
                "name": "흑두루미 소원 모빌 만들기 체험교실",
                "category": "가족 체험",
                "description": "어린이와 가족을 위한 친환경 모빌 공예 체험",
                "reservation_required": False,
                "booking_tip": "현장 접수 후 상시 참여 가능"
            }
        ],
        "parking_lots": [
            {
                "name": "순천만 에코촌 대형 공영주차장 (가장 넓음)",
                "lat": 34.8810,
                "lng": 127.5040,
                "total_spaces": 350,
                "fee": "무료",
                "distance": "축제장 도보 8분 / 갈대열차 연계"
            },
            {
                "name": "순천만습지 정문 제1주차장 (근접)",
                "lat": 34.8842,
                "lng": 127.5085,
                "total_spaces": 150,
                "fee": "3,000원",
                "distance": "축제장 매표소 도보 1분"
            }
        ],
        "model_restaurants": [
            {
                "name": "갈대골 착한 남도식당",
                "lat": 34.8835,
                "lng": 127.5075,
                "menu": "순천만 꼬막정식",
                "price": "12,000원",
                "desc": "순천시 지정 착한가격업소, 바가지 없는 정직한 손맛 (1층 입식 테이블)"
            }
        ],
        "tourist_spots": [
            {
                "name": "순천만 자연소리 쉼터 (그늘 정원)",
                "lat": 34.8850,
                "lng": 127.5100,
                "category": "쉼터",
                "description": "축제장 외곽 도보 5분 거리의 평지 그늘 벤치존"
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
        "default_extra": "아이들과 함께 편하게 쉬면서 체험 부스 둘러보고 싶고, 주차하기 편한 넓은 주차장을 선호합니다.",
        "programs": [
            {
                "name": "수삼 캐기 현장 체험 클래스",
                "category": "영농 체험",
                "description": "인삼밭에서 직접 수삼을 캐보는 사전 접수형 체험 프로그램",
                "reservation_required": "Y",
                "booking_tip": "공식 홈페이지 사전 신청 필수"
            },
            {
                "name": "인삼 아트 플라워 상설 전시관",
                "category": "문화 전시",
                "description": "인삼주와 인삼 꽃공예 작품을 감상하는 실내 자유 관람존",
                "reservation_required": "N",
                "booking_tip": "상시 무료 자유 관람"
            }
        ],
        "parking_lots": [
            {
                "name": "금산천 둔치 대형 임시주차장",
                "lat": 36.1015,
                "lng": 127.4920,
                "total_spaces": 450,
                "fee": "무료",
                "distance": "행사장 도보 7분 (셔틀버스 연계)"
            },
            {
                "name": "금산인삼관 지하공영주차장",
                "lat": 36.1030,
                "lng": 127.4888,
                "total_spaces": 180,
                "fee": "무료",
                "distance": "행사장 도보 2분"
            }
        ],
        "model_restaurants": [
            {
                "name": "금산 착한 삼계탕",
                "lat": 36.1040,
                "lng": 127.4880,
                "menu": "원조 인삼 삼계탕",
                "price": "13,000원",
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
        "default_extra": "공연과 축제 하이라이트를 즐긴 뒤, 조용한 수변 쉼터와 착한 안동찜닭을 맛보고 싶어요.",
        "programs": [
            {
                "name": "하회별신굿탈놀이 마당 특별 공연",
                "category": "공연",
                "description": "국가지정 무형문화재 하회별신굿 완판 공연",
                "reservation_required": "False",
                "booking_tip": "야외 공연장 선착순 자유 착석"
            },
            {
                "name": "나만의 하회탈 만들기 장인 워크숍",
                "category": "전통 공예",
                "description": "탈 제작 기능보유자와 함께하는 1:1 맞춤 목조각 클래스",
                "reservation_required": "True",
                "booking_tip": "사전 정원제 예약 필수"
            }
        ],
        "parking_lots": [
            {
                "name": "낙동강 둔치 대형 공영주차장",
                "lat": 36.5650,
                "lng": 128.7280,
                "total_spaces": 550,
                "fee": "무료",
                "distance": "축제장 도보 6분 (대형면수)"
            },
            {
                "name": "탈춤공원 제1공영주차장",
                "lat": 36.5680,
                "lng": 128.7300,
                "total_spaces": 220,
                "fee": "무료",
                "distance": "축제장 매표소 도보 3분"
            }
        ],
        "model_restaurants": [
            {
                "name": "안동 착한 안동찜닭",
                "lat": 36.5670,
                "lng": 128.7310,
                "menu": "정통 안동찜닭 (중)",
                "price": "28,000원",
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

# 딥그린 테마 & 모던 매거진 UI 스타일
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
    padding: 4px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    margin-top: 8px;
}
.card-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.event-badge-req {
    background: #fee2e2;
    color: #991b1b;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
}
.event-badge-walk {
    background: #dcfce7;
    color: #166534;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
}
</style>
""", unsafe_allow_html=True)

# GNB 헤더 배너
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🎪 Fest & Rest AI 매거진 오케스트레이터</div>
    <div class="hero-desc">
        체력(Stamina)에 기반한 3단계 전략 분기 & LangGraph 오케스트레이션으로 축제의 설렘과 쉼터의 평온함을 조율한 맞춤 매거진을 발행합니다.
    </div>
    <div class="engine-badge">⚡ agent.py LangGraph 파이프라인 정상 연동 완료 · GPT-4o-mini 엔진 가동</div>
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
        value=30,
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
        help="보행 제약, 쉼터 선호도, 주차 희망사항 등을 자연어로 작성하면 LLM이 숨은 의도를 추출하여 기사에 반영합니다."
    )

    # 외부 연계 데이터 확인 패널
    with st.expander("🗄️ 외부 연계 데이터셋 확인", expanded=False):
        st.caption("축제 프로그램, 공영주차장, 착한가격 모범식당, 쉼터 데이터셋입니다.")
        st.json({
            "programs": fest_data.get("programs", []),
            "parking_lots": fest_data.get("parking_lots", []),
            "model_restaurants": fest_data.get("model_restaurants", []),
            "tourist_spots": fest_data.get("tourist_spots", [])
        })

    # AI 맞춤 여정 생성 버튼
    run_button = st.button("🚀 AI 맞춤 매거진 & 큐레이션 발행", type="primary", use_container_width=True)


# ==============================================================================
# 4. 세션 상태 관리 및 agent.py 파이프라인 실행
# ==============================================================================
if "curation_result" not in st.session_state:
    st.session_state.curation_result = None

if run_button or st.session_state.curation_result is None:
    with st.spinner("🤖 agent.py [의도 분석 ➔ 이벤트 분류 ➔ 매거진 에디터 ➔ 지도 핀 가공] 파이프라인 실행 중..."):
        user_inputs = {
            "stamina": stamina,
            "companion": companion,
            "region": fest_data["region"],
            "selected_festival": {
                "name": fest_data["name"],
                "lat": fest_data["lat"],
                "lng": fest_data["lng"],
                "address": fest_data["address"],
                "description": fest_data["description"],
                "programs": fest_data.get("programs", [])
            },
            "extra_details": extra_details
        }
        api_data = {
            "parking_lots": fest_data.get("parking_lots", []),
            "model_restaurants": fest_data.get("model_restaurants", []),
            "tourist_spots": fest_data.get("tourist_spots", [])
        }

        try:
            # agent.py의 공식 단일 호출 함수 실행
            pipeline_output = run_processing_pipeline(user_inputs, api_data)
            st.session_state.curation_result = pipeline_output
            st.session_state.active_fest = fest_data
        except Exception as e:
            st.error(f"❌ LangGraph 파이프라인 실행 오류: {str(e)}")


# ==============================================================================
# 5. 결과 쇼케이스 렌더링 (매거진 기사 + 이벤트 체크리스트 + 지도 핀)
# ==============================================================================
result = st.session_state.get("curation_result")
active_fest = st.session_state.get("active_fest", fest_data)

if result:
    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": []})
    map_markers = result.get("map_markers", [])

    # 2단 메인 레이아웃: 좌측(매거진 기사 전문) / 우측(지도 및 이벤트 체크리스트)
    col_left, col_right = st.columns([6, 5], gap="large")

    with col_left:
        st.markdown("### 📖 🌿 Fest & Rest 큐레이션 매거진")
        st.markdown(f"""
        <div class="card-box" style="border-top: 5px solid #056608; line-height: 1.7;">
        """, unsafe_allow_html=True)
        st.markdown(article_content)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("### 🗺️ 맞춤 안심 동선 지도 (Folium)")
        
        # 지도 중심 좌표 설정
        fest_lat = active_fest.get("lat", 34.8845)
        fest_lng = active_fest.get("lng", 127.5090)
        
        m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="OpenStreetMap")

        # agent.py가 정제한 map_markers를 100% 활용하여 마커 렌더링
        for pin in map_markers:
            p_lat = pin.get("lat")
            p_lng = pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name = pin.get("name", "거점")
                p_cat = pin.get("category", "")
                p_title = pin.get("popup_title", f"📍 {p_name}")
                p_desc = pin.get("desc", "")
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")

                popup_html = f"<div style='font-family: Pretendard, sans-serif; min-width:180px;'>" \
                             f"<b style='font-size:1.05rem;'>{p_title}</b><hr style='margin:4px 0;'/>" \
                             f"<span style='font-size:0.85rem; color:#475569;'>{p_desc}</span></div>"

                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=p_name,
                    icon=folium.Icon(color=p_color, icon=p_icon)
                ).add_to(m)

        st_folium(m, width="100%", height=360)

        st.markdown("---")

        st.markdown("### 📌 프로그램 & 명소 예약 체크리스트")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])

        tab1, tab2 = st.tabs([f"🔒 사전 예약 필수 ({len(req_list)})", f"🔓 자유 참여 가능 ({len(walk_list)})"])

        with tab1:
            if req_list:
                for item in req_list:
                    st.markdown(f"""
                    <div style="background:#fff5f5; border:1px solid #fed7d7; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#991b1b;">{item.get('name')}</span>
                            <span class="event-badge-req">사전 예약 필수</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4a5568; margin-bottom:4px;">{item.get('description')}</div>
                        <div style="font-size:0.8rem; color:#c53030; font-weight:600;">💡 Tip: {item.get('booking_tip')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("등록된 사전 예약 필수 프로그램이 없습니다.")

        with tab2:
            if walk_list:
                for item in walk_list:
                    st.markdown(f"""
                    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#166534;">{item.get('name')}</span>
                            <span class="event-badge-walk">자유 참여 가능</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4a5568; margin-bottom:4px;">{item.get('description')}</div>
                        <div style="font-size:0.8rem; color:#15803d; font-weight:600;">💡 Tip: {item.get('booking_tip')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("등록된 자유 참여 프로그램이 없습니다.")

        with st.expander("🛠️ agent.py 원본 출력 딕셔너리 JSON 확인"):
            st.json(result)
