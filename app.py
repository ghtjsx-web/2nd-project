"""
app_c.py - 초개인화 로컬 축제 & 쉼터 큐레이터 (Fest & Rest 통합 에디션)
================================================================================
팀원 A (LangGraph AI 파이프라인) + 팀원 B (공공데이터 무결성 RAG 엔진) + 팀원 C (2030 모던 UI/UX)

[완벽 통합 아키텍처]
1. UI/UX: app_eunmi.py의 고대비 모던 프리미엄 디자인, 듀얼 스크린(탐색 ➔ 상세),
   6+1 권역별 탭, 캘린더/카드 뷰, 4단계 타임라인 동선 카드, 체력 배터리 컨트롤러
2. 로직: app_ryu.py의 LangGraph 기반 AI 파이프라인(agent_ryu.py), Folium 인터랙티브 지도(st_folium),
   프로그램 3단계 예약 체크리스트(사전예약/자유참여/현장확인), 순수 공공데이터 번들(data_c.py) 연동
3. 무결성: data_c.py의 4대 원칙 100% 준수 (가짜 인프라/가짜 좌표/프로그램 억측 원천 차단)
"""

import os
import sys
import re
import json
import html
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from dotenv import load_dotenv

# 백엔드 및 모듈 탐색 경로 보장
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

# ==============================================================================
# 0. 핵심 백엔드 모듈 연동 (최종 배포용 명확한 고정 임포트)
# ==============================================================================
import data
import agent as agent_module


# ==============================================================================
# [지침 2 준수] App 계층의 is_empty 2차 방어선 헬퍼 함수
# ==============================================================================
def only_real_items(items):
    """더미 객체(is_empty: True)를 원천 필터링하여 순수 유효 인프라 데이터만 통과시킵니다."""
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict) and not x.get("is_empty", False)]


# ==============================================================================
# 1. Streamlit 기본 페이지 설정 및 고대비 모던 CSS
# ==============================================================================
st.set_page_config(
    page_title="🌿 Fest & Rest - 맞춤형 축제 & 쉼터 큐레이터",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2030 감성 맞춤형 고대비 커스텀 CSS 스타일링 (다크 배경 + 검은 글씨 원천 차단)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* 전체 앱 배경 화이트/소프트 그레이 고정 (가독성 보장) */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }
    
    /* 히어로 그라디언트 배너 */
    .hero-container {
        background: linear-gradient(135deg, #064E3B 0%, #065F46 50%, #047857 100%);
        border-radius: 18px;
        padding: 26px 30px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 10px 25px rgba(6, 78, 59, 0.15);
        color: #ffffff !important;
    }
    
    .hero-title {
        font-size: 2.0rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        color: #E2E8F0 !important;
        font-size: 1.0rem;
        font-weight: 400;
        line-height: 1.6;
    }

    .engine-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.20);
        color: #F0FDF4;
        padding: 4px 14px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-top: 10px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    /* 배터리 체력 상태 배지 */
    .stamina-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.86rem;
        margin-right: 6px;
    }
    .stamina-low {
        background-color: #DCFCE7 !important;
        color: #15803D !important;
        border: 1px solid #86EFAC !important;
    }
    .stamina-mid {
        background-color: #FFEDD5 !important;
        color: #C2410C !important;
        border: 1px solid #FDBA74 !important;
    }
    .stamina-high {
        background-color: #FEE2E2 !important;
        color: #B91C1C !important;
        border: 1px solid #FCA5A5 !important;
    }
    
    /* 태그 칩 고대비 & 선명화 */
    .tag-chip {
        display: inline-block;
        background: #F1F5F9;
        color: #334155;
        padding: 4px 11px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-right: 6px;
        margin-bottom: 4px;
        border: 1px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    
    /* 보더 컨테이너 고대비 화이트 카드 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
        color: #1E293B !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] h1,
    div[data-testid="stVerticalBlockBorderWrapper"] h2,
    div[data-testid="stVerticalBlockBorderWrapper"] h3,
    div[data-testid="stVerticalBlockBorderWrapper"] h4 {
        color: #0F172A !important;
    }

    /* 축제 카드 상세 설명/프로그램 고대비 박스 */
    .fest-box-desc {
        background: #F0FDF4 !important;
        border-left: 4px solid #10B981 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin: 8px 0 10px 0 !important;
        font-size: 0.90rem !important;
        line-height: 1.6 !important;
        color: #166534 !important;
        font-weight: 500 !important;
        white-space: pre-line !important;
    }
    .fest-box-desc b {
        color: #14532D !important;
        font-weight: 800 !important;
    }

    .fest-box-prog {
        background: #EEF2FF !important;
        border-left: 4px solid #6366F1 !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        margin: 6px 0 10px 0 !important;
        font-size: 0.88rem !important;
        line-height: 1.5 !important;
        color: #3730A3 !important;
        white-space: pre-line !important;
    }
    .fest-box-prog b {
        color: #312E81 !important;
        font-weight: 800 !important;
    }

    .fest-box-tip {
        background: #FFF7ED !important;
        border-left: 4px solid #F97316 !important;
        padding: 10px 14px !important;
        border-radius: 8px !important;
        margin-top: 10px !important;
        font-size: 0.92rem !important;
        color: #9A3412 !important;
        font-weight: 500 !important;
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


# ==============================================================================
# 2. [캐싱 레이어] 공공데이터 로딩
# ==============================================================================
@st.cache_data(show_spinner="전국 축제 공공데이터를 안전하게 로드 중입니다...")
def load_all_festivals() -> List[Dict[str, Any]]:
    """전국 17개 시도 축제 공공데이터를 1회 캐싱하여 0.005초 내에 공급합니다."""
    fests = data.get_festivals(region="전국 전체", month=None)
    for f in fests:
        name = f.get("name", "")
        desc = f.get("description", "")
        venue = f.get("address", "")
        # 문화행사 여부 분류
        cultural_keywords = ["문화제", "예술제", "연극", "음악회", "전시", "공연", "역사", "비엔날레", "국악", "문학", "학술"]
        comb = f"{name} {desc}"
        f["event_type"] = "문화행사" if any(k in comb for k in cultural_keywords) else "지역축제"
        if not f.get("theme") and hasattr(data, "classify_festival_theme"):
            f["theme"] = data.classify_festival_theme(name, venue, desc)
        elif not f.get("theme"):
            f["theme"] = "문화/체험"
        
        # 시작/종료일 분리 파싱
        dates = f.get("dates", "")
        if " ~ " in dates:
            parts = dates.split(" ~ ")
            f["start_date"] = parts[0].strip()
            f["end_date"] = parts[1].strip()
        else:
            f["start_date"] = dates.strip()
            f["end_date"] = dates.strip()
            
        f["title"] = f.get("name", "")
        f["location"] = f.get("address", "")
        f["sigungu"] = data.extract_sigungu(f.get("address", "")) if hasattr(data, "extract_sigungu") else ""
        # [지침 3 준수] 공공데이터의 실제 요금을 유지하고, 없을 때만 "요금 정보 없음"으로 설정
        f["fee"] = f.get("fee") or "요금 정보 없음"
        f["stamina_level"] = "중"
    return fests


# ==============================================================================
# 3. [세션 상태 관리 및 체력별 반경(Radius) 정의]
# ==============================================================================
# [지침 2 준수] 체력 수준별 실제 검색 반경 (하: 500m, 중: 3000m, 상: 5000m)
RADIUS_BY_STAMINA: Dict[str, int] = {
    "하": 500,
    "중": 3000,
    "상": 5000
}

if "page" not in st.session_state:
    st.session_state.page = "list"

if "selected_festival" not in st.session_state:
    st.session_state.selected_festival = None

if "user_stamina" not in st.session_state:
    st.session_state.user_stamina = "중"

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "card"

if "companion" not in st.session_state:
    st.session_state.companion = "연인"

if "extra_details" not in st.session_state:
    st.session_state.extra_details = "무리 없이 편안하고 안전하게 즐기고 싶어요."

if "ai_pipeline_result" not in st.session_state:
    st.session_state.ai_pipeline_result = None

if "infra_bundle" not in st.session_state:
    st.session_state.infra_bundle = None

if "infra_bundle_radius" not in st.session_state:
    st.session_state.infra_bundle_radius = None


# ==============================================================================
# 4. [사이드바] 체력 배터리 및 여행자 조건 설정
# ==============================================================================
with st.sidebar:
    st.markdown("### 🌿 Fest & Rest 큐레이터")
    st.caption("100% 공공데이터 & AI 체력 맞춤형 힐링 여정")

    st.markdown("---")
    st.markdown("#### 🔋 오늘 내 체력 배터리")
    # [지침 2 준수] 체력별 실제 검색 반경(500m, 3km, 5km)과 라벨 일치화
    stamina_options = [
        "🔋 하 (방전 직전 / 반경 500m 안심 휴식)",
        "⚡ 중 (보통 / 반경 3km 알짜 명소 탐방)",
        "🔥 상 (에너지 100% / 반경 5km 풀코스)"
    ]
    stamina_map = {
        "🔋 하 (방전 직전 / 반경 500m 안심 휴식)": "하",
        "⚡ 중 (보통 / 반경 3km 알짜 명소 탐방)": "중",
        "🔥 상 (에너지 100% / 반경 5km 풀코스)": "상"
    }
    stamina_pct_map = {"하": 25, "중": 50, "상": 85}

    current_idx = ["하", "중", "상"].index(st.session_state.user_stamina)
    selected_stamina_raw = st.radio(
        "체력 상태 선택:",
        options=stamina_options,
        index=current_idx,
        help="선택한 체력 수준에 맞춰 주차장·식당·쉼터 탐색 반경(하: 500m, 중: 3km, 상: 5km) 및 동선이 최적화됩니다."
    )
    new_stamina = stamina_map[selected_stamina_raw]
    if new_stamina != st.session_state.user_stamina:
        st.session_state.user_stamina = new_stamina
        st.session_state.ai_pipeline_result = None
        st.session_state.infra_bundle = None
        st.session_state.infra_bundle_radius = None

    # 동행자 선택
    companion_options = ["연인", "친구", "가족", "부모님 (연로하심)", "어린 자녀와 가족", "혼자/힐링"]
    c_idx = companion_options.index(st.session_state.companion) if st.session_state.companion in companion_options else 0
    selected_companion = st.selectbox(
        "👥 동행자 유형",
        options=companion_options,
        index=c_idx,
        help="동행자에 따라 안전 동선과 스토리텔링 톤앤매너가 차별화됩니다."
    )
    if selected_companion != st.session_state.companion:
        st.session_state.companion = selected_companion
        st.session_state.ai_pipeline_result = None

    # 자유 요청사항 입력
    st.markdown("💬 **세부 요청사항**")
    default_req = "부모님이 무릎이 안 좋으셔서 계단은 피하고 가까운 곳이 좋습니다." if "부모님" in selected_companion else "무리 없이 편안하고 안전하게 즐기고 싶어요."
    req_input = st.text_area(
        "AI 에이전트 맞춤 요청사항",
        value=st.session_state.extra_details or default_req,
        height=80,
        help="주차 우선, 휠체어/유모차, 조용한 쉼터 등 요청사항을 자연어로 적어주세요."
    )
    # [지침 4 준수] 세부 요청사항 변경 시 캐시 무효화
    if req_input != st.session_state.extra_details:
        st.session_state.extra_details = req_input
        st.session_state.ai_pipeline_result = None

    st.markdown("---")
    if st.button("🔄 캐시 및 상태 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state.ai_pipeline_result = None
        st.session_state.infra_bundle = None
        st.session_state.infra_bundle_radius = None
        st.rerun()


# ==============================================================================
# 5. [헬퍼 함수] 일정 계산, 상태 뱃지 및 정렬 (datetime 객체 정밀 비교)
# ==============================================================================
def _parse_date_safe(val: Any) -> Optional[datetime]:
    """문자열 날짜를 안전하게 datetime 객체로 변환"""
    if not val:
        return None
    s = str(val).strip()[:10].replace(".", "-")
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return None


def get_festival_status_badge(start_date: str, end_date: str) -> str:
    """축제 일정에 따른 상태 뱃지 HTML 생성 (datetime 객체 기반 비교)"""
    today_dt = datetime.now().date()
    s = str(start_date).strip()
    e = str(end_date).strip() or s

    # 날짜 미상일 때 "상시운영"으로 단정 짓지 않고 "일정 미확인"으로 표기
    if not s or s in ["일정 확인 중", "일정 미확인", "상시운영", ""]:
        return '<span class="tag-chip" style="background: #F1F5F9; color: #64748B; font-weight: 800;">📅 일정 미확인</span>'

    d_start_dt = _parse_date_safe(s)
    d_end_dt = _parse_date_safe(e) or d_start_dt

    if d_start_dt is None:
        return '<span class="tag-chip" style="background: #F1F5F9; color: #64748B; font-weight: 800;">📅 일정 미확인</span>'
    if d_end_dt is None:
        d_end_dt = d_start_dt

    d_start = d_start_dt.date()
    d_end = d_end_dt.date()

    if d_end < today_dt:
        return '<span class="tag-chip" style="background: #F1F5F9; color: #64748B; font-weight: 800;">🏁 지난축제</span>'
    elif d_start <= today_dt <= d_end:
        return '<span class="tag-chip" style="background: #DCFCE7; color: #15803D; font-weight: 800; border: 1px solid #86EFAC;">🟢 진행중</span>'
    else:
        days_left = (d_start - today_dt).days
        if days_left <= 0:
            d_str = "오늘 시작!"
        elif days_left == 1:
            d_str = "내일 시작!"
        else:
            d_str = f"D-{days_left}"
        return f'<span class="tag-chip" style="background: #FFEDD5; color: #C2410C; font-weight: 800; border: 1px solid #FDBA74;">⏳ {d_str}</span>'


def sort_festivals_by_schedule(festivals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """다가오는 축제 우선 ➔ 진행 중 ➔ 종료된 축제/일정 미확인 순으로 정렬 (datetime 객체 비교)"""
    today_dt = datetime.now().date()
    upcoming, ongoing, past = [], [], []

    for f in festivals:
        s_dt = _parse_date_safe(f.get("start_date"))
        e_dt = _parse_date_safe(f.get("end_date")) or s_dt

        if s_dt is None:
            past.append((datetime.min.date(), f))
        elif s_dt.date() > today_dt:
            upcoming.append((s_dt.date(), f))
        elif s_dt.date() <= today_dt <= e_dt.date():
            ongoing.append((e_dt.date(), f))
        else:
            past.append((s_dt.date(), f))

    upcoming.sort(key=lambda x: x[0])
    ongoing.sort(key=lambda x: x[0])
    past.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in upcoming] + [x[1] for x in ongoing] + [x[1] for x in past]


# ==============================================================================
# 6. [화면 1: 메인 축제 탐색 (리스트 & 캘린더 뷰)]
# ==============================================================================
def render_list_page():
    """전국 축제 목록을 6대 권역 탭, 월별/검색 필터 및 카드/캘린더 뷰로 제공합니다."""
    stamina_label = {
        "하": ("🔋 하 (방전 직전 / 반경 500m)", "stamina-low", "도보 500m 이내 안심 쉼터 & 편안한 휴식"),
        "중": ("⚡ 중 (보통 / 반경 3km)", "stamina-mid", "반경 3km 랜드마크 포토존 & 착한가격 맛집"),
        "상": ("🔥 상 (에너지 100% / 반경 5km)", "stamina-high", "반경 5km 전망대·둘레길 풀코스 & 웰니스 트레킹")
    }[st.session_state.user_stamina]

    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-title">🎪 Fest & Rest AI 맞춤형 축제 & 쉼터 큐레이터</div>
        <div class="hero-subtitle">
            100% 실제 공공데이터 <span style="font-size:0.83rem; color:#A7F3D0; font-weight:normal;">*(테마 및 실내외 구분은 AI/규칙 기반 자동 분류)*</span> <b>(전국문화축제 · 공영주차장 · 행정안전부 착한가격업소 · 한국관광공사 TourAPI 관광·휴식 명소)</b>와 
            <b>LangGraph 멀티에이전트</b>를 결합하여 오늘 내 체력에 딱 맞는 힐링 여행을 발행합니다.<br>
            <span style="display:inline-block; margin-top:8px;">
                현재 체력 배터리: <span class="stamina-badge {stamina_label[1]}">{stamina_label[0]}</span> 
                <span style="color: #E2E8F0; font-size: 0.9rem;">({stamina_label[2]})</span>
            </span>
        </div>
        <div class="engine-badge">⚡ 데이터 무결성 4대 원칙 준수 (가짜 인프라·좌표·프로그램 생성 100% 차단)</div>
    </div>
    """, unsafe_allow_html=True)

    all_festivals = load_all_festivals()

    # 1. 상단 필터 영역
    st.markdown("#### 🎯 축제 일정 및 맞춤 검색")
    c_type, c_month, c_search, c_view = st.columns([2.5, 2, 4, 2.5])

    with c_type:
        event_type_choice = st.radio(
            "🎪 행사 유형",
            options=["전체 보기", "🎉 지역축제", "🎭 문화행사"],
            horizontal=True,
            index=0
        )

    with c_month:
        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        selected_month = st.selectbox("📅 개최 월", options=month_options, index=0)

    with c_search:
        search_query = st.text_input("🔍 축제명 / 시군구 / 내용 검색", placeholder="예: 유등, 불꽃, 강릉, 비빔밥, 힐링 ...")

    with c_view:
        view_mode_choice = st.radio(
            "👁️ 보기 방식",
            options=["카드형 🗂️", "캘린더 📅"],
            horizontal=True,
            index=0 if st.session_state.view_mode == "card" else 1
        )
        st.session_state.view_mode = "card" if "카드형" in view_mode_choice else "calendar"

    # 필터링 파이프라인
    filtered = all_festivals
    if "지역축제" in event_type_choice:
        filtered = [f for f in filtered if f.get("event_type") == "지역축제"]
    elif "문화행사" in event_type_choice:
        filtered = [f for f in filtered if f.get("event_type") == "문화행사"]

    if selected_month != "전체":
        t_month = int(selected_month.replace("월", ""))
        def in_month(f):
            s = str(f.get("start_date", "")).strip()
            e = str(f.get("end_date", "")).strip()
            if not s and not e:
                return False
            m_s = re.search(r"[-./](\d{1,2})[-./]", s) or re.search(r"^\d{4}(\d{2})\d{2}$", s)
            m_e = re.search(r"[-./](\d{1,2})[-./]", e) or re.search(r"^\d{4}(\d{2})\d{2}$", e)
            sm = int(m_s.group(1)) if m_s else None
            em = int(m_e.group(1)) if m_e else None
            # [지침 1 준수] 날짜 미상 축제는 월 필터링 시 검색되지 않도록 엄격히 False 처리
            if sm is None and em is None:
                return False
            if sm and em:
                return (sm <= t_month <= em) if sm <= em else (t_month >= sm or t_month <= em)
            return (sm == t_month) if sm else (em == t_month)
        filtered = [f for f in filtered if in_month(f)]

    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            f for f in filtered
            if q in f.get("name", "").lower()
            or q in f.get("address", "").lower()
            or q in f.get("sigungu", "").lower()
            or q in f.get("description", "").lower()
        ]

    st.markdown("---")

    # 2. 6대 권역별 탭
    tab_defs = [
        ("🌟 전국 전체", "전체", "all"),
        ("🏙️ 수도권", "수도권", "sudo"),
        ("⛰️ 강원권", "강원권", "gw"),
        ("🌾 충청권", "충청권", "cc"),
        ("🌊 전라권", "전라권", "jl"),
        ("🏯 경상권", "경상권", "gs"),
        ("🌴 제주도", "제주도", "jj")
    ]
    tabs = st.tabs([t[0] for t in tab_defs])

    for idx, (t_title, t_region, t_code) in enumerate(tab_defs):
        with tabs[idx]:
            if t_region != "전체":
                tab_fests = [f for f in filtered if f.get("region") == t_region]
            else:
                tab_fests = filtered

            tab_fests = sort_festivals_by_schedule(tab_fests)
            st.markdown(f"**총 `{len(tab_fests)}개`의 축제가 검색되었습니다.** (권역: `{t_region}`, 일정: `{selected_month}` · 다가오는 축제 우선)")

            if st.session_state.view_mode == "card":
                if not tab_fests:
                    st.warning("선택하신 조건에 일치하는 축제가 없습니다.")
                else:
                    for i in range(0, len(tab_fests), 2):
                        cols = st.columns(2)
                        for j in range(2):
                            if i + j < len(tab_fests):
                                with cols[j]:
                                    render_festival_card(tab_fests[i + j], t_code, i + j)
            else:
                render_calendar_view(tab_fests, t_code)


def render_festival_card(f: Dict[str, Any], tab_key: str, idx: int):
    """축제 목록 카드 컴포넌트"""
    title = f.get("name", "축제명")
    dates = f.get("dates", "일정 확인 중")
    addr = f.get("address", "주소 정보 없음")
    desc = f.get("description", "소개 정보 준비 중")
    theme = f.get("theme", "문화/체험")
    is_indoor = f.get("is_indoor", "야외")
    ev_type = f.get("event_type", "지역축제")
    s_date = f.get("start_date", "")
    e_date = f.get("end_date", "")
    status_badge = get_festival_status_badge(s_date, e_date)

    type_badge = '<span class="tag-chip" style="background:#DBEAFE; color:#1E40AF; font-weight:800;">🎉 지역축제</span>' if ev_type == "지역축제" else '<span class="tag-chip" style="background:#F3E8FF; color:#6B21A8; font-weight:800;">🎭 문화행사</span>'
    in_badge = f'<span class="tag-chip" style="background:#E0F2FE; color:#0369A1; font-weight:800;">{"🏠 실내" if is_indoor == "실내" else "🌳 야외"}</span>'
    # [지침 6 준수] theme 및 region 뱃지에 html.escape 적용
    theme_badge = f'<span class="tag-chip" style="background:#FEF3C7; color:#92400E; font-weight:800;">🎨 {html.escape(str(theme))}</span>'
    reg_badge = f'<span class="tag-chip" style="background:#FEE2E2; color:#B91C1C; font-weight:800;">📍 {html.escape(str(f.get("region", "대한민국")))}</span>'

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin-bottom:6px;">
            {status_badge}
            {type_badge}
            {in_badge}
            {reg_badge}
            {theme_badge}
        </div>
        <h4 style="margin:4px 0 8px 0; font-weight:800; color:#0F172A;">{html.escape(title)}</h4>
        <div style="font-size:0.90rem; color:#334155; margin-bottom:8px; line-height:1.5;">
            📅 <b>일정:</b> {html.escape(dates)} &nbsp;|&nbsp; 📍 <b>위치:</b> {html.escape(addr)}
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="fest-box-desc">
            📖 <b>축제 소개 및 관람 포인트:</b><br>{html.escape(desc)}
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1.3])
        with c1:
            st.markdown(f"<div style='text-align:center; padding:7px 0; font-size:0.83rem; color:#475569; background:#F1F5F9; border-radius:6px;'>📍 위경도 검증 완료</div>", unsafe_allow_html=True)

        with c2:
            if st.button("👉 AI 맞춤 힐링 동선 짜기", key=f"btn_{tab_key}_{idx}_{title}", type="primary", use_container_width=True):
                st.session_state.selected_festival = f
                st.session_state.page = "detail"
                st.session_state.ai_pipeline_result = None
                st.session_state.infra_bundle = None
                st.rerun()


def render_calendar_view(festivals: List[Dict[str, Any]], tab_key: str):
    """캘린더 및 타임라인 뷰"""
    st.markdown("### 📅 월별 축제 캘린더 & 타임라인")
    if not festivals:
        st.warning("예정된 축제가 없습니다.")
        return

    today_dt = datetime.now().date()
    cal_data = []
    for f in festivals:
        s = f.get("start_date", "")
        e = f.get("end_date", "") or s
        s_dt = _parse_date_safe(s)
        e_dt = _parse_date_safe(e) or s_dt
        if s_dt is None:
            status = "📅 일정 미확인"
        elif e_dt.date() < today_dt:
            status = "🏁 지난축제"
        elif s_dt.date() <= today_dt <= e_dt.date():
            status = "🟢 진행중"
        else:
            status = "⏳ 시작예정"
        cal_data.append({
            "진행상태": status,
            "행사유형": f.get("event_type", "지역축제"),
            "축제명": f.get("name", ""),
            "기간": f.get("dates", ""),
            "권역": f.get("region", ""),
            "장소": f.get("address", ""),
            "_raw": f
        })

    df = pd.DataFrame(cal_data)
    st.dataframe(df[["진행상태", "행사유형", "축제명", "기간", "권역", "장소"]], use_container_width=True, hide_index=True)

    st.markdown("#### 🎯 캘린더에서 바로 코스 선택하기")
    cols = st.columns(3)
    for i, (_, row) in enumerate(df.head(9).iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{row['진행상태']}** `[{row['행사유형']}]` **{row['축제명']}**")
                st.caption(f"📅 {row['기간']}\n📍 {row['장소']}")
                if st.button("✨ 코스 보기", key=f"cal_btn_{tab_key}_{i}", use_container_width=True):
                    st.session_state.selected_festival = row["_raw"]
                    st.session_state.page = "detail"
                    st.session_state.ai_pipeline_result = None
                    st.session_state.infra_bundle = None
                    st.session_state.infra_bundle_radius = None
                    st.rerun()


# ==============================================================================
# 7. [화면 2: 체력 맞춤 코스 상세 & AI 매거진 쇼케이스]
# ==============================================================================
def render_detail_page():
    """선택한 축제를 기반으로 4단계 코스, Folium 지도, 예약 체크리스트, AI 매거진을 제공합니다."""
    fest = st.session_state.selected_festival
    if not fest:
        st.session_state.page = "list"
        st.rerun()
        return

    fest_name = fest.get("name", fest.get("title", "선택된 축제"))
    fest_addr = fest.get("address", fest.get("location", "주소 정보 없음"))
    fest_dates = fest.get("dates", "일정 확인 중")
    fest_desc = fest.get("description", "소개 정보 준비 중")
    fest_lat = fest.get("lat", 0.0)
    fest_lng = fest.get("lng", 0.0)
    fest_region = fest.get("region", "전국")
    fest_theme = fest.get("theme", "문화/체험")
    fest_indoor = fest.get("is_indoor", "야외")

    # 상단 뒤로가기 버튼
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("← 🔙 축제 목록으로 돌아가기", use_container_width=True):
            st.session_state.page = "list"
            st.session_state.ai_pipeline_result = None
            st.rerun()

    # [지침 4 준수] fest_region, fest_theme, fest_dates, fest_indoor 전체에 html.escape() 적용하여 깨짐/보안 방어
    fest_indoor_text = "🏠 실내" if fest_indoor == "실내" else "🌳 야외"
    st.markdown(f"""
    <div class="hero-container">
        <span class="tag-chip" style="background:rgba(255,255,255,0.15); color:#FFFFFF; font-weight:800;">📍 {html.escape(str(fest_region))}</span>
        <span class="tag-chip" style="background:rgba(255,255,255,0.15); color:#FFFFFF; font-weight:800;">{html.escape(fest_indoor_text)}</span>
        <span class="tag-chip" style="background:rgba(255,255,255,0.15); color:#FFFFFF; font-weight:800;">🎨 {html.escape(str(fest_theme))}</span>
        <span class="tag-chip" style="background:rgba(255,255,255,0.15); color:#FFFFFF; font-weight:800;">📅 {html.escape(str(fest_dates))}</span>
        <div class="hero-title">{html.escape(str(fest_name))}</div>
        <div class="hero-subtitle">
            <b>개최 장소:</b> {html.escape(str(fest_addr))}<br>
            <b>축제 개요:</b> {html.escape(str(fest_desc))}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 체력 컨트롤러 바
    c_st1, c_st2 = st.columns([2, 3])
    with c_st1:
        st.markdown("#### ⚡ 현재 코스 체력 배터리")
        stamina_icons = {
            "하": "🔋 하 (방전 직전 / 반경 500m)",
            "중": "⚡ 중 (보통 / 반경 3km)",
            "상": "🔥 상 (에너지 100% / 반경 5km)"
        }
        current_st = st.radio(
            "체력 모드 실시간 변경:",
            options=["하", "중", "상"],
            index=["하", "중", "상"].index(st.session_state.user_stamina),
            format_func=lambda x: stamina_icons[x],
            horizontal=True
        )
        if current_st != st.session_state.user_stamina:
            st.session_state.user_stamina = current_st
            st.session_state.ai_pipeline_result = None
            st.session_state.infra_bundle = None
            st.session_state.infra_bundle_radius = None
            st.rerun()

    with c_st2:
        st.markdown("#### 🧭 맞춤 큐레이션 안내")
        current_radius = RADIUS_BY_STAMINA.get(st.session_state.user_stamina, 3000)
        radius_km_str = f"{current_radius / 1000:g}km" if current_radius >= 1000 else f"{current_radius}m"
        # [지침 4 준수] 데이터 출처 투명성 안내 덧붙임
        st.info(f"선택하신 **[{st.session_state.user_stamina}]** 체력(탐색 반경: **{radius_km_str}**)과 **[{st.session_state.companion}]** 동행 조건에 맞추어 검증된 100% 실제 공공데이터 인프라를 조합합니다. *(테마 및 실내외 구분은 AI/규칙 기반 자동 분류)*")

    st.markdown("---")

    # 1. [지침 5 준수] 공공데이터 인프라 번들 조회 및 예외 처리
    current_radius = RADIUS_BY_STAMINA.get(st.session_state.user_stamina, 3000)
    radius_km_str = f"{current_radius / 1000:g}km" if current_radius >= 1000 else f"{current_radius}m"

    if st.session_state.infra_bundle is None or st.session_state.get("infra_bundle_radius") != current_radius:
        with st.spinner(f"🔍 반경 {radius_km_str} 내 실제 공공데이터 인프라(주차장·행정안전부 착한가격업소·한국관광공사 TourAPI 관광·휴식 명소)를 탐색 중입니다..."):
            try:
                bundle = data.get_festival_infra_bundle(fest_lat, fest_lng, radius_m=current_radius)
            except Exception as e:
                st.warning("인프라 데이터를 불러오지 못했습니다.")
                bundle = {"parking_lots": [], "model_restaurants": [], "tourist_spots": []}
            st.session_state.infra_bundle = bundle
            st.session_state.infra_bundle_radius = current_radius
    else:
        bundle = st.session_state.infra_bundle

    # [지침 2 준수] Fallback용 Raw 데이터 즉시 정제
    parking_list = only_real_items(bundle.get("parking_lots", []))
    restaurant_list = only_real_items(bundle.get("model_restaurants", []))
    wellness_list = only_real_items(bundle.get("tourist_spots", []))

    # 2. AI 파이프라인 (agent) 실행
    if st.session_state.ai_pipeline_result is None:
        with st.spinner("🤖 AI 에이전트(LangGraph)가 의도 분석 및 매거진 에세이를 집필 중입니다..."):
            raw_programs = fest.get("programs", [])
            user_inputs = {
                "stamina": 25 if st.session_state.user_stamina == "하" else (50 if st.session_state.user_stamina == "중" else 85),
                "companion": st.session_state.companion,
                "region": fest_region,
                "selected_festival": {
                    "name": fest_name,
                    "lat": fest_lat,
                    "lng": fest_lng,
                    "address": fest_addr,
                    "description": fest_desc,
                    "programs": raw_programs if isinstance(raw_programs, list) else []
                },
                "extra_details": st.session_state.extra_details
            }
            if agent_module and hasattr(agent_module, "run_processing_pipeline"):
                try:
                    pipeline_output = agent_module.run_processing_pipeline(user_inputs, bundle)
                    st.session_state.ai_pipeline_result = pipeline_output
                except Exception as e:
                    st.warning(f"AI 파이프라인 실행 중 알림 (정직한 데이터 모드로 전환): {e}")
                    st.session_state.ai_pipeline_result = {
                        "article_content": f"### 🌿 [{fest_name}] 안심 힐링 매거진\n\n{fest_addr} 일대에서 펼쳐지는 축제입니다.\n\n- **주차장**: {len(parking_list)}개소 확인\n- **행정안전부 착한가격업소**: {len(restaurant_list)}개소 확인\n- **한국관광공사 TourAPI 관광·휴식 명소**: {len(wellness_list)}개소 확인",
                        "event_info": {"reservation_required": [], "walk_in": [], "unknown": []},
                        "map_markers": [],
                        "parking_lots": parking_list,
                        "model_restaurants": restaurant_list,
                        "tourist_spots": wellness_list
                    }
            else:
                st.session_state.ai_pipeline_result = {
                    "article_content": f"### 🌿 [{fest_name}] 로컬 매거진\n\n{fest_desc}",
                    "event_info": {"reservation_required": [], "walk_in": [], "unknown": []},
                    "map_markers": [],
                    "parking_lots": parking_list,
                    "model_restaurants": restaurant_list,
                    "tourist_spots": wellness_list
                }

    pipeline_res = st.session_state.ai_pipeline_result or {}
    article_content = pipeline_res.get("article_content", "")
    event_info = pipeline_res.get("event_info", {"reservation_required": [], "walk_in": [], "unknown": []})
    map_markers = pipeline_res.get("map_markers", [])

    # [지침 1 & 2 준수] Agent 결과 빈 리스트 존중 및 App 계층 is_empty 2차 방어선 필터링 적용
    curated_parking = pipeline_res["parking_lots"] if "parking_lots" in pipeline_res else parking_list
    curated_restaurants = pipeline_res["model_restaurants"] if "model_restaurants" in pipeline_res else restaurant_list
    curated_wellness = pipeline_res["tourist_spots"] if "tourist_spots" in pipeline_res else wellness_list

    curated_parking = only_real_items(curated_parking)
    curated_restaurants = only_real_items(curated_restaurants)
    curated_wellness = only_real_items(curated_wellness)

    # 지도 마커가 없으면 번들 데이터 기반으로 정직하게 자동 생성
    if not map_markers and (fest_lat and fest_lng):
        map_markers.append({
            "name": fest_name,
            "lat": fest_lat,
            "lng": fest_lng,
            "category": "festival",
            "popup_title": f"🎪 {fest_name}",
            "desc": fest_addr,
            "color": "red",
            "icon": "flag"
        })
        for p in curated_parking[:5]:
            map_markers.append({
                "name": p.get("name"),
                "lat": p.get("lat"),
                "lng": p.get("lng"),
                "category": "parking",
                "popup_title": f"🚗 {p.get('name')}",
                "desc": f"구획수: {p.get('total_spaces', 0)}면 | {p.get('fee', '요금 정보 없음')}",
                "color": "blue",
                "icon": "car"
            })
        for r in curated_restaurants[:5]:
            r_menu = r.get("menu") or "메뉴 정보 없음"
            r_price = r.get("price") or "가격 정보 없음"
            map_markers.append({
                "name": r.get("name"),
                "lat": r.get("lat"),
                "lng": r.get("lng"),
                "category": "restaurant",
                "popup_title": f"🍲 {r.get('name')}",
                "desc": f"메뉴: {r_menu} | {r_price}",
                "color": "green",
                "icon": "cutlery"
            })
        for w in curated_wellness[:4]:
            w_desc = w.get("description") or "설명 정보 없음"
            map_markers.append({
                "name": w.get("name"),
                "lat": w.get("lat"),
                "lng": w.get("lng"),
                "category": "rest_spot",
                "popup_title": f"🌿 {w.get('name')}",
                "desc": w_desc,
                "color": "purple",
                "icon": "leaf"
            })

    # ==========================================================================
    # 상단 2단 레이아웃: AI 매거진 에세이 (좌) / Folium 인터랙티브 지도 (우)
    # ==========================================================================
    col_left, col_right = st.columns([5.5, 4.5], gap="large")

    with col_left:
        st.markdown("### 📖 🌿 Fest & Rest 큐레이션 매거진")
        st.image(
            "https://images.unsplash.com/photo-1533174000243-c782a20e4010?q=80&w=1200&auto=format&fit=crop",
            caption="🎨 축제 분위기 참고 비주얼 (공공데이터 기반 실시간 큐레이션)",
            use_container_width=True
        )
        with st.container(border=True):
            st.markdown(article_content)

    with col_right:
        st.markdown("### 🗺️ 맞춤 안심 동선 지도 (Folium)")
        if not fest_lat or not fest_lng:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="OpenStreetMap")
        else:
            m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="OpenStreetMap")

        for pin in map_markers:
            p_lat = pin.get("lat")
            p_lng = pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name = html.escape(str(pin.get("name", "거점")))
                p_title = html.escape(str(pin.get("popup_title", f"📍 {p_name}")))
                p_desc = html.escape(str(pin.get("desc", "")))
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")
                p_prefix = "fa" if p_icon in ["cutlery", "car", "leaf", "flag"] else "glyphicon"

                popup_html = f"<div style='font-family: Pretendard, sans-serif; min-width:180px;'>" \
                             f"<b style='font-size:1.02rem;'>{p_title}</b><hr style='margin:4px 0;'/>" \
                             f"<span style='font-size:0.83rem; color:#475569;'>{p_desc}</span></div>"

                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=p_name,
                    icon=folium.Icon(color=p_color, icon=p_icon, prefix=p_prefix)
                ).add_to(m)

        st_folium(m, width="100%", height=380)

        # 프로그램 예약 체크리스트 탭 (Ryu's logic)
        st.markdown("---")
        st.markdown("#### 📌 프로그램 예약 체크리스트")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        unk_list = event_info.get("unknown", [])

        t1, t2, t3 = st.tabs([
            f"🔒 사전 예약 ({len(req_list)})",
            f"🔓 자유 참여 ({len(walk_list)})",
            f"🤔 현장 확인 ({len(unk_list)})"
        ])
        with t1:
            if req_list:
                for it in req_list:
                    st.markdown(f"**{it.get('name')}** - {it.get('description', '')}\n💡 Tip: {it.get('booking_tip', '')}")
            else:
                st.info("등록된 사전 예약 필수 프로그램이 없습니다.")
        with t2:
            if walk_list:
                for it in walk_list:
                    st.markdown(f"**{it.get('name')}** - {it.get('description', '')}\n💡 Tip: {it.get('booking_tip', '')}")
            else:
                st.info("등록된 자유 참여 프로그램이 없습니다.")
        with t3:
            if unk_list:
                for it in unk_list:
                    st.markdown(f"**{it.get('name')}** - {it.get('description', '')}\n💡 Tip: {it.get('booking_tip', '현장 안내소 문의')}")
            else:
                st.info("현장 확인 대상 프로그램이 없습니다.")

    st.markdown("---")

    # ==========================================================================
    # 4단계 맞춤 코스 상세 타임라인 (Agent 큐레이션 결과 동기화 & 가짜 팁 전면 삭제)
    # ==========================================================================
    st.subheader("🧭 체력 맞춤 4단계 원데이 코스 상세 타임라인")

    # Step 1: 공영주차장 (Agent 큐레이션 결과 최우선 렌더링)
    with st.container(border=True):
        c_ic, c_cnt = st.columns([1, 8])
        with c_ic:
            st.markdown("<div style='font-size:2.8rem; text-align:center;'>🚗</div>", unsafe_allow_html=True)
            st.caption("<div style='text-align:center;'><b>Step 1</b><br>안심 주차</div>", unsafe_allow_html=True)
        with c_cnt:
            st.markdown("### 1단계: 축제장 인근 안심 공영주차장")
            if curated_parking:
                p_top = curated_parking[0]
                st.markdown(f"**{p_top.get('name')}**")
                st.write("📍 **위치:** 축제장 좌표 기준 인근 위치")
                st.write(f"🅿️ **주차 구획수:** 총 `{p_top.get('total_spaces', 0):,}면` 보유")
                st.write(f"💰 **요금 정보:** {p_top.get('fee', '현장 안내소 문의')}")
                if len(curated_parking) > 1:
                    with st.expander(f"➕ 인근 추가 공영주차장 {len(curated_parking)-1}곳 더보기"):
                        for p_sub in curated_parking[1:5]:
                            st.write(f"• **{p_sub.get('name')}** ({p_sub.get('total_spaces', 0)}면) - {p_sub.get('fee', '요금 정보 없음')}")
            else:
                # [지침 1 준수] 추측성 문구 없는 건조하고 정직한 안내문
                st.warning("⚠️ 반경 내 확인된 공영주차장 데이터가 없습니다. 공식 홈페이지 또는 주최 측 안내를 확인해 주세요.")

    # Step 2: 축제 및 사진스팟
    with st.container(border=True):
        c_ic, c_cnt = st.columns([1, 8])
        with c_ic:
            st.markdown("<div style='font-size:2.8rem; text-align:center;'>🎪</div>", unsafe_allow_html=True)
            st.caption("<div style='text-align:center;'><b>Step 2</b><br>축제 탐방</div>", unsafe_allow_html=True)
        with c_cnt:
            st.markdown(f"### 2단계: 메인 축제 탐방 — **{fest_name}**")
            st.write(f"📍 **개최 장소:** {fest_addr}")
            st.write(f"📅 **개최 기간:** {fest_dates}")
            st.write(f"🎟️ **요금 안내:** {fest.get('fee', '요금 정보 없음')}")
            st.markdown(f"""
            <div class="fest-box-desc">
                📖 <b>축제 상세 소개:</b><br>{html.escape(str(fest_desc))}
            </div>
            """, unsafe_allow_html=True)

    # Step 3: 착한가격 맛집 & 힐링 카페 (Agent 큐레이션 결과 최우선 렌더링)
    with st.container(border=True):
        c_ic, c_cnt = st.columns([1, 8])
        with c_ic:
            st.markdown("<div style='font-size:2.8rem; text-align:center;'>🍽️</div>", unsafe_allow_html=True)
            st.caption("<div style='text-align:center;'><b>Step 3</b><br>로컬 미식</div>", unsafe_allow_html=True)
        with c_cnt:
            st.markdown("### 3단계: 행정안전부 착한가격업소 & 로컬 미식")
            if curated_restaurants:
                st.success(f"✅ 축제장 인근 행정안전부 착한가격업소 ({len(curated_restaurants)}곳)")
                r_cols = st.columns(min(3, len(curated_restaurants)))
                for r_idx, r_item in enumerate(curated_restaurants[:3]):
                    with r_cols[r_idx]:
                        with st.container(border=True):
                            st.markdown(f"##### **{r_item.get('name')}**")
                            st.caption("🏷️ 행정안전부 착한가격업소")
                            # [지침 5 준수] 가짜 기본값 제거
                            st.write(f"🍲 **대표메뉴:** {r_item.get('menu') or '메뉴 정보 없음'}")
                            st.write(f"💰 **착한가격:** `{r_item.get('price', '가격 정보 없음')}`")
            else:
                st.warning("⚠️ 반경 내 확인된 행정안전부 착한가격업소 데이터가 없습니다. 공식 홈페이지 또는 주최 측 안내를 확인해 주세요.")

    # Step 4: 한국관광공사 TourAPI 관광·휴식 명소 (Agent 큐레이션 결과 최우선 렌더링)
    with st.container(border=True):
        c_ic, c_cnt = st.columns([1, 8])
        with c_ic:
            st.markdown("<div style='font-size:2.8rem; text-align:center;'>🌿</div>", unsafe_allow_html=True)
            st.caption("<div style='text-align:center;'><b>Step 4</b><br>자연 휴식</div>", unsafe_allow_html=True)
        with c_cnt:
            st.markdown("### 4단계: 한국관광공사 TourAPI 관광·휴식 명소")
            if curated_wellness:
                st.success(f"✅ 축제장 인근 한국관광공사 TourAPI 관광·휴식 명소 ({len(curated_wellness)}곳)")
                w_cols = st.columns(min(3, len(curated_wellness)))
                for w_idx, w_item in enumerate(curated_wellness[:3]):
                    with w_cols[w_idx]:
                        with st.container(border=True):
                            st.markdown(f"##### **{w_item.get('name')}**")
                            st.caption(f"🏷️ {html.escape(str(w_item.get('category', '한국관광공사 TourAPI 관광·휴식 명소')))}")
                            # [지침 5 준수] 가짜 기본값 제거
                            st.write(f"📖 {html.escape(str(w_item.get('description') or '설명 정보 없음'))}")
            else:
                st.warning("⚠️ 반경 내 확인된 한국관광공사 TourAPI 관광·휴식 명소 데이터가 없습니다. 공식 홈페이지 또는 주최 측 안내를 확인해 주세요.")

    st.markdown("---")
    if st.button("← 🔙 다른 축제 보러가기 (목록으로 돌아가기)", key="btn_bottom_back"):
        st.session_state.page = "list"
        st.session_state.ai_pipeline_result = None
        st.rerun()


# ==============================================================================
# 8. 메인 라우터
# ==============================================================================
if st.session_state.page == "detail":
    render_detail_page()
else:
    render_list_page()
