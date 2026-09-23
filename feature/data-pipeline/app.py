# ==============================================================================
# 페스타픽 (FestaPick) - 체력 맞춤형 축제 여행 큐레이션 웹 애플리케이션
#
# [핵심 기능]
# 1. 화면 1 (메인 탐색): 전국 축제 목록 리스트 & 캘린더 뷰, 권역/월별 필터, 체력 배터리 선택
# 2. 화면 2 (상세 코스): 선택 축제의 동일 시/군/구(sigungu) 중심 체력 최적화 4단계 동선 패키징
#    [주차장 ➡️ 축제/사진스팟 ➡️ 착한가격 맛집 & 감성 카페 ➡️ 웰니스 힐링]
# 3. 최적화: @st.cache_resource / @st.cache_data 기반 무중단 0초 반응 및 세션 상태(st.session_state) 관리
# ==============================================================================

import os
import sys
import re
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import pandas as pd
import importlib

# data.py 및 prompt.py 모듈 연동 (핫 리로드 강제)
import prompt
import data
try:
    importlib.reload(prompt)
    importlib.reload(data)
except Exception:
    pass

from data import PublicDataRAGManager
from prompt import (
    build_user_prompt,
    get_system_prompt,
    get_storytelling_system_prompt,
    build_storytelling_user_prompt,
    generate_storytelling_fallback
)

def sanitize_address(address_text: Any) -> str:
    """주소 텍스트에서 '전남광주통합특별시' 등 가상 행정구역을 전면 제거하고 표준 실제 주소로 복원합니다."""
    if hasattr(data, "sanitize_address"):
        return data.sanitize_address(address_text)
    if not address_text:
        return ""
    text = str(address_text).strip()
    text = re.sub(r"전남광주통합특별시\s*(동구|서구|남구|북구|광산구)\b", r"광주광역시 \1", text)
    text = re.sub(r"전남광주통합특별시\s*광주\b", "광주광역시", text)
    text = re.sub(r"전남광주통합특별시", "전라남도", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_sigungu(address_text: str) -> str:
    """진짜 시/군/구 1개 단어만 추출합니다."""
    if hasattr(data, "extract_sigungu"):
        return data.extract_sigungu(address_text)
    text = sanitize_address(address_text)
    if "세종특별자치시" in text or re.search(r"\b세종시\b", text):
        return "세종시"
    m_metro = re.search(r"(?:서울|부산|대구|인천|광주|대전|울산)(?:특별시|광역시)?\s+([가-힣]+(?:구|군))\b", text)
    if m_metro:
        return m_metro.group(1)
    m_do = re.search(r"(?:경기|강원|충북|충남|전북|전남|경북|경남|제주)(?:도|특별자치도)?\s+([가-힣]+(?:시|군))\b", text)
    if m_do:
        return m_do.group(1)
    matches = re.findall(r"\b([가-힣]{2,}(?:시|군|구))\b", text)
    for m in matches:
        if not m.endswith(("특별자치도", "특별시", "광역시", "통합특별시", "도")):
            return m
    return ""

# 윈도우 환경 한글 표준 출력 인코딩 설정
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# .env 환경 변수 로드
load_dotenv()

# ==============================================================================
# [설정 및 플래그]
# ==============================================================================
# 개발 모드 플래그 (True: 개발 중 0초 빠른 샘플링 / False: 프로덕션 전수 로드)
IS_DEV_MODE: bool = True

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="🌿 지역축제 맞춤형 힐링 여행 큐레이터",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2030 감성 맞춤형 커스텀 CSS 스타일링
st.markdown("""
<style>
    /* 메인 폰트 및 부드러운 배경 감성 */
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 헤더 그라디언트 배너 */
    .hero-container {
        background: linear-gradient(135deg, #1E1E2F 0%, #2A2A48 50%, #1A1A35 100%);
        border-radius: 18px;
        padding: 30px;
        margin-bottom: 25px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FF6B6B, #FF8E53, #FFA07A);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .hero-subtitle {
        color: #E2E8F0;
        font-size: 1.05rem;
        font-weight: 400;
        line-height: 1.6;
    }

    /* 배터리 체력 상태 배지 */
    .stamina-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        margin-right: 8px;
    }
    .stamina-low {
        background-color: rgba(72, 187, 120, 0.2);
        color: #48BB78;
        border: 1px solid #48BB78;
    }
    .stamina-mid {
        background-color: rgba(237, 137, 54, 0.2);
        color: #ED8936;
        border: 1px solid #ED8936;
    }
    .stamina-high {
        background-color: rgba(245, 101, 101, 0.2);
        color: #F56565;
        border: 1px solid #F56565;
    }
    
    /* 태그 칩 */
    .tag-chip {
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        color: #CBD5E1;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    
    /* 동선 타임라인 스텝 카드 */
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 14px;
        padding: 18px;
        border-left: 5px solid #FF8E53;
        margin-bottom: 16px;
        transition: transform 0.2s ease;
    }
    .step-card:hover {
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# [캐싱 레이어] ChromaDB 매니저 및 데이터 로드 캐싱
# ==============================================================================

@st.cache_resource(show_spinner="통합 공공데이터베이스(ChromaDB)를 연동 중입니다...")
def get_rag_manager(cache_version: str = "v2_companion") -> PublicDataRAGManager:
    """ChromaDB Persistent Client 및 컬렉션을 캐시하여 세션 동안 단 한 번만 생성합니다."""
    manager = data.PublicDataRAGManager(
        data_dir="data",
        data_path="data/festivals.csv",
        db_path="chromadb_store",
        collection_name="integrated_festivals"
    )
    return manager


@st.cache_data(show_spinner="전국 축제 목록을 안전하게 로드 중입니다...")
def get_all_festivals(cache_version: str = "v18_sido_strict") -> List[Dict[str, Any]]:
    """전국 축제 목록(1,320건)을 메모리 캐시에 적재하여 0초 만에 목록 화면에 공급합니다."""
    mgr = get_rag_manager(cache_version="v2_companion")
    # 인메모리 문서가 비어있거나, event_type이 없는 구버전 문서가 캐시되어 있으면 강제 재로드
    has_event_types = any(d.metadata.get("event_type") == "문화행사" for d in getattr(mgr, "documents", []))
    if not mgr.documents or not has_event_types:
        mgr.load_all_datasets()
    # 축제 데이터만 필터링하여 메타데이터 리스트 반환
    festival_metas: List[Dict[str, Any]] = [
        d.metadata for d in mgr.documents
        if d.metadata.get("data_type") == "축제"
    ]
    # 이중 안전장치: 메타데이터에 event_type이 혹시라도 누락된 경우 즉시 동적 보강
    cultural_keywords = ["문화제", "예술제", "연극", "음악회", "전시", "공연", "역사", "비엔날레", "국악", "문학", "학술", "영화", "도서", "북", "페어", "판소리", "가요제", "콘서트", "포크", "클래식", "뮤지컬", "페스티벌"]
    for f in festival_metas:
        if not f.get("event_type"):
            comb = f"{f.get('title', '')} {f.get('description', '')} {f.get('programs', '')}"
            f["event_type"] = "문화행사" if any(k in comb for k in cultural_keywords) else "지역축제"
    return festival_metas


@st.cache_data(show_spinner="체력 맞춤형 4단계 동선(주차 ➔ 축제 ➔ 식사/카페 ➔ 웰니스)을 패키징 중입니다...")
def cached_custom_course(festival_name: str, stamina: str, companion: str = "연인", cache_version: str = "v24_companion_fixed") -> Dict[str, Any]:
    """선택한 축제와 체력 수준, 동행자 유형에 따른 맞춤 코스를 캐싱하여 중복 계산을 방지합니다."""
    mgr = get_rag_manager(cache_version="v2_companion")
    try:
        return mgr.generate_custom_course(festival_name=festival_name, user_stamina=stamina, companion=companion)
    except TypeError:
        # 구버전 캐시 인스턴스로 인한 TypeError 방지: 최신 모듈 리로드 및 인스턴스 즉시 갱신
        st.cache_resource.clear()
        importlib.reload(data)
        new_mgr = data.PublicDataRAGManager(
            data_dir="data",
            data_path="data/festivals.csv",
            db_path="chromadb_store",
            collection_name="integrated_festivals"
        )
        return new_mgr.generate_custom_course(festival_name=festival_name, user_stamina=stamina, companion=companion)
    except Exception:
        # 기타 예외 발생 시 안전 재시도
        return mgr.generate_custom_course(festival_name=festival_name, user_stamina=stamina, companion=companion)


@st.cache_resource
def get_openai_client(api_key: str) -> OpenAI:
    """OpenRouter API 호출용 클라이언트를 안전하게 캐시합니다."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )


# ==============================================================================
# [세션 상태 (Session State) 초기화]
# ==============================================================================
# page: "list" (메인 축제 탐색) 또는 "detail" (체력 맞춤 코스 상세)
if "page" not in st.session_state:
    st.session_state.page = "list"

# 현재 선택된 축제 객체
if "selected_festival" not in st.session_state:
    st.session_state.selected_festival = None

# 사용자 체력 상태 ("하", "중", "상")
if "user_stamina" not in st.session_state:
    st.session_state.user_stamina = "중"

# 뷰 모드 ("card": 카드형 리스트 / "calendar": 월별 캘린더)
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "card"

# AI 도슨트 오디오 가이드 생성 텍스트 보관
if "ai_docent_text" not in st.session_state:
    st.session_state.ai_docent_text = ""

# 동행자 유형 ("연인", "친구", "가족", "혼자")
if "companion" not in st.session_state:
    st.session_state.companion = "연인"


# ==============================================================================
# [사이드바 영역: 오늘 내 체력 배터리 & 앱 제어]
# ==============================================================================
st.sidebar.markdown("### 🌿 지역축제 맞춤형 힐링 여행 큐레이터")
st.sidebar.caption("공공데이터 4종 기반 체력 맞춤형 축제 동선")

if IS_DEV_MODE:
    st.sidebar.info("🛠️ **DEV MODE 활성화** (초고속 샘플링 핫리로드)")

st.sidebar.markdown("---")
st.sidebar.markdown("#### 🔋 오늘 내 체력 배터리")
stamina_options = [
    "🔋 하 (방전 직전 / 휴식·힐링 집중)",
    "⚡ 중 (보통 / 대표 알짜 명소 탐방)",
    "🔥 상 (에너지 100% / 풀코스 인생샷)"
]
stamina_map = {
    "🔋 하 (방전 직전 / 휴식·힐링 집중)": "하",
    "⚡ 중 (보통 / 대표 알짜 명소 탐방)": "중",
    "🔥 상 (에너지 100% / 풀코스 인생샷)": "상"
}
# 역매핑
stamina_rev_map = {"하": stamina_options[0], "중": stamina_options[1], "상": stamina_options[2]}

selected_stamina_raw = st.sidebar.radio(
    "현재 체력 상태를 선택하세요:",
    options=stamina_options,
    index=["하", "중", "상"].index(st.session_state.user_stamina),
    help="선택한 체력 수준에 맞춰 주차장 도보 거리, 사진스팟 개수, 식당/카페 유형, 웰니스 테마가 동적으로 맞춤 구성됩니다."
)
st.session_state.user_stamina = stamina_map[selected_stamina_raw]

# 동행자 선택 (변경 시 실시간 리런으로 맞춤형 스토리텔링 즉시 반영)
companion_options = ["연인", "친구", "가족", "혼자"]
companion_idx = companion_options.index(st.session_state.companion) if st.session_state.companion in companion_options else 0
companion_choice: str = st.sidebar.selectbox(
    "👥 동행 선택",
    options=companion_options,
    index=companion_idx,
    help="선택한 동행자에 맞춰 스토리텔링 톤앤매너와 추천 테마가 완전히 차별화됩니다."
)
if companion_choice != st.session_state.companion:
    st.session_state.companion = companion_choice
    st.rerun()

st.sidebar.markdown("---")
# 캐시 리셋 버튼
if st.sidebar.button("🔄 캐시 및 DB 연결 새로고침", help="메모리와 ChromaDB 연결을 완전히 초기화합니다."):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.session_state.clear()
    st.session_state.page = "list"
    st.rerun()


# ==============================================================================
# [화면 2: 체력 맞춤 상세 코스 페이지]
# ==============================================================================
def render_detail_page():
    """선택한 축제를 중심으로 [주차장 ➡️ 축제/사진스팟 ➡️ 착한가격 맛집/카페 ➡️ 웰니스 힐링] 코스를 보여주는 상세 뷰입니다."""
    fest = st.session_state.selected_festival
    if not fest:
        st.session_state.page = "list"
        st.rerun()
        return

    fest_title = fest.get("title", "선택된 축제")
    raw_location = fest.get("location", "개최지 주소 확인 필요")
    fest_location = sanitize_address(raw_location)
    fest_venue = fest.get("venue", fest_location)
    # 진짜 시/군/구 1개 단어 추출 (가상 행정구역 완전 배제)
    fest_sigungu = extract_sigungu(f"{fest_location} {fest_venue}") or extract_sigungu(raw_location) or fest.get("sigungu", "")
    if "전남광주" in fest_sigungu or "통합" in fest_sigungu:
        fest_sigungu = extract_sigungu(fest_location)
    fest_region = data.classify_region(fest_location) if hasattr(data, "classify_region") else fest.get("region", "")
    start_date = fest.get("start_date", "")
    end_date = fest.get("end_date", "")
    period_str = f"{start_date} ~ {end_date}".strip(" ~") if (start_date or end_date) else "상시 / 개최 기간 확인 필요"
    overview = fest.get("overview", "생생한 현장 프로그램과 다양한 즐길 거리가 가득한 축제입니다.")

    # 상단 네비게이션 및 복귀 버튼
    col_back, col_title = st.columns([1, 4])
    with col_back:
        if st.button("← 🔙 목록으로 돌아가기", use_container_width=True):
            st.session_state.page = "list"
            st.session_state.ai_docent_text = ""
            st.rerun()

    # 상단 축제 요약 카드
    st.markdown(f"""
    <div class="hero-container">
        <span class="tag-chip">📍 {fest_region} · {fest_sigungu}</span>
        <span class="tag-chip">📅 {period_str}</span>
        <div class="hero-title">{fest_title}</div>
        <div class="hero-subtitle">
            <b>개최 장소:</b> {fest_venue} ({fest_location})<br>
            <b>축제 개요:</b> {overview}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 체력 레벨 즉시 전환 컨트롤러 (상세 화면에서도 바로 체력 변경 가능)
    col_ctrl1, col_ctrl2 = st.columns([2, 3])
    with col_ctrl1:
        st.markdown("#### ⚡ 현재 코스 체력 배터리")
        stamina_icons = {"하": "🔋 하 (방전 직전 / 휴식·힐링 집중)", "중": "⚡ 중 (보통 / 대표 알짜 명소)", "상": "🔥 상 (에너지 100% / 풀코스 인생샷)"}
        current_stamina = st.radio(
            "체력 모드 실시간 변경:",
            options=["하", "중", "상"],
            index=["하", "중", "상"].index(st.session_state.user_stamina),
            format_func=lambda x: stamina_icons[x],
            horizontal=True
        )
        if current_stamina != st.session_state.user_stamina:
            st.session_state.user_stamina = current_stamina
            st.session_state.ai_docent_text = ""
            st.rerun()

    with col_ctrl2:
        st.markdown("#### 🧭 코스 패키징 요약")
        st.info(f"선택하신 **[{st.session_state.user_stamina}]** 체력 및 **[{st.session_state.companion}]** 동행 맞춤으로 **'{fest_sigungu}'** 행정구역 내 이동 동선과 장소를 엄선하여 자동 조합했습니다.")

    st.markdown("---")

    # 4단계 맞춤 코스 패키징 데이터 로드
    course_data = cached_custom_course(
        fest_title,
        st.session_state.user_stamina,
        companion=st.session_state.companion,
        cache_version="v24_companion_fixed"
    )

    # 1. 위치 정합성 알림 (fallback_applied 여부에 따라 info/warning 구분)
    notice_text = course_data.get("location_integrity_notice", "")
    is_fallback_applied = course_data.get("fallback_applied", False)
    if notice_text:
        if is_fallback_applied:
            st.info(notice_text)
        else:
            st.success(notice_text)

    st.subheader(f"🗺️ {course_data.get('course_summary', '맞춤 4단계 원데이 코스 타임라인')}")

    timeline_steps = course_data.get("timeline", [])

    # 4단계 스텝 순차적 렌더링
    for step in timeline_steps:
        s_num = step.get("step", 1)
        s_title = step.get("step_title", "")
        s_icon = step.get("icon", "📍")
        s_cat = step.get("category", "")
        s_tip = step.get("stamina_tip", "")

        with st.container(border=True):
            col_icon, col_content = st.columns([1, 8])
            with col_icon:
                st.markdown(f"<div style='font-size: 2.8rem; text-align: center;'>{s_icon}</div>", unsafe_allow_html=True)
                st.caption(f"<div style='text-align:center;'><b>Step {s_num}</b><br>{s_cat}</div>", unsafe_allow_html=True)

            with col_content:
                st.markdown(f"### {s_num}단계: {s_title} — **{step.get('title', '')}**")
                
                # 스텝별 특화 정보 렌더링
                if s_cat == "주차장":
                    p_fallback = step.get("parking_fallback_notice")
                    if p_fallback:
                        st.warning(p_fallback)
                    st.write(f"📍 **위치:** {step.get('location')} ({step.get('sigungu')})")
                    st.write(f"💰 **요금 안내:** {step.get('fee_info', '현장 안내')}")
                    if step.get("phone"):
                        st.write(f"📞 **문의:** {step.get('phone')}")

                elif s_cat == "축제/사진스팟":
                    fest_fee = step.get("fee") or fest.get("fee") or "무료 관람 (상세 현장 확인)"
                    fest_prog = step.get("programs") or fest.get("programs") or step.get("description") or "개막식, 문화예술 공연 및 참여 체험 부스"
                    fest_desc = step.get("description") or fest.get("description") or step.get("detailed_desc") or fest_prog
                    fest_hp = step.get("homepage", fest.get("homepage", ""))
                    fest_phone = step.get("phone", fest.get("phone", ""))
                    fest_type = step.get("event_type", fest.get("event_type", "지역축제"))
                    type_badge_label = "🎭 문화행사" if fest_type == "문화행사" else "🎉 지역축제"
                    venue_full = f"{fest_venue} ({step.get('location')})" if fest_venue and fest_venue != step.get('location') else step.get('location')

                    # [CSV 1:1 바인딩] 원본 축제내용 및 프로그램 100% 전문 출력
                    with st.container(border=True):
                        st.markdown(f"""
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; font-size: 0.92rem;">
                            <span class='tag-chip' style='background:rgba(59,130,246,0.18); color:#2563EB; font-weight:700;'>🏷️ {type_badge_label}</span>
                            <span class='tag-chip' style='background:rgba(239,68,68,0.18); color:#DC2626; font-weight:700;'>🎟️ 요금: {fest_fee}</span>
                            <span class='tag-chip' style='background:rgba(16,185,129,0.18); color:#059669; font-weight:700;'>📅 기간: {step.get('period', '상시 운영')}</span>
                            <span class='tag-chip' style='background:rgba(107,114,128,0.18); color:#374151; font-weight:700;'>📍 {venue_full}</span>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown("#### 📖 축제 소개 (원본 축제내용)")
                        st.write(fest_desc)

                        st.markdown("---")
                        st.markdown("#### 🎪 주요 프로그램 (프로그램 내용)")
                        st.write(fest_prog)

                    # 예매처/공식홈페이지 링크
                    valid_hp = None
                    if fest_hp and str(fest_hp).strip().lower() not in ["nan", "none", "null", "-", ""]:
                        hp_clean = str(fest_hp).strip()
                        if hp_clean.startswith("http://") or hp_clean.startswith("https://"):
                            valid_hp = hp_clean
                        elif hp_clean.startswith("www.") or ("." in hp_clean and "/" not in hp_clean):
                            valid_hp = "https://" + hp_clean

                    c_link, c_blank = st.columns([1.5, 2])
                    with c_link:
                        if valid_hp:
                            st.link_button("🎟️ 축제 사전 예매 & 공식 안내 바로가기", url=valid_hp, use_container_width=True)
                        elif fest_phone:
                            st.info(f"📞 사전 예매/현장 문의: **{fest_phone}**")
                        else:
                            st.caption("ℹ️ 현장 종합안내소에서 상세 일정 및 티켓 문의 가능")

                    spots = step.get("photo_spots", [])
                    if spots:
                        st.markdown("**📸 추천 인생샷 포토스팟:** " + " ".join([f"`{s}`" for s in spots]))

                elif s_cat == "음식점/카페":
                    s_notice = step.get("store_fallback_notice") or step.get("store_fallback", False)
                    stores_list = step.get("restaurants", [])
                    if not stores_list and step.get("restaurant"):
                        r = step.get("restaurant")
                        if not r.get("is_empty"):
                            stores_list = [r]

                    # ★ 2차 엄격 sigungu 검증: fest_sigungu와 다른 지역 데이터 완전 제거
                    if fest_sigungu:
                        verified_stores = [
                            s for s in stores_list
                            if s.get("sigungu") == fest_sigungu
                            and not str(s.get("title", "")).startswith("※")
                        ]
                    else:
                        verified_stores = [s for s in stores_list if not str(s.get("title", "")).startswith("※")]

                    if s_notice or not verified_stores:
                        st.warning(f"⚠️ 현재 [{fest_sigungu}] 관내에 등록된 착한가격업소 데이터가 없습니다.")
                    else:
                        st.success(f"✅ [{fest_sigungu}] 관내 착한가격업소 매칭 ({len(verified_stores)}건)")
                        st.markdown("#### 🍽️ 착한가격 가성비 맛집 (관내 업소 목록)")

                        st_cols = st.columns(max(1, len(verified_stores[:3])))
                        for s_idx, store_item in enumerate(verified_stores[:3]):
                            with st_cols[s_idx]:
                                with st.container(border=True):
                                    st.markdown(f"##### **{store_item.get('title', '가성비 맛집')}**")
                                    st.markdown(f"<span class='tag-chip' style='background:rgba(255,107,107,0.18); color:#FF8E53;'>🏷️ 업종: {store_item.get('category', '음식점')}</span>", unsafe_allow_html=True)
                                    st.caption(f"📍 위치: {store_item.get('location', '주소 확인')}")
                                    if store_item.get("phone"):
                                        st.caption(f"📞 {store_item.get('phone')}")

                                    st.markdown("---")
                                    st.markdown("📋 **대표메뉴 및 가격:**")
                                    m1 = store_item.get("menu1")
                                    p1 = store_item.get("price1")
                                    m2 = store_item.get("menu2")
                                    p2 = store_item.get("price2")
                                    m3 = store_item.get("menu3")
                                    p3 = store_item.get("price3")

                                    if m1:
                                        st.write(f"• **{m1}**: `{p1}원`" if p1 else f"• **{m1}**")
                                    if m2:
                                        st.write(f"• **{m2}**: `{p2}원`" if p2 else f"• **{m2}**")
                                    if m3:
                                        st.write(f"• **{m3}**: `{p3}원`" if p3 else f"• **{m3}**")
                                    if not (m1 or m2 or m3):
                                        menu_raw = store_item.get("menu", "")
                                        if menu_raw:
                                            st.write(f"• {menu_raw}")

                    # 힐링 감성 카페 & 디저트 (실제 데이터가 있을 때만 렌더링)
                    cafe = step.get("cafe", {})
                    cafe_title = cafe.get("title", "")
                    # 더미/fallback 텍스트가 아닌 실제 카페 데이터가 있을 때만 표시
                    if cafe_title and "없음" not in cafe_title and "준비 중" not in cafe_title:
                        st.markdown("#### ☕ 힐링 감성 카페 & 디저트 연계")
                        with st.container(border=True):
                            st.markdown(f"##### ☕ **{cafe_title}** `[{cafe.get('category', '카페/베이커리')}]`")
                            if cafe.get("location"):
                                st.write(f"📍 **위치:** {cafe.get('location')}")
                            if cafe.get("menu"):
                                st.write(f"🍰 **대표 메뉴:** {cafe.get('menu')}")
                            if cafe.get("reason"):
                                st.write(f"💡 **추천 사유:** {cafe.get('reason')}")
                            if cafe.get("phone"):
                                st.caption(f"📞 문의: {cafe.get('phone')}")

                elif s_cat == "웰니스 힐링":
                    w_notice = step.get("wellness_fallback_notice")
                    w_sigungu = step.get("sigungu", "")
                    w_places = step.get("wellness_places", [])
                    verified_w = [
                        wp for wp in w_places
                        if not wp.get("is_empty")
                        and "없음" not in str(wp.get("title", ""))
                        and not str(wp.get("title", "")).startswith("※")
                        and (not fest_sigungu or wp.get("sigungu") == fest_sigungu)
                    ]

                    if not verified_w or bool(w_notice):
                        st.warning(f"⚠️ 현재 [{fest_sigungu}] 관내에 등록된 웰니스 공식 인증 관광지 데이터가 없습니다.")
                        with st.container(border=True):
                            st.markdown("##### 🍃 **자연 산책로 & 공원 힐링 대체 안내**")
                            st.write(f"현재 [{fest_sigungu}] 관내에 한국관광공사 공인 웰니스 관광지가 등록되어 있지 않습니다. 축제 행사장 주변의 자연 산책로 또는 근린공원에서 가벼운 산책과 함께 여유로운 쉼으로 여독을 풀어보세요.")
                    else:
                        st.success(f"✅ [{fest_sigungu}] 관내 한국관광공사 선정 웰니스 명소 매칭 ({len(verified_w[:3])}건)")
                        st.markdown("#### 🌿 추천 웰니스 힐링 명소 (관내 추천 목록)")

                        w_cols = st.columns(max(1, len(verified_w[:3])))
                        for w_idx, w_item in enumerate(verified_w[:3]):
                            with w_cols[w_idx]:
                                with st.container(border=True):
                                    st.markdown(f"##### **{w_item.get('title', '웰니스 명소')}**")
                                    st.markdown(f"<span class='tag-chip' style='background:rgba(72,187,120,0.2); color:#16A34A; font-weight:700;'>🏷️ {w_item.get('theme', '힐링/치유')}</span>", unsafe_allow_html=True)
                                    st.caption(f"📍 위치: {w_item.get('location', '주소 확인')}")
                                    if w_item.get("phone") and w_item.get("phone") != "연락처 미기재":
                                        st.caption(f"📞 {w_item.get('phone')}")

                                    st.markdown("---")
                                    if w_item.get("healing_programs"):
                                        st.markdown("🧘 **치유 프로그램:**")
                                        st.write(w_item.get("healing_programs"))
                                    if w_item.get("overview") and w_item.get("overview") != "한국관광공사 추천 웰니스 관광지":
                                        st.markdown("📖 **시설 개요:**")
                                        st.write(w_item.get("overview"))

                # 체력 맞춤 TIP 배너
                if s_tip:
                    st.markdown(f"""
                    <div style="background: rgba(255, 142, 83, 0.1); border-left: 4px solid #FF8E53; padding: 8px 12px; border-radius: 6px; margin-top: 10px; font-size: 0.92rem;">
                        {s_tip}
                    </div>
                    """, unsafe_allow_html=True)

    # 5. 여행 기획 전문 AI 에디터의 감성 스토리텔링 여행 에세이
    storytelling_text = course_data.get("storytelling_text") or course_data.get("storytelling_summary")
    if storytelling_text:
        st.markdown("---")
        with st.container(border=True):
            col_essay_title, col_essay_btn = st.columns([7, 3])
            with col_essay_title:
                st.markdown("### ✍️ **AI 수석 에디터의 감성 스토리텔링 코스 에세이**")
                st.caption("선택하신 4단계 실제 데이터(주차장·축제·맛집·웰니스)를 기반으로 작성된 1일 여행 에세이 가이드입니다.")
            with col_essay_btn:
                if st.button("🔄 에세이 최신 데이터로 다시 쓰기", use_container_width=True, help="추천 맛집/웰니스 최신 데이터를 반영하여 에세이를 즉시 다시 생성합니다."):
                    cached_custom_course.clear()
                    st.rerun()
            st.markdown(storytelling_text)

    st.markdown("---")
    if st.button("← 🔙 다른 축제 보러가기 (목록으로 돌아가기)", key="bottom_back"):
        st.session_state.page = "list"
        st.rerun()


def get_festival_status_badge(start_date: str, end_date: str) -> str:
    """축제 일정에 따른 상태 뱃지 HTML 생성 (🟢 진행중 / ⏳ D-N 예정 / 🏁 종료)"""
    today = datetime.now().strftime("%Y-%m-%d")
    s = str(start_date).strip()
    e = str(end_date).strip() or s

    if not s and not e:
        return '<span class="tag-chip" style="background: rgba(148, 163, 184, 0.2); color: #94A3B8;">상시운영</span>'

    if e < today:
        return '<span class="tag-chip" style="background: rgba(100, 116, 139, 0.2); color: #94A3B8; font-weight:600;">🏁 지난축제</span>'
    elif s <= today <= e:
        return '<span class="tag-chip" style="background: rgba(72, 187, 120, 0.25); color: #38A169; font-weight:700;">🟢 진행중</span>'
    else:
        try:
            d_today = datetime.strptime(today, "%Y-%m-%d")
            d_start = datetime.strptime(s[:10], "%Y-%m-%d")
            days_left = (d_start - d_today).days
            if days_left <= 0:
                d_str = "오늘 시작!"
            elif days_left == 1:
                d_str = "내일 시작!"
            else:
                d_str = f"D-{days_left}"
            return f'<span class="tag-chip" style="background: rgba(237, 137, 54, 0.25); color: #DD6B20; font-weight:700;">⏳ {d_str}</span>'
        except Exception:
            return '<span class="tag-chip" style="background: rgba(237, 137, 54, 0.25); color: #DD6B20; font-weight:700;">⏳ 시작예정</span>'


def sort_festivals_by_schedule(festivals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """축제 순서 정렬:
    1. 곧 시작하는 축제 우선 (시작일 오름차순: 내일/이번주 등 오늘 이후 가장 먼저 시작하는 축제부터 정렬)
    2. 현재 진행 중인 축제 연계 노출
    3. 이미 지나간 축제는 맨 뒤로 배치 ("지나간 건 나중에")
    """
    today = datetime.now().strftime("%Y-%m-%d")

    upcoming = []
    ongoing = []
    past = []

    for f in festivals:
        s = str(f.get("start_date", "")).strip()
        e = str(f.get("end_date", "")).strip() or s

        if not s and not e:
            past.append(f)
        elif s >= today:
            # 오늘 포함 미래에 시작하는 축제 ("시작하는 날짜를 먼저 보여줘")
            upcoming.append(f)
        elif s <= today <= e:
            # 현재 진행 중인 축제
            ongoing.append(f)
        else:
            # 이미 종료된 지난 축제 ("지나간건 나중에")
            past.append(f)

    # 1. 곧 시작하는 축제: 시작일 빠른 순서대로 정렬 (내일 -> 모레 -> 다음주...)
    upcoming.sort(key=lambda x: str(x.get("start_date", "9999-99-99")).strip() or "9999-99-99")

    # 2. 진행 중인 축제: 종료일 가까운 순서대로 정렬
    ongoing.sort(key=lambda x: str(x.get("end_date", "9999-99-99")).strip() or "9999-99-99")

    # 3. 지난 축제: 최근에 종료된 순서대로 내림차순 정렬
    past.sort(key=lambda x: str(x.get("start_date", "0000-00-00")).strip() or "0000-00-00", reverse=True)

    return upcoming + ongoing + past


# ==============================================================================
# [카드 및 캘린더 컴포넌트 헬퍼 함수]
# ==============================================================================
def render_festival_card(fest_item: Dict[str, Any], tab_key: str, item_idx: int):
    """[요구사항 2 & 3] 축제 카드를 위계감 있게 배치하고 행사 유형 뱃지(지역축제 vs 문화행사)·프로그램·요금·예매 링크 렌더링"""
    f_title = fest_item.get("title", "축제명")
    f_region = fest_item.get("region", "")
    f_sigungu = fest_item.get("sigungu", "")
    f_loc = fest_item.get("location", "장소 미정")
    f_venue = fest_item.get("venue", "")
    f_start = fest_item.get("start_date", "")
    f_end = fest_item.get("end_date", "")
    f_period = f"{f_start} ~ {f_end}".strip(" ~") if (f_start or f_end) else "일정 확인 필요"
    f_spots = fest_item.get("photo_spots", "")
    f_theme = fest_item.get("theme", "문화/체험")
    f_stamina = fest_item.get("stamina_level", "중")
    f_fee = fest_item.get("fee", "무료 관람 (상세 현장 확인)")
    f_programs = fest_item.get("programs", "개막식, 문화예술 공연 및 시민참여 체험 부스 상시 운영")
    f_desc = fest_item.get("detailed_desc") or fest_item.get("description") or fest_item.get("overview", "")
    f_homepage = fest_item.get("homepage", "")
    f_phone = fest_item.get("phone", "")
    f_event_type = fest_item.get("event_type", "지역축제")
    status_badge = get_festival_status_badge(f_start, f_end)

    # [요구사항 3] 행사 유형 뱃지 시각화
    if f_event_type == "문화행사":
        type_badge = '<span class="tag-chip" style="background: rgba(147, 51, 234, 0.2); color: #C084FC; font-weight:700;">🎭 문화행사</span>'
    else:
        type_badge = '<span class="tag-chip" style="background: rgba(59, 130, 246, 0.2); color: #60A5FA; font-weight:700;">🎉 지역축제</span>'

    venue_display = f"{f_venue} ({f_loc})" if f_venue and f_venue != f_loc else f_loc

    with st.container(border=True):
        # [상단]: [진행상태] + [행사유형 뱃지] + [권역/시군구 뱃지] + [체력 소모도 뱃지] + [축제명]
        st.markdown(f"""
        <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; margin-bottom: 6px;">
            {status_badge}
            {type_badge}
            <span class="tag-chip" style="background: rgba(255, 107, 107, 0.18); color: #FF8E53; font-weight:700;">📍 {f_region} · {f_sigungu}</span>
            <span class="tag-chip" style="background: rgba(72, 187, 120, 0.18); color: #38A169; font-weight:700;">🔋 소모 체력 [{f_stamina}]</span>
            <span class="tag-chip">🎨 {f_theme}</span>
        </div>
        <h4 style="margin-top: 4px; margin-bottom: 8px; font-weight: 800; line-height: 1.35;">{f_title}</h4>
        """, unsafe_allow_html=True)

        # [본문 1]: 📅 기간 | 📍 장소 및 주소 | 🎟️ 입장/이용 요금
        st.markdown(f"""
        <div style="font-size: 0.91rem; margin-bottom: 8px; line-height: 1.6;">
            📅 <b>축제 기간:</b> {f_period} &nbsp;|&nbsp; 🎟️ <b>입장/이용 요금:</b> <span style="color: #DC2626; font-weight: 700;">{f_fee}</span><br>
            📍 <b>개최 장소:</b> {venue_display}
        </div>
        """, unsafe_allow_html=True)

        # [요구사항 1-1] 축제 내용(description) 원본 텍스트를 요약하지 말고 3~4줄 이상의 '상세 설명 및 관람 포인트'로 본문에 그대로 출력
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.08); border-left: 3px solid #10B981; border-radius: 6px; padding: 10px 14px; margin: 8px 0 10px 0; font-size: 0.89rem; line-height: 1.6; white-space: pre-line;">
            📖 <b>상세 설명 및 관람 포인트:</b><br>{f_desc if f_desc else f_programs}
        </div>
        """, unsafe_allow_html=True)

        # [본문 2]: 🎪 주요 행사 및 프로그램 안내
        st.markdown(f"""
        <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366F1; border-radius: 6px; padding: 8px 12px; margin: 6px 0 10px 0; font-size: 0.86rem; line-height: 1.5; white-space: pre-line;">
            🎪 <b>주요 프로그램 & 행사:</b><br>{f_programs}
        </div>
        """, unsafe_allow_html=True)

        # [본문 3]: 📸 인생샷 스팟 & 힐링 포인트
        if f_spots and f_spots != "현장 곳곳이 포토존":
            st.caption(f"📸 **인생샷 & 힐링 포인트:** {f_spots}")
        else:
            st.caption("📸 **인생샷 & 힐링 포인트:** 현장 곳곳 랜드마크 포토존")

        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

        # [하단 버튼 영역]: 좌측 [🎟️ 공식 홈페이지 / 예매처], 우측 [👉 맞춤 힐링 동선 짜기]
        btn_c1, btn_c2 = st.columns([1, 1.3])
        
        # URL 유효성 검증 및 결측치 방어
        valid_url = None
        if f_homepage and str(f_homepage).strip().lower() not in ["nan", "none", "null", "-", ""]:
            hp_clean = str(f_homepage).strip()
            if hp_clean.startswith("http://") or hp_clean.startswith("https://"):
                valid_url = hp_clean
            elif hp_clean.startswith("www.") or ("." in hp_clean and "/" not in hp_clean):
                valid_url = "https://" + hp_clean

        with btn_c1:
            if valid_url:
                st.link_button("🎟️ 공식안내/예매", url=valid_url, use_container_width=True)
            elif f_phone:
                st.markdown(f"<div style='text-align:center; padding: 7px 0; font-size: 0.82rem; color: #94A3B8; background: rgba(255,255,255,0.02); border-radius:6px;'>📞 현장 문의: <b>{f_phone}</b></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; padding: 7px 0; font-size: 0.82rem; color: #94A3B8; background: rgba(255,255,255,0.02); border-radius:6px;'>ℹ️ 현장 안내소 문의</div>", unsafe_allow_html=True)

        with btn_c2:
            btn_key = f"btn_card_{tab_key}_{item_idx}_{f_title}"
            if st.button("👉 맞춤 힐링 동선 짜기", key=btn_key, use_container_width=True, type="primary"):
                st.session_state.selected_festival = fest_item
                st.session_state.page = "detail"
                st.rerun()


def render_calendar_view(festivals: List[Dict[str, Any]], tab_key: str):
    """월별 축제 캘린더 & 타임라인 테이블 뷰 렌더러"""
    st.markdown("### 📅 월별 축제 캘린더 & 타임라인 뷰")
    st.caption("축제 개최 일자별 타임라인을 확인하고, 원하는 축제의 힐링 동선을 바로 선택하세요.")

    if not festivals:
        st.warning("선택하신 조건에 예정된 축제가 없습니다.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    cal_data = []
    for idx, f in enumerate(festivals):
        s = str(f.get("start_date", "미정")).strip()
        e = str(f.get("end_date", "미정")).strip() or s
        
        if not s or s == "미정":
            status = "상시"
        elif e < today:
            status = "🏁 지난축제"
        elif s <= today <= e:
            status = "🟢 진행중"
        else:
            status = "⏳ 시작예정"

        cal_data.append({
            "진행상태": status,
            "행사유형": f.get("event_type", "지역축제"),
            "시작일자": s,
            "종료일자": e,
            "권역": f.get("region", ""),
            "시군구": f.get("sigungu", ""),
            "축제명": f.get("title", ""),
            "요금": f.get("fee", "무료 관람 (상세 현장 확인)"),
            "개최장소": f.get("venue", f.get("location", "")),
            "_raw": f
        })

    df_cal = pd.DataFrame(cal_data)

    st.dataframe(
        df_cal[["진행상태", "행사유형", "시작일자", "종료일자", "권역", "시군구", "축제명", "요금", "개최장소"]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("#### 🎯 캘린더에서 바로 코스 선택하기")
    cal_cols = st.columns(3)
    for idx, (_, row) in enumerate(df_cal.iterrows()):
        with cal_cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"{row['진행상태']} `[{row['행사유형']}]` **{row['축제명']}**")
                st.caption(f"📅 {row['시작일자']} ~ {row['종료일자']} | 🎟️ {row['요금']}")
                st.caption(f"📍 {row['권역']} {row['시군구']}")
                if st.button("✨ 코스 보기", key=f"cal_btn_{tab_key}_{idx}", use_container_width=True):
                    st.session_state.selected_festival = row["_raw"]
                    st.session_state.page = "detail"
                    st.rerun()


# ==============================================================================
# [화면 1: 메인 축제 탐색 (리스트 & 캘린더 뷰 + 6대 권역별 탭)]
# ==============================================================================
def render_list_page():
    """전국 축제 목록을 행사유형(지역축제/문화행사)과 권역별 탭, 월별/검색 필터와 함께 탐색하는 메인 화면입니다."""
    
    # 히어로 배너
    stamina_label = {
        "하": ("🔋 하 (방전 직전 / 힐링 집중)", "stamina-low", "무리한 도보 없이 스파/온천 및 편안한 쉼터 위주 코스"),
        "중": ("⚡ 중 (보통 / 대표 알짜 명소)", "stamina-mid", "알짜배기 2대 포토존과 가성비 맛집 & 테마 정원 코스"),
        "상": ("🔥 상 (에너지 100% / 풀코스)", "stamina-high", "전망대·둘레길 풀코스 인생샷과 보양식 & 숲길 트레킹")
    }[st.session_state.user_stamina]

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">🌿 지역축제 맞춤형 힐링 여행 큐레이터</div>
        <div class="hero-subtitle">
            공공데이터 4종<b>(전국 축제 · 안심 주차장 · 착한가격업소 · 한국관광공사 웰니스)</b>을 하나로 연계하여,<br>
            오늘 내 <b>체력 배터리 상태(상/중/하)에 최적화된 [주차장 ➔ 축제/사진스팟 ➔ 가성비 맛집 & 감성 카페 ➔ 웰니스 쉼터]</b> 1일 맞춤 동선을 큐레이션합니다.<br>
            <span style="display:inline-block; margin-top:10px;">
                현재 선택된 체력: <span class="stamina-badge {stamina_label[1]}">{stamina_label[0]}</span> 
                <span style="color: #94A3B8; font-size: 0.9rem;">({stamina_label[2]})</span>
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 전국 축제 데이터 로드
    all_festivals = get_all_festivals()

    # [요구사항 2] 행사 유형 선택 필터 UI 구현
    st.markdown("#### 🎯 축제 일정 및 검색 필터")
    event_type_choice = st.radio(
        "🎪 행사 유형 선택",
        options=["전체 보기", "🎉 신나는 지역축제", "🎭 차분한 문화·예술행사"],
        horizontal=True,
        index=0,
        help="대규모 야외/특산물 축제와 차분한 문화제/예술제/전시 공연 행사를 구분하여 탐색할 수 있습니다."
    )

    col_m, col_q, col_v = st.columns([2, 4, 2])

    with col_m:
        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        selected_month = st.selectbox("📅 월별 필터", options=month_options, index=0)

    with col_q:
        search_query = st.text_input("🔍 축제명 / 시군구 / 프로그램 / 키워드 검색", placeholder="예: 불꽃쇼, 파주, 영화제, 플리마켓, 강릉 ...")

    with col_v:
        view_mode_choice = st.radio(
            "👁️ 보기 방식",
            options=["카드형 리스트 🗂️", "월별 캘린더 📅"],
            horizontal=True,
            index=0 if st.session_state.view_mode == "card" else 1
        )
        st.session_state.view_mode = "card" if "카드형" in view_mode_choice else "calendar"

    # 0단계: 행사 유형 필터 적용 (지역축제 vs 문화행사)
    filtered_base = all_festivals
    if "지역축제" in event_type_choice:
        filtered_base = [f for f in filtered_base if f.get("event_type") == "지역축제"]
    elif "문화" in event_type_choice:
        filtered_base = [f for f in filtered_base if f.get("event_type") == "문화행사"]

    # 1단계: 월별 필터 적용
    if selected_month != "전체":
        target_m = int(selected_month.replace("월", ""))
        def match_month(f):
            s = str(f.get("start_date", "")).strip()
            e = str(f.get("end_date", "")).strip()
            
            m_s = re.search(r"[-./](\d{1,2})[-./]", s) or re.search(r"^\d{4}(\d{2})\d{2}$", s)
            m_e = re.search(r"[-./](\d{1,2})[-./]", e) or re.search(r"^\d{4}(\d{2})\d{2}$", e)
            
            s_m = int(m_s.group(1)) if m_s else None
            e_m = int(m_e.group(1)) if m_e else None
            
            if s_m is None and e_m is None:
                return True
                
            if s_m is not None and e_m is not None:
                if s_m <= e_m:
                    return s_m <= target_m <= e_m
                else: # 연도를 넘기는 기간 (예: 12월 ~ 2월)
                    return target_m >= s_m or target_m <= e_m
            elif s_m is not None:
                return s_m == target_m
            elif e_m is not None:
                return e_m == target_m
            return False
        filtered_base = [f for f in filtered_base if match_month(f)]

    # 2단계: 키워드 검색 필터 적용
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_base = [
            f for f in filtered_base
            if q in f.get("title", "").lower()
            or q in f.get("location", "").lower()
            or q in f.get("sigungu", "").lower()
            or q in f.get("venue", "").lower()
            or q in f.get("programs", "").lower()
            or q in f.get("fee", "").lower()
            or q in f.get("overview", "").lower()
        ]

    st.markdown("---")

    # [요구사항 2] 6대 권역별 탭(Tabs) 카드 뷰 레이아웃 고도화
    tab_defs = [
        ("🌟 전국 전체", "전체", "all"),
        ("🏙️ 수도권", "수도권", "sudo"),
        ("⛰️ 강원권", "강원권", "gw"),
        ("🌾 충청권", "충청권", "cc"),
        ("🌊 전라권", "전라권", "jl"),
        ("🏯 경상권", "경상권", "gs"),
        ("🌴 제주도", "제주도", "jj")
    ]
    region_tabs = st.tabs([td[0] for td in tab_defs])

    for t_idx, (tab_title, tab_region, tab_code) in enumerate(tab_defs):
        with region_tabs[t_idx]:
            # 권역 필터링
            if tab_region != "전체":
                tab_festivals = [f for f in filtered_base if f.get("region") == tab_region]
            else:
                tab_festivals = filtered_base

            # 시작일자 우선 정렬
            tab_festivals = sort_festivals_by_schedule(tab_festivals)

            st.markdown(f"**총 `{len(tab_festivals)}개`의 축제가 검색되었습니다.** (권역: `{tab_region}`, 일정: `{selected_month}` · 다가오는 축제 우선 정렬)")

            # [보기 1: 카드형 리스트 뷰]
            if st.session_state.view_mode == "card":
                if not tab_festivals:
                    st.warning(f"선택하신 조건(권역: {tab_region}, 일정: {selected_month})에 일치하는 축제가 없습니다. 다른 월이나 검색어를 선택해 보세요.")
                else:
                    # 2열 카드 그리드 배치
                    for i in range(0, len(tab_festivals), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(tab_festivals):
                                with cols[j]:
                                    render_festival_card(tab_festivals[i + j], tab_code, i + j)
            # [보기 2: 월별 캘린더 뷰]
            else:
                render_calendar_view(tab_festivals, tab_code)


# ==============================================================================
# [메인 실행 라우터]
# ==============================================================================
# st.session_state.page에 따라 화면을 분기합니다.
if st.session_state.page == "detail":
    render_detail_page()
else:
    render_list_page()
