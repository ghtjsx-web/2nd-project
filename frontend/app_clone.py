"""
app_clone.py - 초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)
=============================================================
팀원 A(agent_clone.py)와 팀원 B(data_clone.py)의 실시간 결합 완성형 웹 애플리케이션

[동적 여행지 탐색 및 데이터 정직성 기능]
1. 전국 17개 광역 행정구역 선택 (서울, 경기, 강원, 충청, 전라, 경상, 제주 등)
2. 1~12월 연중 일정 선택 (원하는 월별 축제 필터링, active_months 기반 프리셋 매칭)
3. 행정구역 x 여행 월 상호 연동형 동적 축제 셀렉터
4. 첫 진입 시 LLM 자동 실행 방지 (명시적 버튼 클릭 시에만 파이프라인 가동)
5. '직선거리' 정직한 거리 표기 및 쉼터 관광지 엄격 카테고리 필터링
6. 축제별 실사 히어로 배너, Folium 인터랙티브 지도, 대형주차장/착한식당 랭킹, 프로그램 체크리스트 완비
"""

import os
import sys
import json
import base64
import streamlit as st
import folium
from streamlit_folium import st_folium

# Windows 콘솔 및 출력 환경 안전화
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_image_base64(filepath: str) -> str:
    """로컬 이미지를 안전하게 base64 data URI로 변환하여 HTML 내 완벽 인라인 렌더링"""
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:image/jpeg;base64,{encoded}"
    return ""


def get_festival_images(fest: dict) -> dict:
    """축제명 및 테마에 맞춰 생성된 고화질 정밀 로컬 실사 이미지를 동적 매핑"""
    name = fest.get("name", "")
    desc = fest.get("description", "")
    target = f"{name} {desc}"

    if "진주" in target or "유등" in target or "남강" in target:
        hero = "assets/jinju_lantern.jpg"
        caption = "📍 진주 남강을 수놓은 오색 전통 유등과 촉석루 야경"
    elif "순천" in target or "갈대" in target or "습지" in target:
        hero = "assets/suncheon_reed.jpg"
        caption = "📍 황금빛 물결의 순천만 갈대숲과 평지 무장애 힐링 탐방로"
    elif "인삼" in target or "금산" in target or "약초" in target:
        hero = "assets/geumsan_ginseng.jpg"
        caption = "📍 생명의 고향 금산 인삼약초 축제 현장과 활기찬 수삼 시장"
    elif any(k in target for k in ["등", "불꽃", "야경", "빛", "달빛", "별"]):
        hero = "assets/jinju_lantern.jpg"
        caption = f"📍 {name}의 낭만적인 야경과 등불 전시"
    elif any(k in target for k in ["갈대", "억새", "자연", "생태", "바람", "습지", "호수", "강", "산", "단풍"]):
        hero = "assets/suncheon_reed.jpg"
        caption = f"📍 {name}의 수려한 가을 자연 경관과 힐링 산책로"
    else:
        hero = "assets/geumsan_ginseng.jpg"
        caption = f"📍 {name}의 활기찬 축제 현장과 로컬 문화 체험"

    return {
        "hero_path": hero,
        "hero_b64": get_image_base64(hero),
        "caption": caption,
        "food_path": "assets/model_food.jpg",
        "nature_path": "assets/nature_shelter.jpg"
    }


# agent_clone 및 data_clone 정식 연동 임포트
try:
    from agent_clone import run_processing_pipeline
    from data_clone import (
        get_festival_infra_bundle,
        get_festivals,
        get_nearby_parking,
        get_nearby_restaurants,
        get_wellness_spots,
        calculate_distance
    )
except ImportError as e:
    st.error(f"클론 모듈 임포트 실패: {e}")
    st.stop()


# ==============================================================================
# 1. 스트림릿 페이지 설정 및 디자인 시스템 (CSS)
# ==============================================================================
st.set_page_config(
    page_title="Fest & Rest - 로컬 축제 & 쉼터 큐레이션",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    .hero-container {
        position: relative;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 22px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        height: 270px;
        background: #111827;
    }
    .hero-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0.88;
        filter: brightness(0.85);
    }
    .hero-text-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 24px 30px;
        background: linear-gradient(180deg, transparent 0%, rgba(10, 25, 18, 0.92) 90%);
        color: white;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
        color: #FFFFFF;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
    .hero-sub {
        font-size: 1.05rem;
        color: #E2E8F0;
        font-weight: 400;
    }
    .card-box {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 18px 20px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .badge-tag {
        display: inline-block;
        padding: 3px 8px;
        font-size: 0.75rem;
        font-weight: 700;
        border-radius: 5px;
        margin-right: 5px;
    }
    .badge-req { background-color: #FDE8E8; color: #9B1C1C; }
    .badge-walk { background-color: #DEF7EC; color: #03543F; }
    .badge-park { background-color: #E1EFFE; color: #1E429F; }
    .badge-food { background-color: #FEF08A; color: #713F12; }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. 전국 17개 행정구역 및 일정 마스터 정의
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

MONTH_OPTIONS = ["전체 (연중)", "1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]

# [지침 2 준수] active_months 필드를 추가하여 11월까지 진행되는 축제 누락 방지
PRESET_FESTIVALS = {
    "진주 남강유등축제": {
        "name": "진주 남강유등축제",
        "region": "경상남도",
        "active_months": [10],
        "lat": 35.19043372, "lng": 128.08022220,
        "address": "경남 진주시 남강로 626 (진주성 일원)",
        "dates": "2026-10-05 ~ 2026-10-20",
        "description": "물과 불과 빛의 아름다운 하모니, 역사와 낭만이 흐르는 대한민국 대표 야경 축제",
        "hero_img": "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1200&q=80",
        "food_img": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?auto=format&fit=crop&w=600&q=80",
        "nature_img": "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=600&q=80",
        "default_extra": "부모님이 무릎이 안 좋으셔서 계단과 장시간 보행은 피하고, 주차가 가장 넓고 편한 곳을 안내해 주세요.",
        "programs": [
            {"name": "남강 소망등 띄우기 체험", "category": "체험/투어", "description": "남강 물길 위로 직접 소망등을 띄워 보내는 사전 접수형 체험 프로그램", "reservation_required": "Y", "booking_tip": "공식 누리집 사전 예약 필수"},
            {"name": "진주성 성곽 등불 자유 산책로", "category": "상설 관람", "description": "진주성 내 무장애 평지 산책로를 따라 즐기는 고즈넉한 전통 등불 전시존", "reservation_required": "False", "booking_tip": "예약 없이 상시 자유 입장"},
            {"name": "촉석루 수변 달빛 음악 버스킹", "category": "문화 공연", "description": "남강 바람을 맞으며 잔디광장 벤치에서 편안히 관람하는 야외 공연", "reservation_required": False, "booking_tip": "현장 자유 착석"}
        ]
    },
    "순천만 갈대축제": {
        "name": "순천만 갈대축제",
        "region": "전라남도",
        "active_months": [10, 11],  # [지침 2 준수] 11월까지 개최 기간 유연 반영
        "lat": 34.8845, "lng": 127.5090,
        "address": "전남 순천시 순천만길 513-25",
        "dates": "2026-10-25 ~ 2026-11-03",
        "description": "광활한 황금빛 갈대밭과 흑두루미가 반겨주는 대한민국 대표 가을 생태 힐링 축제",
        "hero_img": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?auto=format&fit=crop&w=1200&q=80",
        "food_img": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80",
        "nature_img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80",
        "default_extra": "오래 걷기 힘들어서 핵심 갈대밭 30분만 보고 시원한 그늘 쉼터에서 쉬고 싶습니다.",
        "programs": [
            {"name": "생태 해설사와 함께하는 갈대숲 도슨트 투어", "category": "체험/투어", "description": "전문 해설사의 설명과 함께하는 15인 정원제 생태 투어", "reservation_required": "Y", "booking_tip": "공식 누리집 사전 예약 필수"},
            {"name": "갈대 바람소리 야외 포토존 산책길", "category": "상설 관람", "description": "무장애 데크길을 따라 여유롭게 거니는 평지 자유 산책 코스", "reservation_required": "False", "booking_tip": "상시 자유 입장"}
        ]
    },
    "금산 세계인삼축제": {
        "name": "금산 세계인삼축제",
        "region": "충청남도",
        "active_months": [10],
        "lat": 36.1032, "lng": 127.4891,
        "address": "충남 금산군 금산읍 인삼광장로 30",
        "dates": "2026-10-02 ~ 2026-10-11",
        "description": "생명의 고향 금산에서 펼쳐지는 건강 힐링 & 활력 충전 전통 축제",
        "hero_img": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=1200&q=80",
        "food_img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80",
        "nature_img": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?auto=format&fit=crop&w=600&q=80",
        "default_extra": "아이들과 함께 편하게 쉬면서 체험 부스 둘러보고 싶고, 주차하기 편한 넓은 주차장을 선호합니다.",
        "programs": [
            {"name": "수삼 캐기 현장 체험 클래스", "category": "영농 체험", "description": "인삼밭에서 직접 수삼을 캐보는 사전 접수형 체험 프로그램", "reservation_required": "Y", "booking_tip": "공식 홈페이지 사전 신청 필수"},
            {"name": "인삼 아트 플라워 상설 전시관", "category": "문화 전시", "description": "인삼주와 인삼 꽃공예 작품을 감상하는 실내 자유 관람존", "reservation_required": False, "booking_tip": "현장 자유 관람"}
        ]
    }
}


# ==============================================================================
# 3. 사이드바 - [행정구역 x 일정 연동형 동적 축제 선택기]
# ==============================================================================
with st.sidebar:
    st.markdown("## 🗺️ 여행지 및 축제 검색")
    st.caption("전국 17개 시·도 및 1~12월 일정 기반 동적 매칭")

    # 1. 전국 행정구역 선택
    selected_region = st.selectbox("📍 1. 여행 목적지 (광역 행정구역)", options=ADMIN_REGIONS, index=16)  # 기본 경상남도

    # 2. 날짜 1~12월 선택
    selected_month_str = st.selectbox("📅 2. 여행 희망 일정 (1~12월)", options=MONTH_OPTIONS, index=10)  # 기본 10월
    selected_month_int = None
    if "월" in selected_month_str:
        selected_month_int = int(selected_month_str.replace("월", "").strip())

    st.markdown("---")

    # 3. 행정구역 x 날짜 기반 축제 목록 동적 추출 (data_clone 연동)
    try:
        dynamic_fests = get_festivals(region=selected_region, month=selected_month_int)
    except TypeError:
        import importlib
        import data_clone
        importlib.reload(data_clone)
        dynamic_fests = data_clone.get_festivals(region=selected_region, month=selected_month_int)
    except Exception:
        dynamic_fests = []

    # 프리셋 축제 중 조건에 부합하는 항목 우선 배치
    festival_map = {}
    preset_names = []

    # [지침 2 준수] active_months 기반 유연한 월 매칭 (하드코딩 제거)
    for p_name, p_data in PRESET_FESTIVALS.items():
        region_match = (selected_region == "전국 전체") or (selected_region in p_data["region"])
        active_months = p_data.get("active_months", [])
        month_match = (selected_month_int is None) or (selected_month_int in active_months)
        if region_match and month_match:
            display_label = f"⭐ [명품 추천] {p_name}"
            festival_map[display_label] = p_data
            preset_names.append(display_label)

    # 공공데이터 동적 축제 추가
    for f in dynamic_fests:
        f_name = f["name"]
        if f_name in PRESET_FESTIVALS:
            continue
        dates_label = f" ({f.get('dates', '')})" if f.get('dates') and "일정" not in f.get('dates') else ""
        display_label = f"🎪 {f_name}{dates_label}"
        festival_map[display_label] = f

    if not festival_map:
        st.warning(f"선택하신 '{selected_region}'의 '{selected_month_str}' 축제가 데이터셋에 없습니다. 기본 추천 축제를 안내합니다.")
        festival_map = {f"⭐ [명품 추천] {k}": v for k, v in PRESET_FESTIVALS.items()}

    # 4. 동적으로 구성된 축제 셀렉트박스
    chosen_fest_label = st.selectbox(
        f"🎯 3. 축제 선택 (총 {len(festival_map)}개 매칭)",
        options=list(festival_map.keys()),
        index=0
    )
    selected_fest = festival_map[chosen_fest_label]

    st.markdown("---")

    # 4. 여행자 성향 및 체력 설정
    st.markdown("## ⚡ 여행자 맞춤 설정")
    stamina = st.slider("체력 지수 (%)", min_value=10, max_value=100, value=35, step=5)
    if stamina <= 30:
        st.info(f"🌿 체력 {stamina}%: [Low 분기] 직선거리 500m 이내 / 80% 쉼터 휴식")
    elif stamina <= 70:
        st.info(f"🚶 체력 {stamina}%: [Moderate 분기] 직선거리 2~3km / 50:50 균형")
    else:
        st.success(f"🏃 체력 {stamina}%: [High 분기] 직선거리 5km+ / 풀코스")

    companion = st.selectbox(
        "👥 동반자 유형",
        options=["부모님 (연로하심)", "나홀로 힐링", "연인/커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"],
        index=0
    )

    default_extra = selected_fest.get("default_extra", "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 차는 주차하기 편하고 넓은 곳이 좋겠습니다.")
    extra_details = st.text_area(
        "💬 자유 요청사항 (보행 제약, 쉼터 선호 등)",
        value=default_extra,
        height=75
    )

    # 실시간 인프라 번들 사전 조회 (data_clone 캐시)
    fest_lat = selected_fest.get("lat", 35.1904)
    fest_lng = selected_fest.get("lng", 128.0802)
    infra_data = get_festival_infra_bundle(fest_lat, fest_lng, radius_m=3000)

    with st.expander("🗄️ 주변 실시간 인프라 집계", expanded=False):
        st.markdown(f"- 🅿️ **공영주차장**: `{len(infra_data['parking_lots'])}개`")
        st.markdown(f"- 🍲 **착한가격 모범식당**: `{len(infra_data['model_restaurants'])}개`")
        st.markdown(f"- 🌿 **웰니스 쉼터 (관광지)**: `{len(infra_data['tourist_spots'])}개`")

    # [지침 1 준수] 사용자 클릭 시에만 AI 파이프라인이 가동되도록 변경
    run_button = st.button("🚀 AI 맞춤 매거진 & 큐레이션 발행", type="primary", use_container_width=True)


# ==============================================================================
# 4. 세션 상태 관리 및 AI 파이프라인 호출 ([지침 1 준수] if run_button 만 허용)
# ==============================================================================
if "curation_result" not in st.session_state:
    st.session_state.curation_result = None
    st.session_state.last_fest_label = None

# [지침 1 준수] 첫 진입 시 LLM 자동 실행 원천 차단: 오직 사용자가 버튼을 클릭했을 때만 실행
if run_button:
    with st.spinner(f"🤖 '{selected_fest['name']}' 맞춤 매거진과 안심 지도를 정밀 발행 중..."):
        user_inputs = {
            "stamina": stamina,
            "companion": companion,
            "region": selected_fest.get("region", selected_region),
            "selected_festival": selected_fest,
            "extra_details": extra_details
        }
        output = run_processing_pipeline(user_inputs, infra_data)
        st.session_state.curation_result = output
        st.session_state.last_fest_label = chosen_fest_label


# ==============================================================================
# 5. 상단 히어로 배너 (실사 비주얼 + 지역/일정 태그)
# ==============================================================================
img_bundle = get_festival_images(selected_fest)
hero_src = img_bundle["hero_b64"] if img_bundle["hero_b64"] else "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1200&q=80"
date_info = selected_fest.get("dates", "연중 상시 진행")

st.markdown(f"""
<div class="hero-container">
    <img src="{hero_src}" class="hero-img" alt="{selected_fest['name']}">
    <div class="hero-text-overlay">
        <div>
            <span class="badge-tag" style="background:#056608; color:#FFFFFF;">📍 {selected_fest.get('region', selected_region)}</span>
            <span class="badge-tag" style="background:rgba(255,255,255,0.28); color:#FFFFFF;">📅 {date_info}</span>
        </div>
        <h1 class="hero-title">{selected_fest['name']}</h1>
        <p class="hero-sub">{img_bundle['caption']} | 📍 {selected_fest.get('address', '')}</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 6. 인프라 핵심 메트릭 카드 (4단 KPI)
# ==============================================================================
top_park_spaces = infra_data['parking_lots'][0]['total_spaces'] if infra_data['parking_lots'] else 0
top_park_name = infra_data['parking_lots'][0]['name'] if infra_data['parking_lots'] else "주차장"
top_food_name = infra_data['model_restaurants'][0]['name'] if infra_data['model_restaurants'] else "모범식당"
top_food_price = infra_data['model_restaurants'][0].get('price', '착한가격') if infra_data['model_restaurants'] else "안심가격"

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric(label="🅿️ 추천 최대 주차장", value=f"{top_park_spaces}면", delta=top_park_name[:12])
with col_m2:
    st.metric(label="🍲 인근 착한가격업소", value=f"{len(infra_data['model_restaurants'])}개소", delta=top_food_price)
with col_m3:
    st.metric(label="🌿 안심 웰니스 쉼터", value=f"{len(infra_data['tourist_spots'])}개소", delta="관광지 공인 시설")
with col_m4:
    st.metric(label="⚡ 여행자 큐레이션 모드", value=f"체력 {stamina}%", delta="쉼표 80% 휴식" if stamina <= 30 else "균형 50%")


# ==============================================================================
# 7. 메인 2단 뷰포트 - 매거진 기사 & Folium 인터랙티브 지도
# ==============================================================================
result = st.session_state.get("curation_result")

if result:
    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": []})
    map_markers = result.get("map_markers", [])

    col_left, col_right = st.columns([6, 5], gap="large")

    # [좌측] 큐레이션 매거진 기사
    with col_left:
        st.markdown("### 📖 🌿 Fest & Rest 에디터 맞춤 기사")
        st.markdown(f"""
        <div class="card-box" style="border-top: 4px solid #056608; line-height: 1.85;">
        """, unsafe_allow_html=True)
        st.markdown(article_content)
        st.markdown("</div>", unsafe_allow_html=True)

        # 미식 & 쉼터 비주얼 사진 카드 (로컬 정밀 실사 이미지 렌더링)
        st.markdown("#### 🍲 현장 추천 안심 먹거리 & 쉼표 스팟")
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            st.image(img_bundle["food_path"], caption="🍲 지자체 공인 착한가격업소의 정갈한 남도 한상차림", use_container_width=True)
        with col_sub2:
            st.image(img_bundle["nature_path"], caption="🌿 보행약자도 편안히 쉬어가는 수변 그늘 벤치 힐링 쉼터", use_container_width=True)

    # [우측] Folium 지도 및 프로그램 가이드
    with col_right:
        st.markdown("### 🗺️ 맞춤 안심 동선 지도 (Folium)")

        m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="OpenStreetMap")

        for pin in map_markers:
            p_lat = pin.get("lat")
            p_lng = pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name = pin.get("name", "거점")
                p_title = pin.get("popup_title", f"📍 {p_name}")
                p_desc = pin.get("desc", "")
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")

                # [지침 3 준수] 팝업에도 축제장 직선거리 명시
                p_dist_val = int(calculate_distance(fest_lat, fest_lng, p_lat, p_lng))
                p_dist_html = f"<p style='font-size: 11px; margin: 2px 0; color: #0284C7;'>축제장 직선거리: 약 {p_dist_val:,}m</p>" if (p_dist_val > 0 and pin.get("category") != "festival") else ""

                popup_html = f"""
                <div style="font-family: Pretendard, sans-serif; min-width: 170px;">
                    <strong style="font-size: 13px; color: #1A3026;">{p_title}</strong>
                    <hr style="margin: 5px 0; border: none; border-top: 1px solid #E2EBE6;">
                    {p_dist_html}
                    <p style="font-size: 11px; margin: 0; color: #4A5568;">{p_desc}</p>
                </div>
                """
                folium.Marker(
                    location=[p_lat, p_lng],
                    tooltip=p_name,
                    popup=folium.Popup(popup_html, max_width=280),
                    icon=folium.Icon(color=p_color, icon=p_icon, prefix="fa" if p_icon in ["cutlery", "car", "leaf", "flag"] else "glyphicon")
                ).add_to(m)

        st_folium(m, height=430, use_container_width=True)

        st.markdown("---")

        # 프로그램 체크리스트 탭
        st.markdown("### 📋 프로그램 체크리스트")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])

        tab1, tab2 = st.tabs([f"🔴 사전 예약 필수 ({len(req_list)})", f"🟢 현장 자유 참여 ({len(walk_list)})"])

        with tab1:
            if req_list:
                for item in req_list:
                    st.markdown(f"""
                    <div style="padding: 10px; background: #FFF5F5; border-left: 4px solid #E53E3E; border-radius: 6px; margin-bottom: 8px;">
                        <span class="badge-tag badge-req">사전예약 필수</span>
                        <strong>{item['name']}</strong> <span style="font-size:0.8rem; color:#718096;">({item.get('category', '체험')})</span>
                        <div style="font-size: 0.85rem; color: #4A5568; margin-top: 4px;">{item.get('description', '')}</div>
                        <div style="font-size: 0.78rem; color: #E53E3E; margin-top: 2px;">💡 예약 팁: {item.get('booking_tip', '사전 예약 필수')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("선택된 축제에 등록된 사전 예약 필수 프로그램이 없습니다.")

        with tab2:
            if walk_list:
                for item in walk_list:
                    st.markdown(f"""
                    <div style="padding: 10px; background: #F0FFF4; border-left: 4px solid #38A169; border-radius: 6px; margin-bottom: 8px;">
                        <span class="badge-tag badge-walk">상설 자유 참여</span>
                        <strong>{item['name']}</strong> <span style="font-size:0.8rem; color:#718096;">({item.get('category', '상설')})</span>
                        <div style="font-size: 0.85rem; color: #4A5568; margin-top: 4px;">{item.get('description', '')}</div>
                        <div style="font-size: 0.78rem; color: #2F855A; margin-top: 2px;">💡 입장 팁: {item.get('booking_tip', '상시 자유 입장')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("선택된 축제에 등록된 상설/자유 참여 프로그램이 없습니다.")

        # [지침 3 준수] 대형 주차장 & 착한식당 추천 리스트에 '직선거리' 명시
        st.markdown("---")
        st.markdown("### 🅿️ 대형 주차장 & 🍲 착한식당 추천 랭킹")
        col_pk, col_fd = st.columns(2)

        with col_pk:
            st.caption("규모가 큰 안심 공영주차장 (직선거리 순)")
            for p in infra_data['parking_lots'][:3]:
                p_dist = int(calculate_distance(fest_lat, fest_lng, p['lat'], p['lng']))
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; margin-bottom: 6px;">
                    <span class="badge-tag badge-park">{p['total_spaces']}면</span>
                    <strong style="font-size: 0.88rem;">{p['name']}</strong>
                    <div style="font-size: 0.78rem; color: #64748B;">축제장 직선거리 약 {p_dist:,}m | 요금: {p['fee']}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_fd:
            st.caption("인증 착한가격 모범식당 (직선거리 순)")
            for r in infra_data['model_restaurants'][:3]:
                r_dist = int(calculate_distance(fest_lat, fest_lng, r['lat'], r['lng']))
                st.markdown(f"""
                <div style="padding: 8px 12px; background: #FFFDF5; border: 1px solid #FEF08A; border-radius: 6px; margin-bottom: 6px;">
                    <span class="badge-tag badge-food">{r.get('price', '착한가격')}</span>
                    <strong style="font-size: 0.88rem;">{r['name']}</strong>
                    <div style="font-size: 0.78rem; color: #854D0E;">축제장 직선거리 약 {r_dist:,}m | 메뉴: {r.get('menu', '대표식')}</div>
                </div>
                """, unsafe_allow_html=True)

else:
    # [지침 1 준수] 최초 진입 시 토큰 소모 없이 사용자의 버튼 클릭을 유도하는 친절한 안내 뷰
    st.markdown("""
    <div style="padding: 35px 25px; background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 14px; text-align: center; margin-top: 15px;">
        <div style="font-size: 2.2rem; margin-bottom: 10px;">🌿 🗺️ 🚀</div>
        <h3 style="color: #1E293B; margin-bottom: 8px; font-weight: 700;">AI 맞춤 큐레이션 매거진 발행 준비 완료</h3>
        <p style="color: #64748B; font-size: 0.96rem; line-height: 1.6; max-width: 650px; margin: 0 auto 16px auto;">
            좌측 사이드바에서 <strong>1) 여행지</strong>와 <strong>2) 일정(1~12월)</strong>을 선택한 후,<br>
            여행자의 <strong>체력(%)과 동반자 유형, 자유 요청사항</strong>을 설정해 주세요.<br>
            준비가 되셨다면 아래 <strong>[🚀 AI 맞춤 매거진 & 큐레이션 발행]</strong> 버튼을 눌러 여정을 시작하세요!
        </p>
    </div>
    """, unsafe_allow_html=True)
