"""
app.py - 초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
===================================================
팀원 A의 백엔드 LangGraph 모듈(agent.py)과 팀원 B의 공공데이터 모듈(data.py)을
100% 실시간 연동하는 순수 공공데이터 기반 Streamlit 웹 애플리케이션

※ 가짜/샘플 데이터(FESTIVAL_PRESETS)를 완전히 배제하고,
  실제 공공데이터(data.py)만을 기반으로 초개인화 맞춤 매거진 및 지도를 발행합니다.
"""

import os
import sys
import json
import html
import streamlit as st
import folium
from streamlit_folium import st_folium

# agent.py 백엔드 파이프라인 정식 인터페이스 임포트
try:
    from agent import run_processing_pipeline, PipelineState
except ImportError as e:
    st.error(f"agent.py 임포트 오류: {e}")
    st.stop()

# data.py 실제 공공데이터 엔지니어링 모듈 연동
try:
    from data import get_festival_infra_bundle, get_festivals
except ImportError as e:
    st.error(f"data.py 임포트 오류: {e}")
    st.stop()


# ==============================================================================
# 1. 대한민국 17개 광역 행정구역 마스터 목록
# ==============================================================================
ADMIN_REGIONS = [
    "전국 전체",
    "서울특별시",
    "부산광역시",
    "대구광역시",
    "인천광역시",
    "광주광역시",
    "대전광역시",
    "울산광역시",
    "세종특별자치시",
    "경기도",
    "강원특별자치도",
    "충청북도",
    "충청남도",
    "전북특별자치도",
    "전라남도",
    "경상북도",
    "경상남도",
    "제주특별자치도"
]


# ==============================================================================
# 2. Streamlit 기본 페이지 설정 및 스타일
# ==============================================================================
st.set_page_config(
    page_title="Fest & Rest AI - 100% 공공데이터 기반 축제 & 쉼터 큐레이션",
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
        100% 실제 공공데이터(문화축제표준데이터, 주차장, 착한가격업소, 한국관광공사 TourAPI)와 체력 기반 3단계 LangGraph 파이프라인으로 맞춤 매거진을 발행합니다.
    </div>
    <div class="engine-badge">⚡ 순수 공공데이터 모듈(data.py) & LangGraph AI(agent.py) 정식 연동 가동 중</div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 3. 사이드바: 100% 공공데이터 기반 동적 지역 및 축제 검색
# ==============================================================================
with st.sidebar:
    st.header("⚙️ 여행자 조건 설정")

    # 1. 광역 행정구역 선택
    selected_region = st.selectbox(
        "📍 1. 여행 목적지 (광역 행정구역)",
        options=ADMIN_REGIONS,
        index=0,
        help="원하는 지역을 선택하면 해당 지역의 실제 공공데이터 축제 목록이 조회됩니다."
    )

    # [지침 1 준수] 2. 방문 월(Month) 선택 필터 추가
    month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
    selected_month = st.selectbox(
        "🗓️ 2. 방문 월 (Month)",
        options=month_options,
        index=0,
        help="축제가 개최되는 월을 선택하여 필터링합니다."
    )
    selected_month_int = int(selected_month.replace("월", "")) if selected_month != "전체" else None

    # 3. 실제 공공데이터 축제 목록 조회 (data.py) - 지역 및 월 조건 전달
    try:
        festivals_list = get_festivals(region=selected_region, month=selected_month_int)
    except Exception as e:
        st.error(f"⚠️ 축제 공공데이터 조회 실패: {e}")
        festivals_list = []

    fest_data = None

    # 4. 실제 축제 선택 selectbox
    if not festivals_list:
        month_label = f" ({selected_month})" if selected_month != "전체" else ""
        st.warning(f"선택하신 '{selected_region}'{month_label}에 등록된 축제가 없습니다.")
    else:
        # 축제명 매핑 딕셔너리 생성 (중복 방지 및 빠른 조회)
        festival_options = {f["name"]: f for f in festivals_list}
        selected_fest_name = st.selectbox(
            f"🎪 3. 방문할 로컬 축제 (총 {len(festival_options)}개 검색됨)",
            options=list(festival_options.keys()),
            index=0
        )
        fest_data = festival_options[selected_fest_name]

    st.markdown("---")

    # 5. 체력(stamina) 슬라이더
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

    # 6. 동반자 선택
    companion = st.selectbox(
        "👥 동반자 유형",
        options=["부모님 (연로하심)", "나홀로 힐링", "연인/커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"],
        index=0
    )

    # 7. 세부 요구사항 텍스트
    st.markdown("💬 **세부 요청사항**")
    default_request = "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 차는 주차하기 편하고 넓은 곳이 좋겠습니다." if "부모님" in companion else "무리 없이 편안하게 즐기고 싶어요."
    extra_details = st.text_area(
        "자유 작성 요구사항 (LLM 심층 분석 대상)",
        value=default_request,
        height=85,
        max_chars=1000,
        help="보행 제약, 쉼터 선호도, 주차 희망사항 등을 자연어로 작성하면 LLM이 숨은 의도를 추출하여 기사에 반영합니다."
    )

    # [지침 2 준수] 8. 축제 정보 시각화 카드 (사이드바에는 간결한 요약 카드 배치)
    if fest_data:
        st.markdown("---")
        st.markdown("### 🏷️ 축제 프로필 미리보기")
        fest_name_safe = html.escape(str(fest_data.get("name", "축제명 미상")))
        fest_dates_safe = html.escape(str(fest_data.get("dates", "일정 확인 중")))
        fest_addr_safe = html.escape(str(fest_data.get("address", "장소 정보 없음")))
        fest_desc_safe = html.escape(str(fest_data.get("description", "소개 정보가 준비 중입니다.")))

        st.markdown(f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:14px; margin-top:8px; margin-bottom:14px;">
            <div style="font-weight:800; font-size:1.02rem; color:#0f172a; margin-bottom:6px;">🎪 {fest_name_safe}</div>
            <div style="font-size:0.83rem; color:#475569; margin-bottom:4px;"><strong>📅 기간:</strong> {fest_dates_safe}</div>
            <div style="font-size:0.83rem; color:#475569; margin-bottom:8px;"><strong>📍 위치:</strong> {fest_addr_safe}</div>
            <div style="font-size:0.82rem; color:#334155; line-height:1.5; background:#ffffff; border-radius:6px; padding:9px; border:1px solid #f1f5f9;">
                {fest_desc_safe}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # AI 맞춤 여정 생성 버튼
    run_button = st.button(
        "🚀 AI 맞춤 매거진 & 큐레이션 발행",
        type="primary",
        use_container_width=True,
        disabled=(fest_data is None)
    )


# ==============================================================================
# 4. 세션 상태 관리 및 100% 공공데이터 파이프라인 실행
# ==============================================================================
if "curation_result" not in st.session_state:
    st.session_state.curation_result = None

# [첫 진입 시 LLM 자동 실행 방지] 오직 사용자가 발행 버튼을 클릭했을 때만 파이프라인 가동
if run_button:
    if not fest_data:
        st.error("선택된 축제 정보가 없습니다. 축제를 먼저 선택해 주세요.")
    else:
        with st.spinner("🤖 agent.py [의도 분석 ➔ 이벤트 분류 ➔ 매거진 에디터 ➔ 지도 핀 가공] 파이프라인 실행 중..."):
            user_inputs = {
                "stamina": stamina,
                "companion": companion,
                "region": fest_data.get("region", selected_region),
                "selected_festival": {
                    "name": fest_data.get("name", "로컬 축제"),
                    "lat": fest_data.get("lat"),
                    "lng": fest_data.get("lng"),
                    "address": fest_data.get("address", ""),
                    "description": fest_data.get("description", ""),
                    "programs": fest_data.get("programs", [])
                },
                "extra_details": extra_details
            }

            p_lots, m_rests, t_spots = [], [], []

            # [지침 2 준수] 100% 실제 공공데이터 조회 (가짜/샘플 폴백 완전 배제)
            # 결과가 0건이면 억지로 채우지 않고 정직하게 빈 리스트([])를 전달함
            try:
                infra = get_festival_infra_bundle(
                    fest_lat=fest_data.get("lat", 0.0),
                    fest_lng=fest_data.get("lng", 0.0),
                    radius_m=3000
                )
                p_lots = infra.get("parking_lots", [])
                m_rests = infra.get("model_restaurants", [])
                t_spots = infra.get("tourist_spots", [])
            except Exception as e:
                # [지침 1 준수] 공공데이터 API 연동 장애 발생 시 사용자에게 명시적으로 에러 표시
                st.error(f"⚠️ 공공데이터 API 연동 장애가 발생했습니다: {e}")
                p_lots, m_rests, t_spots = [], [], []

            api_data = {
                "parking_lots": p_lots,
                "model_restaurants": m_rests,
                "tourist_spots": t_spots
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

if result and active_fest:
    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": []})
    map_markers = result.get("map_markers", [])

    # 2단 메인 레이아웃: 좌측(매거진 기사 전문) / 우측(지도 및 이벤트 체크리스트)
    col_left, col_right = st.columns([6, 5], gap="large")

    with col_left:
        st.markdown("### 📖 🌿 Fest & Rest 큐레이션 매거진")
        # [지침 4 준수] 축제 메인 비주얼 사진 (오해 방지용 직관적 캡션 명시)
        st.image(
            "https://images.unsplash.com/photo-1533174000243-c782a20e4010?q=80&w=1200&auto=format&fit=crop",
            caption="🎨 축제 분위기 참고 이미지 · 실제 행사 사진이 아닙니다",
            use_container_width=True
        )
        st.markdown(f"""
        <div class="card-box" style="border-top: 5px solid #056608; line-height: 1.7;">
        """, unsafe_allow_html=True)
        st.markdown(article_content)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("### 🗺️ 맞춤 안심 동선 지도 (Folium)")
        
        # [지침 4 준수] 축제 좌표 확인 및 임의 하드코딩 제거 (좌표 누락 시 대한민국 전도 중심 [36.5, 127.5], zoom=7로 줌아웃)
        fest_lat = active_fest.get("lat")
        fest_lng = active_fest.get("lng")

        if not fest_lat or not fest_lng:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="OpenStreetMap")
        else:
            m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="OpenStreetMap")

        # agent.py가 정제한 map_markers를 100% 활용하여 마커 렌더링
        for pin in map_markers:
            p_lat = pin.get("lat")
            p_lng = pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name_raw = pin.get("name", "거점")
                p_name = html.escape(str(p_name_raw))
                p_cat = html.escape(str(pin.get("category", "")))
                p_title = html.escape(str(pin.get("popup_title", f"📍 {p_name_raw}")))
                p_desc = html.escape(str(pin.get("desc", "")))
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")
                # FontAwesome 아이콘 호환성 접두사 지정 (깨짐 방지)
                p_prefix = "fa" if p_icon in ["cutlery", "car", "leaf", "flag"] else "glyphicon"

                popup_html = f"<div style='font-family: Pretendard, sans-serif; min-width:180px;'>" \
                             f"<b style='font-size:1.05rem;'>{p_title}</b><hr style='margin:4px 0;'/>" \
                             f"<span style='font-size:0.85rem; color:#475569;'>{p_desc}</span></div>"

                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=p_name,
                    icon=folium.Icon(color=p_color, icon=p_icon, prefix=p_prefix)
                ).add_to(m)

        st_folium(m, width="100%", height=360)

        st.markdown("---")

        st.markdown("### 📌 프로그램 & 명소 예약 체크리스트")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        unknown_list = event_info.get("unknown", [])

        # [지침 2 준수] 예약 필수 vs 자유 참여 vs 현장 확인 필요 3단계 탭 구성
        tab1, tab2, tab3 = st.tabs([
            f"🔒 사전 예약 필수 ({len(req_list)})",
            f"🔓 자유 참여 가능 ({len(walk_list)})",
            f"🤔 현장 확인 필요 ({len(unknown_list)})"
        ])

        with tab1:
            if req_list:
                for item in req_list:
                    req_name = html.escape(str(item.get('name', '')))
                    req_desc = html.escape(str(item.get('description', '')))
                    req_tip = html.escape(str(item.get('booking_tip', '')))
                    st.markdown(f"""
                    <div style="background:#fff5f5; border:1px solid #fed7d7; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#991b1b;">{req_name}</span>
                            <span class="event-badge-req">사전 예약 필수</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4a5568; margin-bottom:4px;">{req_desc}</div>
                        <div style="font-size:0.8rem; color:#c53030; font-weight:600;">💡 Tip: {req_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("등록된 사전 예약 필수 프로그램이 없습니다.")

        with tab2:
            if walk_list:
                for item in walk_list:
                    walk_name = html.escape(str(item.get('name', '')))
                    walk_desc = html.escape(str(item.get('description', '')))
                    walk_tip = html.escape(str(item.get('booking_tip', '')))
                    st.markdown(f"""
                    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#166534;">{walk_name}</span>
                            <span class="event-badge-walk">자유 참여 가능</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4a5568; margin-bottom:4px;">{walk_desc}</div>
                        <div style="font-size:0.8rem; color:#15803d; font-weight:600;">💡 Tip: {walk_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("등록된 자유 참여 프로그램이 없습니다.")

        with tab3:
            if unknown_list:
                for item in unknown_list:
                    unk_name = html.escape(str(item.get('name', '')))
                    unk_desc = html.escape(str(item.get('description', '')))
                    unk_tip = html.escape(str(item.get('booking_tip', '공식 누리집 또는 현장 안내소 문의 요망')))
                    st.markdown(f"""
                    <div style="background:#fffbeb; border:1px solid #fef3c7; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#b45309;">{unk_name}</span>
                            <span class="event-badge-req" style="background:#fef3c7; color:#92400e;">현장 확인 필요</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4a5568; margin-bottom:4px;">{unk_desc}</div>
                        <div style="font-size:0.8rem; color:#b45309; font-weight:600;">💡 Tip: {unk_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("등록된 현장 확인 필요 프로그램이 없습니다.")

        st.markdown("---")

        # [지침 2, 5 준수] 착한가격업소 & 인근 관광·휴식 명소 추천 UI 카드
        st.markdown("### 🍽️ 착한가격업소 & 🌿 인근 관광·휴식 명소 추천")

        restaurant_pins = [p for p in map_markers if p.get("category") == "restaurant"]
        rest_spot_pins = [p for p in map_markers if p.get("category") == "rest_spot"]

        tab_rest, tab_spot = st.tabs([
            f"🍽️ 착한가격업소 ({len(restaurant_pins)})",
            f"🌿 인근 관광·휴식 명소 ({len(rest_spot_pins)})"
        ])

        with tab_rest:
            if restaurant_pins:
                for r in restaurant_pins:
                    r_name = html.escape(str(r.get("name", "착한가격업소")))
                    r_menu = html.escape(str(r.get("menu", "대표메뉴")))
                    r_price = html.escape(str(r.get("price", "가격 정보 없음")))
                    st.markdown(f"""
                    <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#166534;">🍲 {r_name}</span>
                            <span style="background:#dcfce7; color:#15803d; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.78rem;">착한가격업소</span>
                        </div>
                        <div style="font-size:0.85rem; color:#374151; margin-bottom:3px;"><strong>대표메뉴:</strong> {r_menu}</div>
                        <div style="font-size:0.82rem; color:#15803d; font-weight:600;">💰 가격: {r_price}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("축제장 인근에 등록된 착한가격업소 정보가 없습니다.")

        with tab_spot:
            if rest_spot_pins:
                for s in rest_spot_pins:
                    s_name = html.escape(str(s.get("name", "관광·휴식 명소")))
                    s_desc = html.escape(str(s.get("desc", "인근 관광 및 휴식 명소")))
                    st.markdown(f"""
                    <div style="background:#fffbeb; border:1px solid #fef3c7; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <span style="font-weight:700; font-size:0.95rem; color:#92400e;">🌿 {s_name}</span>
                            <span style="background:#fef3c7; color:#b45309; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.78rem;">관광·휴식 명소</span>
                        </div>
                        <div style="font-size:0.85rem; color:#4b5563;">{s_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("축제장 인근에 등록된 인근 관광·휴식 명소 정보가 없습니다.")

        with st.expander("🛠️ agent.py 원본 출력 딕셔너리 JSON 확인"):
            st.json(result)
else:
    # [첫 진입 시 LLM 자동 실행 방지] 토큰 소모 없이 사용자의 버튼 클릭을 유도하는 친절한 대기 화면
    st.markdown("""
    <div style="padding: 35px 25px; background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 14px; text-align: center; margin-top: 15px;">
        <div style="font-size: 2.2rem; margin-bottom: 10px;">🌿 🗺️ 🚀</div>
        <h3 style="color: #1E293B; margin-bottom: 8px; font-weight: 700;">AI 맞춤 큐레이션 매거진 발행 준비 완료</h3>
        <p style="color: #64748B; font-size: 0.96rem; line-height: 1.6; max-width: 650px; margin: 0 auto 16px auto;">
            좌측 사이드바에서 <strong>1) 여행지(행정구역)</strong>와 <strong>2) 로컬 축제</strong>를 선택하고,<br>
            <strong>체력 배터리(Stamina), 동반자 유형, 세부 요청사항</strong>을 설정하신 후<br>
            아래 <strong>[🚀 AI 맞춤 매거진 & 큐레이션 발행]</strong> 버튼을 누르면 100% 공공데이터 기반의 맞춤 매거진과 안심 지도가 발행됩니다.
        </p>
    </div>
    """, unsafe_allow_html=True)
