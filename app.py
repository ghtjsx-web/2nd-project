"""
app.py - 페스타픽 (FestaPick)
===================================================
29CM & Kinfolk 스타일의 시네마틱 라이프스타일 여행 매거진
100% 공공데이터 기반 체력 & 동행 맞춤형 로컬 축제 에디토리얼 큐레이션 웹 대시보드

[사용자 맞춤 3열 대칭형 제어 패널]
- [좌측 컬럼]: Where & When (목적지 드롭다운 ➔ 방문시기 ➔ 로컬 축제)
- [중앙 컬럼]: Energy & Dynamic Visual (체력 슬라이더 조절 시 실시간 반응형 비주얼 카드)
- [우측 컬럼]: How & Action (동반자 ➔ 이동수단 ➔ 세부 요청사항 ➔ 매거진 발행 버튼)
"""

import os
import sys
import json
import html
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import folium
from streamlit_folium import st_folium

# 백엔드(backend) 및 데이터(festapick) 모듈 경로 자동 등록
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR
for p in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "festapick"), os.path.join(PROJECT_ROOT, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

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
# 1. 대한민국 17개 광역 행정구역 마스터 목록 & 핫 축제 프리셋 (200 OK 검증 URL)
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

FALLBACK_SAFE_IMAGE = "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1200"

HOT_FESTIVALS_PRESET = [
    {
        "name": "순천만 갈대축제",
        "region": "전라남도",
        "month": 10,
        "badge": "VOL. 01 · 힐링 1위",
        "tag": "황금빛 갈대 데크로드 · 흑두루미 생태 쉼터",
        "stamina": 30,
        "companion": "부모님 (연로하심)",
        "transport": "🚗 자가용 (렌터카)",
        "img": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1200",
        "desc": "은빛 갈대와 흑두루미가 맞이하는 순천만의 가을 서정, 계단 없는 평지 무장애 힐링 로드"
    },
    {
        "name": "화담숲 가을 단풍축제",
        "region": "경기도",
        "month": 10,
        "badge": "VOL. 02 · 가을의 색",
        "tag": "모노레일 안심 관람 · 오색 단풍 숲길",
        "stamina": 40,
        "companion": "연인/커플",
        "transport": "🚗 자가용 (렌터카)",
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1200",
        "desc": "완만하게 굽이치는 숲길을 따라 펼쳐지는 400여 종의 다채로운 가을 단풍 파노라마"
    },
    {
        "name": "진주 남강유등축제",
        "region": "경상남도",
        "month": 10,
        "badge": "VOL. 03 · 빛의 야경",
        "tag": "남강 수상 유등 전시 · 촉석루 달빛 산책",
        "stamina": 50,
        "companion": "친구들과 함께",
        "transport": "🚶 도보 (대중교통)",
        "img": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1200",
        "desc": "물과 불, 빛이 어우러져 강물 위에 수놓는 수천 개의 유등, 잊지 못할 가을밤의 낭만"
    }
]


# ==============================================================================
# 2. 29CM 에디토리얼 테마별 고화질 비주얼 큐레이션 엔진
# ==============================================================================
def get_curated_visuals(fest_name: str, region: str) -> Dict[str, str]:
    """축제명과 지역 키워드를 분석하여 잡지 표지 및 3단 여정용 고품질 사진을 큐레이션합니다."""
    name = str(fest_name or "")
    
    if any(k in name for k in ["갈대", "억새", "순천만", "생태", "습지"]):
        return {
            "cover": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
            "spot": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=800"
        }
    elif any(k in name for k in ["단풍", "숲", "산", "화담숲", "단양", "내장산", "지리산"]):
        return {
            "cover": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
            "spot": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?q=80&w=800"
        }
    elif any(k in name for k in ["유등", "빛", "등불", "야경", "불꽃", "야행", "남강"]):
        return {
            "cover": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
            "spot": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=800"
        }
    elif any(k in name for k in ["바다", "해변", "항", "해양", "대하", "꽃게", "자갈치", "포구"]):
        return {
            "cover": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
            "spot": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=800"
        }
    else:
        return {
            "cover": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1400",
            "spot": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=800"
        }


def get_festival_status_badge(dates_str: str) -> str:
    """축제 기간 문자열을 분석하여 [진행 중 / 개최 예정 / 축제 종료] 뱃지 HTML을 반환합니다."""
    if not dates_str:
        return '<span class="editorial-badge badge-neutral">SCHEDULE CHECK</span>'
    
    date_patterns = re.findall(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", str(dates_str))
    if not date_patterns:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:20])}</span>'
    
    try:
        today = date.today()
        start_y, start_m, start_d = map(int, date_patterns[0])
        start_date = date(start_y, start_m, start_d)
        
        if len(date_patterns) >= 2:
            end_y, end_m, end_d = map(int, date_patterns[1])
            end_date = date(end_y, end_m, end_d)
        else:
            end_date = start_date
            
        if start_date <= today <= end_date:
            return '<span class="editorial-badge badge-live">● LIVE NOW</span>'
        elif today < start_date:
            d_day = (start_date - today).days
            return f'<span class="editorial-badge badge-D-day">D-{d_day}</span>'
        else:
            return '<span class="editorial-badge badge-ended">ENDED</span>'
    except Exception:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:20])}</span>'


# ==============================================================================
# 3. Streamlit 페이지 설정 & 반응형 3열 패널 CSS
# ==============================================================================
st.set_page_config(
    page_title="FestaPick · 에디토리얼 로컬 힐링 여정 매거진",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,800;1,600&display=swap');

@font-face {
    font-family: 'Pretendard-Local';
    src: local('Pretendard'),
         url('./Pretendard-1.3.9/web/static/woff2/Pretendard-Regular.woff2') format('woff2');
    font-weight: 400;
}

* {
    font-family: 'Pretendard', 'Pretendard-Local', -apple-system, BlinkMacSystemFont, sans-serif;
    letter-spacing: -0.4px;
}

/* 사이드바 UI 완전 제거 */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* 29CM 에디토리얼 어반 보태니컬 세이지 그린 캔버스 (다른 PC에서도 동일한 힐링 무드) */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #EFF4F1 !important;
    color: #111827 !important;
}

/* 크로스 플랫폼 테마 고정 (OS 다크모드/라이트모드 무관 일관된 UI 보장) */
.stSelectbox label, .stSlider label, .stRadio label, .stTextInput label {
    color: #1F2937 !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
}
div[data-baseweb="select"] > div {
    background-color: #FAFCFA !important;
    border-color: #CCD8D0 !important;
    color: #111827 !important;
    border-radius: 8px !important;
}
div[data-baseweb="input"] > div {
    background-color: #FAFCFA !important;
    border-color: #CCD8D0 !important;
    color: #111827 !important;
    border-radius: 8px !important;
}
div.stButton > button[kind="primary"] {
    background-color: #1B4332 !important;
    border: 1px solid #143225 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 10px 18px !important;
    box-shadow: 0 4px 14px rgba(27, 67, 50, 0.25) !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #2D5A43 !important;
    border-color: #244835 !important;
    box-shadow: 0 6px 18px rgba(27, 67, 50, 0.35) !important;
    transform: translateY(-1px);
}

/* 전체 컨텐츠 폭을 1180px로 제한하여 와이드 모니터에서 쩍 벌어짐 방지 */
.main .block-container {
    max-width: 1180px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3.5rem !important;
    margin: 0 auto !important;
}

/* 상단 29CM 미니멀 헤더 내비게이션 */
.editorial-top-nav {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 18px 0 16px 0;
    border-bottom: 2.5px solid #1B4332;
    margin-bottom: 24px;
}
.brand-serif {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #1B4332;
    line-height: 1.1;
    margin: 0;
    white-space: nowrap !important;
    word-break: keep-all !important;
}
.brand-subline {
    font-size: 0.80rem;
    letter-spacing: 0.12em;
    color: #4A6B5B;
    text-transform: uppercase;
    font-weight: 700;
    margin-top: 4px;
}
.editorial-pill-bar {
    display: flex;
    gap: 8px;
}
.nav-tag {
    font-size: 0.74rem;
    letter-spacing: 0.04em;
    color: #1B4332;
    background: #DEE8E2;
    padding: 5px 12px;
    border-radius: 9999px;
    font-weight: 700;
    white-space: nowrap;
    border: 1px solid #CCD8D0;
}

/* 3열 대칭형 제어 패널 카드 박스 - 3개 열 동일한 높이(Equal Height) 완벽 맞춤 */
[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    align-items: stretch !important;
}
[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 0% !important;
    align-self: stretch !important;
}
[data-testid="column"] > div,
[data-testid="column"] > [data-testid="stVerticalBlock"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 100% !important;
    height: 100% !important;
    align-self: stretch !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CCD8D0 !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 24px -4px rgba(27, 67, 50, 0.08), 0 2px 6px -1px rgba(0, 0, 0, 0.03) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
    display: flex !important;
    flex-direction: column !important;
    box-sizing: border-box !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #1B4332 !important;
    box-shadow: 0 14px 30px -4px rgba(27, 67, 50, 0.14) !important;
    transform: translateY(-2px);
}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    padding: 22px 22px 24px 22px !important;
    gap: 12px !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    height: 100% !important;
    justify-content: space-between !important;
    box-sizing: border-box !important;
}
.panel-card-title {
    font-size: 0.98rem;
    font-weight: 800;
    color: #111827;
    margin-bottom: 2px;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1.5px solid #F0F4F2;
    padding-bottom: 12px;
}
.panel-step-badge {
    background-color: #1B4332;
    color: #FFFFFF;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 3px 8px;
    border-radius: 4px;
    display: inline-block;
}

/* 중앙 컬럼: 체력 반응형 다이내믹 비주얼 카드 */
.stamina-dynamic-container {
    width: 100% !important;
    height: 200px !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    position: relative !important;
    background-color: #F3F4F6 !important;
    margin-bottom: 4px !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.08) !important;
}
.stamina-dynamic-img {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    object-position: center !important;
    display: block !important;
    filter: brightness(0.96) contrast(1.02) !important;
    transition: transform 0.4s ease, filter 0.3s ease !important;
}
.stamina-dynamic-container:hover .stamina-dynamic-img {
    transform: scale(1.04) !important;
}
.stamina-dynamic-overlay {
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(180deg, rgba(0,0,0,0.12) 0%, rgba(0,0,0,0.02) 40%, rgba(0,0,0,0.70) 100%) !important;
    padding: 14px 16px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    color: #FFFFFF !important;
}

/* 29CM 시네마틱 매거진 표지 (Magazine Hero Cover) */
.magazine-hero-cover {
    position: relative;
    width: 100%;
    height: 480px;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 34px;
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.18);
    background-color: #1F2937;
}
.cover-bg-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.72) contrast(1.05);
}
.cover-overlay-content {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.4) 40%, rgba(0,0,0,0.85) 100%);
    padding: 44px 48px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    color: #FFFFFF;
}
.cover-vol-tag {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.15rem;
    letter-spacing: 0.22em;
    font-weight: 600;
    opacity: 0.9;
    text-transform: uppercase;
}
.cover-main-headline {
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.25;
    margin: 12px 0 16px 0;
    text-shadow: 0 3px 12px rgba(0,0,0,0.4);
}
.cover-sub-meta {
    font-size: 1.02rem;
    opacity: 0.92;
    line-height: 1.6;
    max-width: 800px;
    font-weight: 300;
}
.cover-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
}
.cover-badge {
    background: rgba(255, 255, 255, 0.22);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.4);
    padding: 6px 15px;
    border-radius: 9999px;
    font-size: 0.80rem;
    font-weight: 700;
    letter-spacing: -0.2px;
}

/* 3단 비주얼 스토리 타임라인 카드 */
.story-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.story-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 28px -6px rgba(0,0,0,0.08);
}
.story-card-img-wrap {
    width: 100%;
    height: 190px;
    overflow: hidden;
    position: relative;
    background-color: #F3F4F6;
}
.story-card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.4s ease;
}
.story-card:hover .story-card-img {
    transform: scale(1.04);
}
.story-step-badge {
    position: absolute;
    top: 12px;
    left: 12px;
    background: #111827;
    color: #FFFFFF;
    padding: 4px 10px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    border-radius: 4px;
}
.story-card-body {
    padding: 18px 20px;
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

/* 29CM 에디토리얼 뱃지 */
.editorial-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 3px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
.badge-live {
    background: #111827;
    color: #FFFFFF;
}
.badge-D-DAY,
.badge-D-day {
    background: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #DBEAFE;
}
.badge-ended {
    background: #F3F4F6;
    color: #9CA3AF;
}
.badge-neutral {
    background: #F3F4F6;
    color: #4B5563;
}

/* 첫 화면 핫한 축제 프리뷰 카드 */
.preset-editorial-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 4px 18px rgba(0,0,0,0.03);
    transition: all 0.3s ease;
    height: 100%;
    display: flex;
    flex-direction: column;
}
.preset-editorial-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 18px 32px -8px rgba(0,0,0,0.09);
    border-color: #111827;
}

/* 매거진 텍스트 본문 */
.editorial-article-paper {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 32px 36px;
    line-height: 1.85;
    box-shadow: 0 6px 20px rgba(0,0,0,0.02);
}

/* 모바일 최적화 미디어 쿼리 */
@media (max-width: 768px) {
    .editorial-top-nav {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 10px !important;
    }
    .brand-serif {
        font-size: 1.75rem !important;
    }
    .editorial-pill-bar {
        flex-wrap: wrap !important;
    }
    .magazine-hero-cover {
        height: 380px !important;
    }
    .cover-overlay-content {
        padding: 24px 20px !important;
    }
    .cover-main-headline {
        font-size: 1.65rem !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 4. 29CM 미니멀 에디토리얼 탑 헤더
# ==============================================================================
st.markdown("""
<div class="editorial-top-nav">
    <div>
        <h1 class="brand-serif">FestaPick</h1>
        <div class="brand-subline">내 체력에 꼭 맞춘, 로컬 힐링 & 축제 여행 매거진</div>
    </div>
    <div class="editorial-pill-bar">
        <span class="nav-tag">🎪 1,264 FESTIVALS</span>
        <span class="nav-tag">🍲 9,563 STORES</span>
        <span class="nav-tag">🅿️ 18,883 PARKINGS</span>
        <span class="nav-tag">🌿 694 WELLNESS</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 5. 세션 상태 관리
# ==============================================================================
if "curation_result" not in st.session_state:
    st.session_state.curation_result = None
if "selected_region_state" not in st.session_state:
    st.session_state.selected_region_state = "전국 전체"
if "selected_month_state" not in st.session_state:
    st.session_state.selected_month_state = "10월"
if "selected_fest_name_state" not in st.session_state:
    st.session_state.selected_fest_name_state = None
if "stamina_state" not in st.session_state:
    st.session_state.stamina_state = 35
if "trigger_quick_run" not in st.session_state:
    st.session_state.trigger_quick_run = False


# ==============================================================================
# 6. 사용자 와이어프레임 3열 대칭형 제어 패널 구현
# ==============================================================================
col_where, col_energy, col_action = st.columns(3, gap="medium")

# -------------------------------------------------------------
# [좌측 컬럼 (1)]: Where & When (목적지 ➔ 방문시기 ➔ 로컬 축제)
# -------------------------------------------------------------
with col_where:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 01</span> <span>📍 여행지 & 축제 탐색</span></div>', unsafe_allow_html=True)

        # 1) 목적지 (드롭다운)
        region_idx = ADMIN_REGIONS.index(st.session_state.selected_region_state) if st.session_state.selected_region_state in ADMIN_REGIONS else 0
        selected_region = st.selectbox(
            "목적지 (Region)",
            options=ADMIN_REGIONS,
            index=region_idx,
            key="main_region"
        )

        # 2) 방문시기 (Month)
        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        month_idx = month_options.index(st.session_state.selected_month_state) if st.session_state.selected_month_state in month_options else 10
        selected_month = st.selectbox(
            "방문시기 (Month)",
            options=month_options,
            index=month_idx,
            key="main_month"
        )
        selected_month_int = int(selected_month.replace("월", "")) if selected_month != "전체" else None

        # 데이터 로드
        try:
            festivals_list = get_festivals(region=selected_region, month=selected_month_int)
        except Exception as e:
            st.error(f"⚠️ 축제 공공데이터 조회 실패: {e}")
            festivals_list = []

        fest_data = None

        # 3) 로컬 축제 (드롭다운)
        if not festivals_list:
            st.warning("선택하신 조건에 등록된 축제가 없습니다.")
        else:
            festival_options = {f["name"]: f for f in festivals_list}
            fest_keys = list(festival_options.keys())
            
            def_fest_idx = 0
            if st.session_state.selected_fest_name_state in fest_keys:
                def_fest_idx = fest_keys.index(st.session_state.selected_fest_name_state)
                
            selected_fest_name = st.selectbox(
                f"로컬 축제 ({len(festival_options)}개)",
                options=fest_keys,
                index=def_fest_idx,
                key="main_fest"
            )
            fest_data = festival_options[selected_fest_name]

        if fest_data:
            fest_dates_raw = str(fest_data.get("dates", "일정 확인 중"))
            status_badge_html = get_festival_status_badge(fest_dates_raw)
            st.markdown(f"""
            <div style="font-size:0.80rem; color:#4B5563; margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
                <span>📅 {html.escape(fest_dates_raw[:22])}</span>
                <span>{status_badge_html}</span>
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------
# [중앙 컬럼 (2)]: Energy & Dynamic Visual (체력 슬라이더 실시간 연동 비주얼)
# -------------------------------------------------------------
with col_energy:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 02</span> <span>🪫 체력 & 실시간 반응</span></div>', unsafe_allow_html=True)

        # 현재 체력 상태값 동기화
        current_stamina = st.session_state.get("stamina_slider", st.session_state.get("stamina_state", 35))
        st.session_state.stamina_state = current_stamina

        # 슬라이더 구간별 다이내믹 비주얼 (직관적인 사람 실루엣/뒷모습) & 카피 분기
        if current_stamina <= 30:
            stamina_img = "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800"
            stamina_badge = "🪫 저강도 안심 쉼표"
            stamina_copy = "도보 500m 이내 · 쉼터 집중형 코스"
            badge_style = "background:#EF4444; color:#FFFFFF;"
        elif current_stamina <= 69:
            stamina_img = "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=800"
            stamina_badge = "🔋 황금 밸런스 산책"
            stamina_copy = "반경 2~3km 산책 · 축제 50 : 쉼터 50"
            badge_style = "background:#F59E0B; color:#FFFFFF;"
        else:
            stamina_img = "https://images.unsplash.com/photo-1501555088652-021faa106b9b?q=80&w=800"
            stamina_badge = "⚡ 파워 풀코스 액티브"
            stamina_copy = "반경 5km+ 활력 탐방 · 풀코스 위주"
            badge_style = "background:#10B981; color:#FFFFFF;"

        # 1) 상단: 밝고 선명한 풀커버리지 다이내믹 이미지 렌더링
        st.markdown(f"""
        <div class="stamina-dynamic-container">
            <img class="stamina-dynamic-img" 
                 src="{stamina_img}" 
                 alt="체력 직관적 비주얼" 
                 onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
            <div class="stamina-dynamic-overlay">
                <span style="font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:4px; width:fit-content; {badge_style}">
                    {stamina_badge}
                </span>
                <div>
                    <div style="font-size:1.15rem; font-weight:800; letter-spacing:-0.5px; margin-bottom:3px; text-shadow:0 2px 8px rgba(0,0,0,0.65);">
                        체력 {current_stamina}% 맞춤 모드
                    </div>
                    <div style="font-size:0.80rem; opacity:0.95; font-weight:500; text-shadow:0 1px 4px rgba(0,0,0,0.65);">
                        {stamina_copy}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # 2) 하단: 체력 배터리 슬라이더 배치
        st.slider(
            "체력 배터리 (슬라이더 조절)",
            min_value=0,
            max_value=100,
            value=current_stamina,
            step=5,
            key="stamina_slider"
        )


# -------------------------------------------------------------
# [우측 컬럼 (3)]: How & Action (동반자 ➔ 이동수단 ➔ 요청사항 ➔ 발행)
# -------------------------------------------------------------
with col_action:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 03</span> <span>🚗 동행 & 여정 발행</span></div>', unsafe_allow_html=True)

        # 1) 동반자 (사용자 요청: 우측 상단 배치)
        companion = st.selectbox(
            "👥 동반자 선택",
            options=["부모님 (연로하심)", "나홀로 힐링", "연인/커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"],
            index=0,
            key="main_companion"
        )

        # 2) 이동수단 선택
        transport = st.radio(
            "🚗 이동수단",
            options=["🚗 자가용 (렌터카)", "🚶 도보 (대중교통)"],
            index=0,
            horizontal=True,
            key="main_transport"
        )

        # 3) 세부 요청사항
        default_request = "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 주차하기 편하고 넓은 곳이 좋겠습니다." if "부모님" in companion else "무리 없이 편안하게 즐기고 싶어요."
        extra_details = st.text_input(
            "💬 에디터에게 전달할 세부 요청사항 (직접 입력)",
            value=default_request,
            key="main_extra"
        )

        # 4) 매거진 발행 버튼
        run_button = st.button(
            "🗞️ 매거진 발행하기",
            type="primary",
            use_container_width=True,
            disabled=(fest_data is None)
        )

# 3열 카드 높이 실시간 100% 자동 동기화 (JavaScript Auto-Equalizer)
import streamlit.components.v1 as _st_components
_st_components.html("""
<script>
function syncCardHeights() {
    try {
        const doc = window.parent.document;
        if (!doc) return;
        const wrappers = doc.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]');
        if (wrappers && wrappers.length >= 3) {
            const first = wrappers[0].getBoundingClientRect();
            const second = wrappers[1].getBoundingClientRect();
            const isHorizontal = Math.abs(first.top - second.top) < 40;
            
            if (isHorizontal) {
                // 1단계: 자연스러운 내부 콘텐츠 높이 측정을 위해 일시 초기화
                for (let i = 0; i < 3; i++) {
                    wrappers[i].style.height = 'auto';
                    wrappers[i].style.minHeight = '0px';
                }
                // 2단계: 3개 카드 중 가장 높은 카드의 높이 측정
                const h1 = wrappers[0].scrollHeight || wrappers[0].offsetHeight;
                const h2 = wrappers[1].scrollHeight || wrappers[1].offsetHeight;
                const h3 = wrappers[2].scrollHeight || wrappers[2].offsetHeight;
                const maxHeight = Math.max(h1, h2, h3);
                
                // 3단계: 3개 카드 모두 가장 높은 카드의 높이로 완벽 고정
                if (maxHeight > 100) {
                    for (let i = 0; i < 3; i++) {
                        wrappers[i].style.height = maxHeight + 'px';
                        wrappers[i].style.minHeight = maxHeight + 'px';
                    }
                }
            } else {
                for (let i = 0; i < 3; i++) {
                    wrappers[i].style.height = 'auto';
                    wrappers[i].style.minHeight = 'auto';
                }
            }
        }
    } catch(e) {}
}

syncCardHeights();
setTimeout(syncCardHeights, 60);
setTimeout(syncCardHeights, 200);
setTimeout(syncCardHeights, 500);
setTimeout(syncCardHeights, 1000);
if (!window._stCardSyncInterval) {
    window._stCardSyncInterval = setInterval(syncCardHeights, 300);
    window.addEventListener('resize', syncCardHeights);
}
</script>
""", height=0, width=0)

st.markdown("<hr style='margin:26px 0 32px 0; border:none; border-top:1px solid #E5E7EB;'/>", unsafe_allow_html=True)


# ==============================================================================
# 7. 백엔드 파이프라인 가동
# ==============================================================================
if st.session_state.trigger_quick_run:
    run_button = True
    st.session_state.trigger_quick_run = False

if run_button:
    if not fest_data:
        st.error("선택된 축제 정보가 없습니다. 축제를 먼저 선택해 주세요.")
    else:
        with st.spinner("🖋️ FestaPick 수석 에디터가 100% 공공데이터 기반 맞춤형 여행 매거진을 조판 중입니다..."):
            user_inputs = {
                "stamina": current_stamina,
                "companion": companion,
                "transport": transport,
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

            try:
                infra = get_festival_infra_bundle(
                    fest_lat=fest_data.get("lat", 0.0),
                    fest_lng=fest_data.get("lng", 0.0),
                    radius_m=3000,
                    target_address=fest_data.get("address", "")
                )
                p_lots = infra.get("parking_lots", [])
                m_rests = infra.get("model_restaurants", [])
                t_spots = infra.get("tourist_spots", [])
            except Exception as e:
                st.error(f"⚠️ 공공데이터 API 연동 장애가 발생했습니다: {e}")
                p_lots, m_rests, t_spots = [], [], []

            api_data = {
                "parking_lots": p_lots,
                "model_restaurants": m_rests,
                "tourist_spots": t_spots
            }

            try:
                pipeline_output = run_processing_pipeline(user_inputs, api_data)
                st.session_state.curation_result = pipeline_output
                st.session_state.active_fest = fest_data
                st.session_state.active_transport = transport
                st.session_state.active_stamina = current_stamina
                st.session_state.active_companion = companion
                st.toast("🗞️ FestaPick 맞춤 여행 매거진 에디토리얼이 성공적으로 발행되었습니다!", icon="✨")
            except Exception as e:
                st.error(f"❌ LangGraph 파이프라인 실행 오류: {str(e)}")


# ==============================================================================
# 8. 29CM 에디토리얼 쇼케이스 렌더링
# ==============================================================================
result = st.session_state.get("curation_result")
active_fest = st.session_state.get("active_fest", fest_data)
active_transport = st.session_state.get("active_transport", "도보 (대중교통)")
active_stamina = st.session_state.get("active_stamina", 35)
active_companion = st.session_state.get("active_companion", "부모님 (연로하심)")

if result and active_fest:
    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": [], "unknown": []})
    map_markers = result.get("map_markers", [])

    fest_name = active_fest.get("name", "로컬 힐링 축제")
    fest_addr = active_fest.get("address", "대한민국 로컬 명소")
    fest_region = active_fest.get("region", "전국")
    fest_dates = active_fest.get("dates", "2026 Season")
    visuals = get_curated_visuals(fest_name, fest_region)

    # [WOW 포인트 1] 29CM 시네마틱 매거진 표지 (Hero Cover)
    cover_tag = "DRIVE ROAD" if "자가용" in active_transport else "WALKING REST"
    
    st.markdown(f"""
    <div class="magazine-hero-cover">
        <img class="cover-bg-image" 
             src="{visuals['cover']}" 
             alt="{fest_name}" 
             onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
        <div class="cover-overlay-content">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="cover-vol-tag">ISSUE · {fest_region.upper()}</span>
                <span style="font-size:0.80rem; letter-spacing:0.15em; font-weight:700; opacity:0.85;">100% PUBLIC DATA CURATION</span>
            </div>
            <div>
                <h2 class="cover-main-headline">{fest_name}</h2>
                <div class="cover-sub-meta">
                    바람과 쉼이 머무는 곳, 체력에 맞추어 가장 안심하고 누리는 1일 힐링 에디토리얼 여정.<br>
                    <strong>📍 {fest_addr}</strong> &nbsp;·&nbsp; <strong>📅 {fest_dates}</strong>
                </div>
                <div class="cover-badge-row">
                    <span class="cover-badge">🪫 체력 {active_stamina}% 맞춤</span>
                    <span class="cover-badge">{active_transport}</span>
                    <span class="cover-badge">👥 {active_companion}</span>
                    <span class="cover-badge">🌿 {cover_tag}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # [WOW 포인트 2] 3단 비주얼 스토리 타임라인 카드
    st.markdown("""
    <div style="margin-bottom:16px;">
        <span style="font-family:'Playfair Display', serif; font-size:1.4rem; font-weight:800; color:#111827;">Curated 3-Step Journey</span>
        <span style="font-size:0.86rem; color:#6B7280; margin-left:10px;">에디터가 추천하는 오늘의 3대 핵심 거점</span>
    </div>
    """, unsafe_allow_html=True)

    first_restaurant = next((p for p in map_markers if p.get("category") == "restaurant"), None)
    first_spot = next((p for p in map_markers if p.get("category") == "rest_spot"), None)

    rest_name = first_restaurant.get("name", "착한가격 식당") if first_restaurant else "로컬 추천 맛집"
    rest_desc = first_restaurant.get("desc", "정직한 가격의 대표 먹거리") if first_restaurant else "주변 외식 정보"
    spot_name = first_spot.get("name", "자연 쉼터") if first_spot else "웰니스 치유 쉼터"
    spot_desc = first_spot.get("desc", "몸과 마음을 비우는 안심 휴식처") if first_spot else "인근 힐링 명소"

    story_col1, story_col2, story_col3 = st.columns(3, gap="medium")

    with story_col1:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{visuals['spot']}" 
                     alt="축제" 
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">10:30 AM · FESTIVAL</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#059669; font-weight:800; margin-bottom:4px;">STEP 01</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{fest_name}</h4>
                    <p style="font-size:0.84rem; color:#4B5563; line-height:1.5; margin:0;">계단 없는 평지 데크와 여유로운 축제장 관람</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with story_col2:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{visuals['food']}" 
                     alt="맛집" 
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">12:30 PM · LUNCH</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#D97706; font-weight:800; margin-bottom:4px;">STEP 02</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{rest_name}</h4>
                    <p style="font-size:0.84rem; color:#4B5563; line-height:1.5; margin:0;">{rest_desc}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with story_col3:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{visuals['rest']}" 
                     alt="쉼터" 
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">02:30 PM · WELLNESS</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#2563EB; font-weight:800; margin-bottom:4px;">STEP 03</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{spot_name}</h4>
                    <p style="font-size:0.84rem; color:#4B5563; line-height:1.5; margin:0;">{spot_desc}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:36px 0 28px 0; border:none; border-top:1px solid #E5E7EB;'/>", unsafe_allow_html=True)

    # [WOW 포인트 3] 에디터 기사 전문 & 인터랙티브 지도 2단 레이아웃
    col_left, col_right = st.columns([58, 42], gap="large")

    with col_left:
        sub_c1, sub_c2 = st.columns([7, 3])
        with sub_c1:
            st.markdown('<div style="font-family:\'Playfair Display\', serif; font-size:1.35rem; font-weight:800; color:#111827;">Editorial Reading</div>', unsafe_allow_html=True)
            st.caption("FestaPick 수석 에디터가 작성한 정직한 여행 에세이입니다.")
        with sub_c2:
            if st.button("📋 기사 전문 복사", use_container_width=True):
                st.toast("✨ 에디토리얼 매거진 전문이 클립보드에 복사되었습니다! 카톡에 공유해보세요.", icon="📋")

        st.markdown('<div class="editorial-article-paper">', unsafe_allow_html=True)
        st.markdown(article_content)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div style="font-family:\'Playfair Display\', serif; font-size:1.35rem; font-weight:800; color:#111827; margin-bottom:4px;">Safe Mobility Map</div>', unsafe_allow_html=True)
        st.caption("축제장(🔴), 주차장(🔵), 착한가격업소(🟢), 웰니스(🟠) 4색 공공 핀")
        
        fest_lat = active_fest.get("lat")
        fest_lng = active_fest.get("lng")

        if not fest_lat or not fest_lng:
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")
        else:
            m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="CartoDB positron")

        for pin in map_markers:
            p_lat = pin.get("lat")
            p_lng = pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name_raw = pin.get("name", "거점")
                p_name = html.escape(str(p_name_raw))
                p_title = html.escape(str(pin.get("popup_title", f"📍 {p_name_raw}")))
                p_desc = html.escape(str(pin.get("desc", "")))
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")
                p_prefix = "fa" if p_icon in ["cutlery", "car", "leaf", "flag"] else "glyphicon"

                popup_html = f"<div style='font-family: Pretendard, sans-serif; min-width:180px;'>" \
                             f"<b style='font-size:1.02rem; color:#111827;'>{p_title}</b><hr style='margin:4px 0;'/>" \
                             f"<span style='font-size:0.83rem; color:#4B5563;'>{p_desc}</span></div>"

                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=p_name,
                    icon=folium.Icon(color=p_color, icon=p_icon, prefix=p_prefix)
                ).add_to(m)

        st_folium(m, width="100%", height=370)

        st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #E5E7EB;'/>", unsafe_allow_html=True)

        # 📌 프로그램 예약 체크리스트 (3단 탭)
        st.markdown("##### 📌 프로그램 사전 체크리스트")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        unknown_list = event_info.get("unknown", [])

        tab1, tab2, tab3 = st.tabs([
            f"사전 예약 ({len(req_list)})",
            f"자유 참여 ({len(walk_list)})",
            f"현장 확인 ({len(unknown_list)})"
        ])

        with tab1:
            if req_list:
                for item in req_list:
                    r_name = html.escape(str(item.get('name', '')))
                    r_desc = html.escape(str(item.get('description', '')))
                    r_tip = html.escape(str(item.get('booking_tip', '')))
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #FEE2E2; border-left:3px solid #EF4444; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
                        <div style="font-weight:700; font-size:0.9rem; color:#991B1B;">{r_name}</div>
                        <div style="font-size:0.82rem; color:#4B5563; margin:2px 0;">{r_desc}</div>
                        <div style="font-size:0.78rem; color:#EF4444; font-weight:600;">Tip: {r_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("사전 예약 필수 프로그램이 없습니다.")

        with tab2:
            if walk_list:
                for item in walk_list:
                    w_name = html.escape(str(item.get('name', '')))
                    w_desc = html.escape(str(item.get('description', '')))
                    w_tip = html.escape(str(item.get('booking_tip', '')))
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #DCFCE7; border-left:3px solid #10B981; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
                        <div style="font-weight:700; font-size:0.9rem; color:#065F46;">{w_name}</div>
                        <div style="font-size:0.82rem; color:#4B5563; margin:2px 0;">{w_desc}</div>
                        <div style="font-size:0.78rem; color:#10B981; font-weight:600;">Tip: {w_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("자유 참여 프로그램이 없습니다.")

        with tab3:
            if unknown_list:
                for item in unknown_list:
                    u_name = html.escape(str(item.get('name', '')))
                    u_desc = html.escape(str(item.get('description', '')))
                    u_tip = html.escape(str(item.get('booking_tip', '')))
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #FEF3C7; border-left:3px solid #F59E0B; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
                        <div style="font-weight:700; font-size:0.9rem; color:#92400E;">{u_name}</div>
                        <div style="font-size:0.82rem; color:#4B5563; margin:2px 0;">{u_desc}</div>
                        <div style="font-size:0.78rem; color:#F59E0B; font-weight:600;">Tip: {u_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("현장 확인 대상 프로그램이 없습니다.")

        st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #E5E7EB;'/>", unsafe_allow_html=True)

        # 🍽️ 착한가격업소 & 🌿 웰니스 쉼터 추천 카드
        st.markdown("##### 🍽️ 착한가격업소 & 🌿 웰니스 쉼터 추천")

        restaurant_pins = [p for p in map_markers if p.get("category") == "restaurant"]
        rest_spot_pins = [p for p in map_markers if p.get("category") == "rest_spot"]

        tab_rest, tab_spot = st.tabs([
            f"착한 식당 ({len(restaurant_pins)})",
            f"웰니스 쉼터 ({len(rest_spot_pins)})"
        ])

        with tab_rest:
            if restaurant_pins:
                for r in restaurant_pins:
                    r_name = html.escape(str(r.get("name", "착한가격업소")))
                    r_menu = html.escape(str(r.get("menu", "대표메뉴")))
                    r_price = html.escape(str(r.get("price", "가격 정보 없음")))
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#111827; font-size:0.92rem;">🍲 {r_name}</strong>
                            <span style="font-size:0.75rem; color:#059669; font-weight:700;">착한가격</span>
                        </div>
                        <div style="font-size:0.82rem; color:#4B5563; margin-top:2px;">{r_menu} · <span style="color:#111827; font-weight:600;">{r_price}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("등록된 착한가격업소 정보가 없습니다.")

        with tab_spot:
            if rest_spot_pins:
                for s in rest_spot_pins:
                    s_name = html.escape(str(s.get("name", "관광·휴식 명소")))
                    s_desc = html.escape(str(s.get("desc", "인근 관광 및 휴식 명소")))
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#111827; font-size:0.92rem;">🌿 {s_name}</strong>
                            <span style="font-size:0.75rem; color:#2563EB; font-weight:700;">웰니스</span>
                        </div>
                        <div style="font-size:0.82rem; color:#4B5563; margin-top:2px;">{s_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("등록된 웰니스 쉼터 정보가 없습니다.")

else:
    # -------------------------------------------------------------
    # 첫 진입 화면: 29CM 에디토리얼 프리셋 쇼케이스 3선
    # -------------------------------------------------------------
    st.markdown("""
    <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
            <span style="font-family:'Playfair Display', serif; font-size:1.6rem; font-weight:800; color:#111827;">Editor's Top 3 Picks</span>
            <div style="font-size:0.88rem; color:#6B7280; margin-top:3px;">수석 에디터가 엄선한 이번 시즌 가장 걷기 좋은 힐링 여정</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="large")

    for idx, (col, hot) in enumerate(zip([col1, col2, col3], HOT_FESTIVALS_PRESET)):
        with col:
            st.markdown(f"""
            <div class="preset-editorial-card">
                <div style="width:100%; height:230px; overflow:hidden; background-color:#1F2937;">
                    <img src="{hot['img']}" 
                         alt="{hot['name']}" 
                         style="width:100%; height:100%; object-fit:cover;" 
                         onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                </div>
                <div style="padding:22px; display:flex; flex-direction:column; justify-content:space-between; flex-grow:1;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span class="editorial-badge badge-live">{hot['badge']}</span>
                            <span style="font-size:0.80rem; color:#6B7280; font-weight:600;">📍 {hot['region']}</span>
                        </div>
                        <h3 style="font-family:'Playfair Display', Pretendard, serif; font-size:1.35rem; font-weight:800; color:#111827; margin:6px 0 10px 0;">{hot['name']}</h3>
                        <p style="font-size:0.86rem; color:#4B5563; line-height:1.6; margin-bottom:14px;">{hot['desc']}</p>
                    </div>
                    <div style="background:#F9FAFB; border-radius:6px; padding:10px 12px; font-size:0.80rem; color:#374151; margin-bottom:14px;">
                        ✨ {hot['tag']}<br>
                        🪫 권장 체력 {hot['stamina']}% · {hot['transport']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗞️ {hot['name']} 에디토리얼 읽기", key=f"quick_btn_{idx}", use_container_width=True):
                st.session_state.selected_region_state = hot["region"]
                st.session_state.selected_month_state = f"{hot['month']}월"
                st.session_state.selected_fest_name_state = hot["name"]
                st.session_state.trigger_quick_run = True
                st.rerun()

    st.markdown("<hr style='margin:36px 0 20px 0; border:none; border-top:1px solid #E5E7EB;'/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#9CA3AF; font-size:0.84rem; padding-bottom:30px;">
        FESTAPICK EDITORIAL · 100% PUBLIC DATA MEETS GENERATIVE AI · ALL RIGHTS RESERVED
    </div>
    """, unsafe_allow_html=True)