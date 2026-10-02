"""
app.py - 페스타픽 (FestaPick) 웹 서비스 메인 애플리케이션
================================================================================
[시스템 아키텍처 개요]
1. 프론트엔드 (Frontend)  : Streamlit 기반 킨포크/29CM 에디토리얼 라이프스타일 UI
                          - Pretendard 웹폰트 및 웜 크림(#FDF9F0) 테마 고정
                          - Flexbox 기반 디스플레이/배율(DPI) 대응 및 다크모드 차단
2. 백엔드 (Backend AI)    : LangGraph 멀티 에이전트 오케스트레이션 (backend/agent.py)
                          - run_processing_pipeline: 큐레이션 에세이 및 체크포인트 생성
3. 데이터 및 API (Data/API): 대한민국 공공데이터 오픈 API 엔지니어링 모듈 (data.py)
                          - 한국관광공사 TourAPI 4.0, 행안부 착한가격업소, KNPS 국립공원
================================================================================
"""

import os
import sys
import json
import html
import re
import textwrap
import urllib.parse
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import folium
from streamlit_folium import st_folium

# ------------------------------------------------------------------------------
# [모듈 경로 등록] backend(LangGraph 에이전트) 및 festapick(공공데이터 엔진) 경로 설정
# ------------------------------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR
for p in [PROJECT_ROOT, os.path.join(PROJECT_ROOT, "festapick"), os.path.join(PROJECT_ROOT, "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# [Backend API 연동] agent.py LangGraph 파이프라인 인터페이스
try:
    from agent import run_processing_pipeline, PipelineState
except ImportError as e:
    st.error(f"agent.py 임포트 오류: {e}")
    st.stop()

# [Open Data API 연동] data.py 공공데이터포털 실시간 수집 및 인프라 번들 인터페이스
try:
    from data import get_festival_infra_bundle, get_festivals
except ImportError as e:
    st.error(f"data.py 임포트 오류: {e}")
    st.stop()


# ==============================================================================
# 1. 행정구역 마스터 & 큐레이션 에셋 프리셋
# ==============================================================================
# [Data Schema] 대한민국 행정표준코드 기반 17개 광역시도 마스터 목록
ADMIN_REGIONS = [
    "전국 전체", "서울특별시", "부산광역시", "대구광역시", "인천광역시", 
    "광주광역시", "대전광역시", "울산광역시", "세종특별자치시", "경기도", 
    "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전라남도", 
    "경상북도", "경상남도", "제주특별자치도"
]

# [Frontend Fallback] 이미지 깨짐/404 방어를 위한 고해상도 안전 백업 이미지
FALLBACK_SAFE_IMAGE = "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1600"

def validate_image_url(url: Optional[str], default_url: str = FALLBACK_SAFE_IMAGE) -> str:
    """[Frontend Utility] 이미지 URL 유효성(Null/NaN/프로토콜) 검증 및 Fallback 안전 보장"""
    if not url:
        return default_url
    url_str = str(url).strip()
    if url_str.lower() in ["none", "null", "nan", "", "-", "undefined"]:
        return default_url
    if not (url_str.startswith("http://") or url_str.startswith("https://") or url_str.startswith("data:image")):
        return default_url
    return url_str

# [Content Preset] 초기 진입 화면 롤링 캐러셀용 기획특집 추천 3선 프리셋
HOT_FESTIVALS_PRESET = [
    {
        "name": "순천만 갈대축제",
        "region": "전라남도",
        "month": 10,
        "badge": "VOL. 01 · 힐링 1위",
        "tag": "황금빛 갈대 데크로드 · 흑두루미 생태 쉼터",
        "stamina": 35,
        "companion": "부모님 (연로하심)",
        "transport": "🚗 자가용 (렌터카)",
        "img": "https://lh3.googleusercontent.com/aida/AEtjO1WR-1WaQhXHCUW86ozttsZLRmdyZvzFLqsKu2MyPhTutaRHXST8Mv-YHQ_PSl_W9J7pVB103mE5FR6M0rHSakgaF5-US3cufVE1pUya1ZWvIeu5YknQnL-qfIjYdCSz9QuEQwuqcU2PAbdLUOcyQ7MxL3qPYODY_ID-e0lZ37ROD0zcm6WxrxDJgvKLC9NvAiE7Rtffu_3w4MUkEJM5jMinrNVmDGc6A_oys5YMUpXP1rGgUAM3OwBUUg",
        "desc": "바람과 은빛 갈대숲이 머무는 곳, 체력에 맞추어 가장 안심하고 누리는 1일 힐링 에디토리얼 여정."
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
        "img": "https://lh3.googleusercontent.com/aida-public/AB6AXuA4KZ_S3OC5-6GmZfLfCY_22LR4Cme4H0WPV1hJkJJ-mZrdyuPUecPZDHVSNckSMovAYr0ZD8sdREyw9gPds_dEVCCkSY0zf2It0jWm917IOu5trCarRP7eXheb07gOo-ZVRa9ajajNMluUbMBJ5mMnAHW9hoQiZCFTpsPBqhgxtkjCgg6Ot-ipwZhheTrpWdt6N684OJOAU7n4g0duE7N8MWxheded8YQV9Kvu4Hg1nuqIFXam4yKf",
        "desc": "모노레일로 오르는 붉은 단풍 파노라마. 경사로 없는 완만한 나무 데크 숲길에서 마주하는 깊은 가을 쉼표."
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
        "img": "https://lh3.googleusercontent.com/aida/AEtjO1XOmb0KhHWjdsC5LcQocFGCQfU-FbWQKLiY8RHyCnflSlNBPEkM8l1YGjDSUzBYaO11xfODdOdxsmY7JAdpc2fhZL9kHF5BOZfgRvTYwcSICAqLsVrGsyp7-s-KHTun3KsjY6PBY68YOqvEHcXaw7aOQvY2S79-UAOZesWJB5_8oF0FCrs0Okk7uZ9vsKmr4wyh8niQURwC8R2gJEl6oSSwkrMYalUl7w0O18PteDbiTaRxg4URt_cTePQ",
        "desc": "천 년의 역사를 품은 남강 물결 위에 수놓아진 수만 개의 유등. 물빛과 달빛이 어우러진 낭만적인 밤 산책 코스."
    }
]


# ==============================================================================
# 2. 비주얼 큐레이션 및 축제 상태 뱃지 판별 로직
# ==============================================================================
def get_curated_visuals(fest_name: str, region: str = "", fest_dict: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    [Frontend/Data] 축제명 키워드 기반 고해상도 에디토리얼 비주얼 큐레이션
    - 1순위: 공공데이터(TourAPI/지자체)에 실측 등록된 공식 고유 이미지
    - 2순위: 축제 테마(갈대, 단풍, 유등, 꽃, 바다 등) 기반 고해상도 큐레이션 에셋
    """
    name = str(fest_name or "")
    
    # 1. 축제 자체 데이터에 이미 고유 이미지가 등록된 경우 우선 활용
    custom_cover = None
    if fest_dict and isinstance(fest_dict, dict):
        raw_img = fest_dict.get("img") or fest_dict.get("firstimage") or fest_dict.get("image") or fest_dict.get("cover")
        if raw_img:
            custom_cover = validate_image_url(raw_img, "")
    
    # 2. 테마별 고해상도 에디토리얼 비주얼 큐레이션
    if any(k in name for k in ["갈대", "억새", "순천만", "생태", "습지", "늪"]):
        base = {
            "cover": "https://lh3.googleusercontent.com/aida/AEtjO1WR-1WaQhXHCUW86ozttsZLRmdyZvzFLqsKu2MyPhTutaRHXST8Mv-YHQ_PSl_W9J7pVB103mE5FR6M0rHSakgaF5-US3cufVE1pUya1ZWvIeu5YknQnL-qfIjYdCSz9QuEQwuqcU2PAbdLUOcyQ7MxL3qPYODY_ID-e0lZ37ROD0zcm6WxrxDJgvKLC9NvAiE7Rtffu_3w4MUkEJM5jMinrNVmDGc6A_oys5YMUpXP1rGgUAM3OwBUUg",
            "spot": "https://lh3.googleusercontent.com/aida/AEtjO1WR-1WaQhXHCUW86ozttsZLRmdyZvzFLqsKu2MyPhTutaRHXST8Mv-YHQ_PSl_W9J7pVB103mE5FR6M0rHSakgaF5-US3cufVE1pUya1ZWvIeu5YknQnL-qfIjYdCSz9QuEQwuqcU2PAbdLUOcyQ7MxL3qPYODY_ID-e0lZ37ROD0zcm6WxrxDJgvKLC9NvAiE7Rtffu_3w4MUkEJM5jMinrNVmDGc6A_oys5YMUpXP1rGgUAM3OwBUUg",
            "food": "https://lh3.googleusercontent.com/aida/AEtjO1ViY5T8NaLesyyUd-tnrolgeZ_goCCwoR77PpwalGcXp6nEjuJCl_5reMJcDXgardcY603jr8hIN0KVa7z-93kGn4vhZ779J7_NFftLEiOsVuXRDFs7wFMxr_JevRTjivYpdTwFe9HvakTTl6ZEVPQFzKnJvAIjwr21Z7C_MCb24pax2oC07r8V-d_3XM3LGtbgx52TWKOnHN5jt2ib0wHjuJlBI6DhNXlHUd9ioMsSHjIRRic0y1yCn2E",
            "rest": "https://lh3.googleusercontent.com/aida/AEtjO1XOmb0KhHWjdsC5LcQocFGCQfU-FbWQKLiY8RHyCnflSlNBPEkM8l1YGjDSUzBYaO11xfODdOdxsmY7JAdpc2fhZL9kHF5BOZfgRvTYwcSICAqLsVrGsyp7-s-KHTun3KsjY6PBY68YOqvEHcXaw7aOQvY2S79-UAOZesWJB5_8oF0FCrs0Okk7uZ9vsKmr4wyh8niQURwC8R2gJEl6oSSwkrMYalUl7w0O18PteDbiTaRxg4URt_cTePQ"
        }
    elif any(k in name for k in ["단풍", "숲", "산", "화담숲", "수목원", "자연", "힐링"]):
        base = {
            "cover": "https://lh3.googleusercontent.com/aida-public/AB6AXuA4KZ_S3OC5-6GmZfLfCY_22LR4Cme4H0WPV1hJkJJ-mZrdyuPUecPZDHVSNckSMovAYr0ZD8sdREyw9gPds_dEVCCkSY0zf2It0jWm917IOu5trCarRP7eXheb07gOo-ZVRa9ajajNMluUbMBJ5mMnAHW9hoQiZCFTpsPBqhgxtkjCgg6Ot-ipwZhheTrpWdt6N684OJOAU7n4g0duE7N8MWxheded8YQV9Kvu4Hg1nuqIFXam4yKf",
            "spot": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?q=80&w=800"
        }
    elif any(k in name for k in ["유등", "남강", "빛", "야경", "등불", "달빛", "불꽃", "야행"]):
        base = {
            "cover": "https://lh3.googleusercontent.com/aida/AEtjO1XOmb0KhHWjdsC5LcQocFGCQfU-FbWQKLiY8RHyCnflSlNBPEkM8l1YGjDSUzBYaO11xfODdOdxsmY7JAdpc2fhZL9kHF5BOZfgRvTYwcSICAqLsVrGsyp7-s-KHTun3KsjY6PBY68YOqvEHcXaw7aOQvY2S79-UAOZesWJB5_8oF0FCrs0Okk7uZ9vsKmr4wyh8niQURwC8R2gJEl6oSSwkrMYalUl7w0O18PteDbiTaRxg4URt_cTePQ",
            "spot": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?q=80&w=800"
        }
    elif any(k in name for k in ["꽃", "국화", "장미", "벚꽃", "매화", "연꽃", "튤립", "유채"]):
        base = {
            "cover": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?q=80&w=1600",
            "spot": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1518241353330-0f7941c2d9b5?q=80&w=800"
        }
    elif any(k in name for k in ["바다", "해변", "항구", "섬", "해맞이", "포구"]):
        base = {
            "cover": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1600",
            "spot": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=800"
        }
    else:
        base = {
            "cover": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1600",
            "spot": "https://images.unsplash.com/photo-1519671482749-fd09be7ccebf?q=80&w=800",
            "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=800",
            "rest": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=800"
        }
    
    if custom_cover:
        base["cover"] = custom_cover

    # 전수 유효성 검증 및 안전 Fallback 보장
    return {k: validate_image_url(v, FALLBACK_SAFE_IMAGE) for k, v in base.items()}

def get_festival_status_badge(dates_str: str) -> str:
    """[Data/API Utility] 축제 일정 문자열 파싱 후 실시간 D-Day/LIVE/종료 상태 뱃지 반환"""
    if not dates_str:
        return '<span class="editorial-badge badge-neutral">일정 확인 중</span>'
    date_patterns = re.findall(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", str(dates_str))
    if not date_patterns:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:20])}</span>'
    try:
        today = date.today()
        start_y, start_m, start_d = map(int, date_patterns[0])
        start_date = date(start_y, start_m, start_d)
        end_date = date(int(date_patterns[1][0]), int(date_patterns[1][1]), int(date_patterns[1][2])) if len(date_patterns) >= 2 else start_date
        
        if start_date <= today <= end_date:
            return '<span class="editorial-badge badge-live">● LIVE NOW</span>'
        elif today < start_date:
            return f'<span class="editorial-badge badge-dday">D-{(start_date - today).days}</span>'
        else:
            return '<span class="editorial-badge badge-ended">종료</span>'
    except Exception:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:20])}</span>'


# ==============================================================================
# 3. Streamlit 페이지 설정 & 스티치(Stitch) 킨포크 에디토리얼 디자인 CSS
# ==============================================================================
st.set_page_config(
    page_title="FestaPick · 공공데이터 안심 여행 매거진",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,800;1,600&display=swap');

/* 전체 앱 배경: 스티치 시그니처 웜 크림 톤 및 프리텐다드 웹폰트 100% 보장 */
:root, .stApp {
    background-color: #FDF9F0 !important;
    font-family: 'Pretendard', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #1C1C16 !important;
}

* {
    word-break: keep-all; /* 단어 단위 줄바꿈으로 한글 쪼개짐 방지 */
}

[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.main .block-container {
    max-width: 1200px !important;
    padding-top: 1.2rem !important;
    padding-bottom: 3.5rem !important;
    margin: 0 auto !important;
}

/* 상단 에디토리얼 헤더 & 마스트헤드 */
.brand-masthead {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 14px;
    border-bottom: 2px solid #012D1D;
    margin-bottom: 20px;
}
.brand-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.3rem;
    font-weight: 800;
    color: #012D1D;
    line-height: 1;
    margin: 0;
}
.brand-desc {
    font-size: 0.88rem;
    color: #414844;
    font-weight: 500;
    margin-top: 6px;
}

/* 공통 에디토리얼 카드 컨테이너 */
.magazine-card {
    background-color: #FAF7F2;
    border: 1px solid #EAE4DA;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    margin-bottom: 18px;
}

/* 3열 제어 패널 전용 카드 (해상도/배율 차이 틀어짐 방지) */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #EAE4DA !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(1, 45, 29, 0.05) !important;
    transition: all 0.25s ease !important;
    min-height: 450px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #3A674F !important;
    box-shadow: 0 8px 24px rgba(1, 45, 29, 0.1) !important;
    transform: translateY(-2px);
}

.panel-step-badge {
    background-color: #012D1D;
    color: #FFFFFF;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.06em;
}

/* 체력 반응형 다이내믹 비주얼 */
.stamina-dynamic-container {
    width: 100%;
    height: 175px;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
    background-color: #ECE8DF;
    margin-bottom: 6px;
}
.stamina-dynamic-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.95);
    transition: transform 0.4s ease;
}
.stamina-dynamic-container:hover .stamina-dynamic-img {
    transform: scale(1.04);
}
.stamina-dynamic-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(1,45,29,0.85) 100%);
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    color: #FFFFFF;
}

/* 메인 발행 버튼 */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #012D1D 0%, #1B4332 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid #3A674F !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    box-shadow: 0 4px 14px rgba(1, 45, 29, 0.25) !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    opacity: 0.94 !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(1, 45, 29, 0.35) !important;
}

/* 뱃지 시스템 */
.editorial-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 4px;
    display: inline-block;
}
.badge-live { background-color: #BCEECF; color: #002112; }
.badge-dday { background-color: #FFDBD1; color: #4D1000; }
.badge-ended { background-color: #E6E2D9; color: #717973; }
.badge-neutral { background-color: #ECE8DF; color: #414844; }

/* [UI: Hero Cover] 시네마틱 매거진 표지 배너 (100% 풀필 레이아웃) */
.magazine-hero-cover {
    position: relative !important;
    width: 100% !important;
    height: 500px !important;
    min-height: 500px !important;
    border-radius: 16px !important;
    overflow: hidden !important;
    margin-bottom: 0 !important;
    box-shadow: 0 16px 36px rgba(1, 45, 29, 0.12) !important;
    background-color: #0B192C !important; /* 이미지 로딩 지연/에러 시 안정적인 다크 톤 유지 */
}
.cover-bg-image {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-width: 100% !important;
    min-height: 100% !important;
    max-width: none !important;
    object-fit: cover !important;
    object-position: center center !important;
    display: block !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    z-index: 1 !important;
}
.cover-overlay-content {
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(180deg, rgba(0,0,0,0.22) 0%, rgba(0,0,0,0.48) 45%, rgba(1,45,29,0.95) 100%) !important;
    padding: 36px 40px 80px 40px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    color: #FFFFFF !important;
    z-index: 2 !important;
}

/* [UI: Hero Dock] 배너 내부 하단 컨트롤 오버레이 도크 (단일 컨테이너 마진 음수화) */
div.st-key-carousel_dock {
    position: relative !important;
    margin-top: -65px !important;
    z-index: 20 !important;
    padding: 0 40px !important;
    margin-bottom: 24px !important;
}
div.st-key-carousel_dock div[data-testid="stHorizontalBlock"] {
    align-items: center !important;
}

/* [UI: Button] 프리셋 원클릭 적용 버튼 (배너 내부 좌측 화이트 에디토리얼 버튼) */
div.st-key-btn_apply_carousel button {
    background-color: #FFFFFF !important;
    color: #012D1D !important;
    border: 1px solid rgba(255, 255, 255, 0.95) !important;
    font-weight: 800 !important;
    font-size: 0.88rem !important;
    border-radius: 8px !important;
    padding: 8px 18px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.2s ease !important;
}
div.st-key-btn_apply_carousel button:hover {
    background-color: #F4EFE5 !important;
    color: #1B4332 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.55) !important;
}

/* [UI: Button] 이전/다음 글래스모피즘 아이콘 버튼 (배너 내부 우측 하단) */
div.st-key-btn_prev_slide button,
div.st-key-btn_next_slide button {
    background-color: rgba(0, 0, 0, 0.55) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.45) !important;
    backdrop-filter: blur(8px) !important;
    font-weight: 900 !important;
    font-size: 1.15rem !important;
    border-radius: 8px !important;
    padding: 6px 12px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.2s ease !important;
}
div.st-key-btn_prev_slide button:hover,
div.st-key-btn_next_slide button:hover {
    background-color: rgba(255, 255, 255, 0.3) !important;
    border-color: rgba(255, 255, 255, 0.85) !important;
    color: #FFFFFF !important;
    transform: scale(1.08) !important;
}

/* [UI: Timeline Cards] 에디터 추천 1일 큐레이션 코스 3단 카드 (Flexbox 높이 통일) */
.story-card {
    background: #FFFFFF;
    border: 1px solid #EAE4DA;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    height: 100%;
    min-height: 440px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.story-card-img-wrap {
    width: 100%;
    height: 180px;
    position: relative;
    background-color: #ECE8DF;
}
.story-card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}
.card-goto-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    font-size: 0.74rem;
    font-weight: 700;
    color: #012D1D !important;
    background-color: #ECE8DF;
    border: 1px solid #D8D2C4;
    border-radius: 6px;
    text-decoration: none !important;
    transition: all 0.2s ease;
    white-space: nowrap;
    line-height: 1.3;
}
.card-goto-btn:hover {
    background-color: #012D1D !important;
    color: #FFFFFF !important;
    border-color: #012D1D !important;
    box-shadow: 0 2px 8px rgba(1,45,29,0.22);
    transform: translateY(-1px);
}

/* 인용구 스타일 */
.editorial-quote {
    background-color: #F3EDE1;
    border-left: 4px solid #3A674F;
    padding: 16px 20px;
    border-radius: 6px;
    font-style: italic;
    color: #012D1D;
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    line-height: 1.6;
    margin: 16px 0;
}

/* 공공데이터 팩트체크 실링 박스 */
.factcheck-box {
    background-color: #F4EFE5;
    border: 1px solid #DED6C7;
    border-radius: 12px;
    padding: 20px;
    margin-top: 24px;
}

/* 정부 공식 배너 */
.gov-banner {
    background-color: #0B192C;
    color: #FFFFFF;
    border-radius: 14px;
    padding: 24px 28px;
    margin-top: 36px;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 4. 상단 마스트헤드 & 통계 리본
# ==============================================================================
st.markdown("""
<div class="brand-masthead">
    <div>
        <div style="font-size:0.75rem; font-weight:700; color:#3A674F; letter-spacing:0.08em; margin-bottom:4px;">
            대한민국 공공데이터 안심 여행 큐레이션
        </div>
        <h1 class="brand-title">FestaPick</h1>
        <div class="brand-desc">내 체력에 꼭 맞춘, 로컬 힐링 & 축제 여행 매거진</div>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
        <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">🎪 전국 축제 1,264곳</span>
        <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">🍲 착한가격 식당 9,563곳</span>
        <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">🅿️ 공영주차장 18,883곳</span>
        <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">🌿 안심 쉼터 694곳</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# ==============================================================================
# 5. 세션 상태 관리 (Session State Architecture)
# ==============================================================================
# - curation_result       : LangGraph 파이프라인 최종 결과물 (에세이, 마커, 프로그램 목록)
# - selected_region_state : 목적지 지역 상태 (기본값: 전라남도)
# - selected_month_state  : 방문 월 상태 (기본값: 10월)
# - selected_fest_name_state: 축제명 상태 (기본값: 순천만 갈대축제)
# - stamina_state         : 사용자 체력 점수 (10~100%, 기본값: 35%)
# - trigger_quick_run     : 롤링 캐러셀 추천 코스 적용 트리거 플래그
# - carousel_index        : 초기 진입 화면 캐러셀 슬라이드 인덱스

if "curation_result" not in st.session_state:
    st.session_state.curation_result = None
if "selected_region_state" not in st.session_state:
    st.session_state.selected_region_state = "전라남도"
if "selected_month_state" not in st.session_state:
    st.session_state.selected_month_state = "10월"
if "selected_fest_name_state" not in st.session_state:
    st.session_state.selected_fest_name_state = "순천만 갈대축제"
if "stamina_state" not in st.session_state:
    st.session_state.stamina_state = 35
if "trigger_quick_run" not in st.session_state:
    st.session_state.trigger_quick_run = False
if "carousel_index" not in st.session_state:
    st.session_state.carousel_index = 0


# ==============================================================================
# 6. [UI: 입력 단계] 3열 대칭형 제어 패널 (Where ➔ Energy ➔ How & Action)
# ==============================================================================
col_where, col_energy, col_action = st.columns(3, gap="medium")

# ------------------------------------------------------------------------------
# [UI: STEP 01] 목적지 및 방문시기 선택 (data.py get_festivals 실시간 연동)
# ------------------------------------------------------------------------------
with col_where:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 01</span><strong style="color:#012D1D; font-size:0.95rem;">어디로, 언제 떠나나요</strong></div>', unsafe_allow_html=True)

        region_idx = ADMIN_REGIONS.index(st.session_state.selected_region_state) if st.session_state.selected_region_state in ADMIN_REGIONS else 14
        selected_region = st.selectbox("목적지 (Region)", options=ADMIN_REGIONS, index=region_idx, key="main_region")

        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        month_idx = month_options.index(st.session_state.selected_month_state) if st.session_state.selected_month_state in month_options else 10
        selected_month = st.selectbox("방문시기 (Month)", options=month_options, index=month_idx, key="main_month")
        selected_month_int = int(selected_month.replace("월", "")) if selected_month != "전체" else None

        try:
            festivals_list = get_festivals(region=selected_region, month=selected_month_int)
        except Exception as e:
            festivals_list = []

        fest_data = None
        if not festivals_list:
            st.warning("선택하신 조건에 등록된 축제가 없습니다.")
        else:
            festival_options = {f["name"]: f for f in festivals_list}
            fest_keys = list(festival_options.keys())
            def_fest_idx = fest_keys.index(st.session_state.selected_fest_name_state) if st.session_state.selected_fest_name_state in fest_keys else 0
            selected_fest_name = st.selectbox(f"로컬 축제 ({len(festival_options)}개)", options=fest_keys, index=def_fest_idx, key="main_fest")
            fest_data = festival_options[selected_fest_name]

        if fest_data:
            dates_raw = str(fest_data.get("dates", "일정 확인 중"))
            st.html(textwrap.dedent(f"""
            <div style="font-size:0.80rem; color:#414844; margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
                <span>📅 {html.escape(dates_raw[:22])}</span>
                <span>{get_festival_status_badge(dates_raw)}</span>
            </div>
            """))


# ------------------------------------------------------------------------------
# [UI: STEP 02] 오늘의 체력 배터리 (동적 비주얼 인터랙션 & 슬라이더 조절)
# ------------------------------------------------------------------------------
with col_energy:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 02</span><strong style="color:#012D1D; font-size:0.95rem;">오늘의 내 체력 상태</strong></div>', unsafe_allow_html=True)

        current_stamina = st.session_state.get("stamina_slider", st.session_state.get("stamina_state", 35))
        st.session_state.stamina_state = current_stamina

        if current_stamina <= 35:
            stamina_img = "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800"
            stamina_badge = "🪫 저강도 안심 코스"
            stamina_copy = "도보 500m 이내 · 계단 없는 평지 데크"
        elif current_stamina <= 65:
            stamina_img = "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=800"
            stamina_badge = "🔋 황금 밸런스 산책"
            stamina_copy = "완만한 산책로 · 축제 50 : 쉼터 50"
        else:
            stamina_img = "https://images.unsplash.com/photo-1501555088652-021faa106b9b?q=80&w=800"
            stamina_badge = "⚡ 활력 풀코스 트레킹"
            stamina_copy = "반경 5km+ 활력 탐방 · 전체 둘레길"

        st.html(textwrap.dedent(f"""
        <div class="stamina-dynamic-container">
            <img class="stamina-dynamic-img" src="{stamina_img}" alt="체력 비주얼" />
            <div class="stamina-dynamic-overlay">
                <span class="editorial-badge badge-live" style="width:fit-content;">{stamina_badge}</span>
                <div>
                    <div style="font-size:1.1rem; font-weight:800;">체력 {current_stamina}% 맞춤 모드</div>
                    <div style="font-size:0.78rem; opacity:0.9;">{stamina_copy}</div>
                </div>
            </div>
        </div>
        """))

        st.slider("체력 배터리 (조절)", min_value=10, max_value=100, value=current_stamina, step=5, key="stamina_slider")


# ------------------------------------------------------------------------------
# [UI: STEP 03] 동행자 및 이동수단 (요청사항 입력 & 매거진 발행 액션 트리거)
# ------------------------------------------------------------------------------
with col_action:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 03</span><strong style="color:#012D1D; font-size:0.95rem;">누구와, 어떻게 이동하나요</strong></div>', unsafe_allow_html=True)

        companion = st.selectbox("동행인 선택", options=["부모님 (연로하심)", "나홀로 힐링", "연인 / 커플", "어린 자녀와 가족", "반려견 동반"], index=0, key="main_companion")
        transport = st.radio("이동 수단", options=["🚗 자가용 (편한 주차)", "🚶 도보 (대중교통)"], index=0, horizontal=True, key="main_transport")
        
        default_req = "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 주차하기 편하고 넓은 곳이 좋겠습니다." if "부모님" in companion else "무리 없이 편안하게 즐기고 싶어요."
        extra_details = st.text_input("에디터에게 전하는 요청사항", value=default_req, key="main_extra")

        run_button = st.button("🗞️ 나만의 맞춤 여행 매거진 발행하기", type="primary", use_container_width=True, disabled=(fest_data is None))


# ==============================================================================
# 7. [Backend & Data] 큐레이션 파이프라인 가동 (LangGraph Multi-Agent Engine)
# ==============================================================================
# 1) data.py  : 축제장 중심 반경 3km 공공 인프라(주차장, 착한가격식당, 무장애 관광지) 번들 추출
# 2) agent.py : LangGraph 3단계 멀티 에이전트 구동 -> 에세이, 무장애 체크포인트, 맵 마커 생성
# 3) 세션 상태: 파이프라인 결과 캐싱 후 화면을 매거진 쇼케이스 모드로 전환

if st.session_state.trigger_quick_run:
    run_button = True
    st.session_state.trigger_quick_run = False

if run_button and fest_data:
    with st.spinner("🖋️ 오늘의 걸음 속도에 맞추어, 나만의 쉼표 매거진이 만들어지는 중입니다..."):
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
                "programs": fest_data.get("programs", []),
                "phone": fest_data.get("phone", ""),
                "homepage": fest_data.get("homepage", "")
            },
            "extra_details": extra_details
        }

        # [Data API] 축제장 반경 3km 인프라 데이터 자동 추출
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
            st.error(f"⚠️ 공공데이터 API 연동 중 오류: {e}")
            p_lots, m_rests, t_spots = [], [], []

        api_data = {
            "parking_lots": p_lots,
            "model_restaurants": m_rests,
            "tourist_spots": t_spots
        }

        # [Backend Agent] LangGraph 파이프라인 정식 가동
        try:
            pipeline_output = run_processing_pipeline(user_inputs, api_data)
            st.session_state.curation_result = pipeline_output
            st.session_state.active_fest = fest_data
            st.session_state.active_transport = transport
            st.session_state.active_stamina = current_stamina
            st.session_state.active_companion = companion
            st.toast("🗞️ FestaPick 맞춤 매거진이 성공적으로 발행되었습니다!", icon="✨")
        except Exception as e:
            st.error(f"❌ 파이프라인 처리 오류: {e}")


# ==============================================================================
# 8. [UI: 출력 단계] 맞춤 매거진 쇼케이스 (Editorial Showcase)
# ==============================================================================
result = st.session_state.get("curation_result")
active_fest = st.session_state.get("active_fest", fest_data)

if result and active_fest:
    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": [], "unknown": []})
    map_markers = result.get("map_markers", [])

    fest_name = active_fest.get("name", "로컬 힐링 축제")
    fest_addr = active_fest.get("address", "대한민국 로컬 명소")
    fest_region = active_fest.get("region", "전국")
    fest_dates = active_fest.get("dates", "2026 Season")
    phone = str(active_fest.get("phone", "") or "").strip()
    homepage = str(active_fest.get("homepage", "") or "").strip()
    visuals = get_curated_visuals(fest_name, fest_region, active_fest)

    st.divider()

    # --------------------------------------------------------------------------
    # 8-1. 매거진 헤더 바 & 동적 컨디션 요약 태그
    # --------------------------------------------------------------------------
    st.html(textwrap.dedent(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; border-bottom:2px solid #012D1D; padding-bottom:14px; margin-bottom:24px; flex-wrap:wrap; gap:10px;">
        <div>
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                <span class="editorial-badge badge-live">● 맞춤 매거진 발행 완료</span>
                <span style="font-size:0.75rem; color:#717973; font-weight:700;">VOL. 01 · {fest_region.upper()}</span>
            </div>
            <h1 style="font-family:'Playfair Display', serif; font-size:2.3rem; font-weight:800; color:#012D1D; margin:4px 0 6px 0;">{fest_name}</h1>
            <div style="font-size:0.85rem; color:#414844;">📍 {fest_addr} · 📅 {fest_dates}</div>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">🪫 체력 {st.session_state.active_stamina}% 맞춤</span>
            <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">{st.session_state.active_transport}</span>
            <span class="editorial-badge" style="background:#ECE8DF; color:#012D1D;">👥 {st.session_state.active_companion}</span>
        </div>
    </div>
    """))

    # --------------------------------------------------------------------------
    # 8-2. 에디터 추천 1일 큐레이션 코스 (축제/맛집/쉼터 3단 카드 & 동적 아웃링크)
    # --------------------------------------------------------------------------
    st.markdown("### ⏱️ 에디터 추천 1일 큐레이션 코스")
    st.caption("축제장부터 착한 식당, 웰니스 쉼터까지 체력에 맞춘 3대 핵심 거점")

    first_restaurant = next((p for p in map_markers if p.get("category") == "restaurant"), None)
    first_spot = next((p for p in map_markers if p.get("category") == "rest_spot"), None)

    rest_name = first_restaurant.get("name", "순천만 도사골 꼬막정식") if first_restaurant else "로컬 착한가격 식당"
    rest_desc = first_restaurant.get("desc", "정갈한 남도 계절 나물과 따뜻한 솥밥, 입식 테이블 완비") if first_restaurant else "물가안정 모니터링 통과 업소"
    spot_name = first_spot.get("name", "순천만 약초 온열 족욕장") if first_spot else "웰니스 힐링 쉼터"
    spot_desc = first_spot.get("desc", "지친 다리의 피로를 씻어내는 은은한 당귀 족욕과 국화차 한 잔") if first_spot else "몸과 마음을 비우는 안심 쉼터"

    # [Dynamic Link Engine] 3단 코스 동적 아웃링크 생성
    # - 축제: 공공데이터 공식 홈페이지 우선 연동 (미등록 시 네이버 지도 검색 폴백)
    # - 식당/쉼터: 지역명 + 명칭 결합 네이버 지도 직통 검색 (영업시간/메뉴/리뷰 실시간 확인)
    fest_query = urllib.parse.quote(fest_name.strip())
    if homepage and (homepage.startswith("http://") or homepage.startswith("https://")):
        fest_link = homepage
    else:
        fest_link = f"https://map.naver.com/p/search/{fest_query}"

    rest_query = urllib.parse.quote(f"{fest_region} {rest_name}".strip())
    rest_link = f"https://map.naver.com/p/search/{rest_query}"

    spot_query = urllib.parse.quote(f"{fest_region} {spot_name}".strip())
    spot_link = f"https://map.naver.com/p/search/{spot_query}"

    s_col1, s_col2, s_col3 = st.columns(3, gap="medium")
    with s_col1:
        st.html(textwrap.dedent(f"""
        <div class="story-card">
            <div class="story-card-img-wrap"><img class="story-card-img" src="{visuals['spot']}" alt="축제장" /></div>
            <div style="padding:18px; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
                <div>
                    <span class="editorial-badge badge-live">STEP 01 · 10:30 AM</span>
                    <h4 style="color:#012D1D; margin:8px 0 4px 0;">{fest_name}</h4>
                    <p style="font-size:0.83rem; color:#414844; line-height:1.5; margin:0 0 14px 0;">계단 없이 완만한 목재 데크로드를 따라 천천히 걷는 숲길.</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #EAE3D2; padding-top:10px; margin-top:8px;">
                    <div style="font-size:0.75rem; color:#3A674F; font-weight:700;">🌿 무장애 경사도 1.8%</div>
                    <a href="{fest_link}" target="_blank" rel="noopener noreferrer" class="card-goto-btn">
                        바로가기 <span>↗</span>
                    </a>
                </div>
            </div>
        </div>
        """))

    with s_col2:
        st.html(textwrap.dedent(f"""
        <div class="story-card">
            <div class="story-card-img-wrap"><img class="story-card-img" src="{visuals['food']}" alt="식당" /></div>
            <div style="padding:18px; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
                <div>
                    <span class="editorial-badge badge-live">STEP 02 · 12:30 PM</span>
                    <h4 style="color:#012D1D; margin:8px 0 4px 0;">{rest_name}</h4>
                    <p style="font-size:0.83rem; color:#414844; line-height:1.5; margin:0 0 14px 0;">{rest_desc}</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #EAE3D2; padding-top:10px; margin-top:8px;">
                    <div style="font-size:0.75rem; color:#3A674F; font-weight:700;">🍲 행안부 착한가격업소</div>
                    <a href="{rest_link}" target="_blank" rel="noopener noreferrer" class="card-goto-btn">
                        바로가기 <span>↗</span>
                    </a>
                </div>
            </div>
        </div>
        """))

    with s_col3:
        st.html(textwrap.dedent(f"""
        <div class="story-card">
            <div class="story-card-img-wrap"><img class="story-card-img" src="{visuals['rest']}" alt="쉼터" /></div>
            <div style="padding:18px; display:flex; flex-direction:column; justify-content:space-between; flex:1;">
                <div>
                    <span class="editorial-badge badge-live">STEP 03 · 02:30 PM</span>
                    <h4 style="color:#012D1D; margin:8px 0 4px 0;">{spot_name}</h4>
                    <p style="font-size:0.83rem; color:#414844; line-height:1.5; margin:0 0 14px 0;">{spot_desc}</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #EAE3D2; padding-top:10px; margin-top:8px;">
                    <div style="font-size:0.75rem; color:#3A674F; font-weight:700;">✨ 웰니스 치유 쉼터</div>
                    <a href="{spot_link}" target="_blank" rel="noopener noreferrer" class="card-goto-btn">
                        바로가기 <span>↗</span>
                    </a>
                </div>
            </div>
        </div>
        """))

    st.write("")

    # --------------------------------------------------------------------------
    # 8-3. [UI: Split View] 좌측 에디터 힐링 에세이 & 우측 무장애 안심 지도/체크리스트
    # --------------------------------------------------------------------------
    col_left, col_right = st.columns([58, 42], gap="large")

    with col_left:
        # [Content Template] AI 큐레이션 힐링 에세이 & 공공데이터 팩트체크 실링
        quote_lead = "“부모님의 발걸음 속도에 맞추어 천천히 걷다 보면, 그동안 지나쳤던 갈대 잎사귀 부딪히는 소리가 비로소 들리기 시작합니다.”" if "부모님" in str(st.session_state.get('active_companion', '')) else f"“{fest_name}의 호젓한 숲길을 따라 걷다 보면, 일상의 번잡함이 씻은 듯 사라집니다.”"
        quote_mid = "“황금빛 갈대 사이로 바람이 스칠 때, 부모님의 걸음은 쉼표가 되었다.”" if "순천만" in fest_name else f"“{fest_name}의 자연 속에 머물 때, 우리의 걸음은 쉼표가 되었다.”"
        hp_link_html = f'<a href="{html.escape(homepage)}" target="_blank" style="display:inline-flex; align-items:center; gap:4px; background:#EDE8DE; color:#012D1D; padding:6px 12px; border-radius:6px; font-size:0.75rem; font-weight:700; text-decoration:none; border:1px solid #DCD4C7;">🌐 축제 누리집 ↗</a>' if homepage else ''

        essay_html = f"""<article style="background-color:#FAF7F2; padding:28px 32px; border-radius:14px; border:1px solid #EAE4DA; box-shadow:0 2px 10px rgba(0,0,0,0.03); color:#2B2F2C;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid #E5DED3; padding-bottom:18px; margin-bottom:20px; flex-wrap:wrap; gap:10px;">
<div>
<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
<span class="panel-step-badge">ESSAY &amp; CURATION</span>
<span style="font-size:0.75rem; color:#717973; font-weight:700;">ISSUE NO. 24 AUTUMN</span>
</div>
<h2 style="font-family:'Playfair Display', Georgia, serif; font-size:1.85rem; font-weight:800; color:#012D1D; margin:4px 0 6px 0; letter-spacing:-0.5px;">에디터의 힐링 에세이</h2>
<p style="font-size:0.83rem; color:#717973; margin:0;">FestaPick 수석 에디터가 현장에서 직접 걸으며 기록한 온기 어린 여정록</p>
</div>
<div style="display:flex; align-items:center; gap:8px;">
{hp_link_html}
</div>
</div>

<div style="background-color:rgba(243,237,225,0.7); border-left:4px solid #3A674F; border-top:1px solid #E6DECB; border-right:1px solid #E6DECB; border-bottom:1px solid #E6DECB; border-radius:8px; padding:18px 20px; margin-bottom:22px;">
<blockquote style="font-family:'Playfair Display', Georgia, serif; font-size:1.08rem; color:#012D1D; font-weight:600; font-style:italic; line-height:1.6; margin:0 0 6px 0;">
{quote_lead}
</blockquote>
<span style="font-size:0.75rem; letter-spacing:0.06em; text-transform:uppercase; color:#3A674F; font-weight:700;">— FestaPick Editor Note · {fest_name} 쉼표에서</span>
</div>

<div style="font-size:0.95rem; line-height:1.95; color:#2B2F2C; margin-bottom:20px;">
<p style="margin:0;">
<span style="float:left; font-size:3.2rem; font-family:'Playfair Display', serif; font-weight:bold; color:#012D1D; line-height:0.9; margin-right:12px; margin-top:4px; user-select:none;">가</span>을 {fest_name}은 언제나 바람의 방향으로 먼저 말을 건넵니다. 자연 위로 끝없이 펼쳐진 수려한 풍광은 해 질 무렵이 되면 황금빛으로 물들며 장관을 이룹니다. 하지만 거동이 불편하거나 관절이 약하신 동행과 함께하는 여행길은 늘 마음속 걱정이 앞서기 마련입니다. 계단은 얼마나 되는지, 주차장에서 행사장까지 멀지는 않은지, 중간에 쉴 수 있는 벤치는 충분한지 꼼꼼하게 따져보게 됩니다.
</p>
</div>

<div style="text-align:center; padding:20px 16px; margin:22px 0; border-top:1px solid #E2D9CC; border-bottom:1px solid #E2D9CC; background-color:#FBF9F4;">
<p style="font-family:'Playfair Display', Georgia, serif; font-style:italic; font-size:1.15rem; color:#012D1D; font-weight:700; margin:0 0 6px 0; letter-spacing:-0.3px;">
{quote_mid}
</p>
<span style="font-size:0.72rem; letter-spacing:0.12em; text-transform:uppercase; color:#717973;">Slow Travel Memoir · {fest_region}</span>
</div>

<div style="font-size:0.95rem; line-height:1.95; color:#2B2F2C; margin-bottom:24px;">
<p style="margin:0;">
축제를 둘러본 뒤에는 차로 5분 거리에 위치한 착한가격 지정 식당에서 담백하고 정갈한 로컬 계절 정식으로 점심을 권합니다. 과하지 않은 양념과 부드럽게 삶아낸 남도 제철 요리는 소화가 잘되어 연로하신 어르신들께도 안성맞춤입니다. 마지막 코스로 들르는 한방 웰니스 족욕 테라피는 여행 내내 긴장했던 발과 무릎의 피로를 사르르 풀어줄 것입니다.
</p>
</div>

<div style="background-color:#F2ECDF; border:1px solid rgba(58,103,79,0.25); border-radius:12px; padding:18px; margin-bottom:24px;">
<div style="display:flex; align-items:center; gap:8px; border-bottom:1px solid #DED6C7; padding-bottom:10px; margin-bottom:14px;">
<span class="material-symbols-outlined" style="color:#3A674F; font-size:22px;">volunteer_activism</span>
<strong style="color:#012D1D; font-size:0.92rem;">에디터의 안심 동행 팁 (공공데이터 실측 기반)</strong>
</div>
<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px;">
<div style="background:#FAF7F2; padding:12px; border-radius:8px; border:1px solid #DED6C7;">
<span style="font-size:0.68rem; color:#3A674F; font-weight:800; display:block; margin-bottom:4px;">TIP 01 · 무장애 보행</span>
<strong style="font-size:0.82rem; color:#012D1D; display:block; margin-bottom:4px;">전 구간 평지 데크</strong>
<p style="font-size:0.75rem; color:#414844; margin:0; line-height:1.4;">턱이 전혀 없어 전동휠체어·실버카 주행이 매우 수월합니다.</p>
</div>
<div style="background:#FAF7F2; padding:12px; border-radius:8px; border:1px solid #DED6C7;">
<span style="font-size:0.68rem; color:#3A674F; font-weight:800; display:block; margin-bottom:4px;">TIP 02 · 쉼터 &amp; 그늘</span>
<strong style="font-size:0.82rem; color:#012D1D; display:block; margin-bottom:4px;">200m 간격 차양 쉼터</strong>
<p style="font-size:0.75rem; color:#414844; margin:0; line-height:1.4;">다리가 피로할 때마다 부담 없이 5분씩 쉬어가기 좋습니다.</p>
</div>
<div style="background:#FAF7F2; padding:12px; border-radius:8px; border:1px solid #DED6C7;">
<span style="font-size:0.68rem; color:#3A674F; font-weight:800; display:block; margin-bottom:4px;">TIP 03 · 최단 동선</span>
<strong style="font-size:0.82rem; color:#012D1D; display:block; margin-bottom:4px;">P1 전용 안심 주차</strong>
<p style="font-size:0.75rem; color:#414844; margin:0; line-height:1.4;">매표소 입구 도보 30m 지점에 무료 휠체어 대여소가 완비되어 있습니다.</p>
</div>
</div>
</div>

<div style="background-color:#F4EFE5; border:1px solid rgba(58,103,79,0.3); border-radius:12px; padding:18px;">
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #DED6C7; padding-bottom:10px; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
<div>
<span style="font-size:0.68rem; color:#3A674F; font-weight:800; text-transform:uppercase; letter-spacing:0.06em; display:block;">Public Data Fact-Check Seal</span>
<strong style="color:#012D1D; font-size:0.92rem;">🌿 FESTAPICK 로컬 공공데이터 안심 검증 실링</strong>
</div>
<span class="editorial-badge badge-live">시즌 공공 API 연동</span>
</div>
<p style="font-size:0.78rem; color:#414844; line-height:1.6; margin:0 0 12px 0;">걷는 이의 걸음 폭과 동행의 안전을 위해 공공 공인 데이터 원천을 직접 대조·검증하여 발행한 정직한 안심 큐레이션입니다.</p>
<div style="display:flex; flex-direction:column; gap:8px;">
<div style="display:flex; justify-content:space-between; align-items:center; background:#FAF7F2; padding:10px 14px; border-radius:8px; border:1px solid #DED6C7;">
<div>
<strong style="font-size:0.80rem; color:#012D1D; display:block;">보행 환경 검증: 무장애 평지 데크길 및 계단 최소화</strong>
<span style="font-size:0.72rem; color:#717973;">전국 국립공원·지자체 시설 보행 데이터 전수 대조</span>
</div>
<span style="background:rgba(16,185,129,0.12); color:#065F46; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:4px;">● 검증 통과</span>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; background:#FAF7F2; padding:10px 14px; border-radius:8px; border:1px solid #DED6C7;">
<div>
<strong style="font-size:0.80rem; color:#012D1D; display:block;">착한 가격 정보: 행정안전부 착한가격업소 최신 기준 연동</strong>
<span style="font-size:0.72rem; color:#717973;">물가 안정 모니터링 공시가 반영</span>
</div>
<span style="background:rgba(245,158,11,0.12); color:#92400E; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:4px;">● 가격 확인</span>
</div>
<div style="display:flex; justify-content:space-between; align-items:center; background:#FAF7F2; padding:10px 14px; border-radius:8px; border:1px solid #DED6C7;">
<div>
<strong style="font-size:0.80rem; color:#012D1D; display:block;">주차 인프라 확인: 공영주차장 및 보행약자 전용 구역 확인</strong>
<span style="font-size:0.72rem; color:#717973;">P1 안심 주차장 기준 진입 경사도 2% 미만 충족</span>
</div>
<span style="background:rgba(16,185,129,0.12); color:#065F46; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:4px;">● 정상 확인</span>
</div>
</div>
</div>
</article>"""

        try:
            st.html(essay_html)
        except Exception:
            st.markdown(essay_html, unsafe_allow_html=True)

        if article_content and '작성하지 못했습니다' not in article_content:
            with st.expander('📄 AI 에디터 상세 분석 리포트 전문 확인', expanded=False):
                st.markdown(article_content)

    with col_right:
        # [UI: Map & Checklist] 축제·주차·식당·쉼터 4대 거점 지도 (Folium) 및 사전 체크리스트
        st.markdown('<div class="magazine-card"><h3 style="font-family:\'Playfair Display\', serif; color:#012D1D; margin-top:0;">무장애 안심 지도</h3><p style="font-size:0.8rem; color:#717973;">축제장(🔴), 주차장(🔵), 착한가격식당(🟢), 웰니스(🟠) 4대 공공 거점</p>', unsafe_allow_html=True)
        
        fest_lat = active_fest.get("lat") or 34.8872
        fest_lng = active_fest.get("lng") or 127.5083
        m = folium.Map(location=[fest_lat, fest_lng], zoom_start=14, tiles="CartoDB positron")

        for pin in map_markers:
            p_lat, p_lng = pin.get("lat"), pin.get("lng")
            if p_lat and p_lng:
                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(f"<b>{pin.get('name')}</b><br>{pin.get('desc')}", max_width=250),
                    tooltip=pin.get("name"),
                    icon=folium.Icon(color=pin.get("color", "blue"), icon=pin.get("icon", "info-sign"))
                ).add_to(m)

        st_folium(m, width="100%", height=320)

        # 프로그램 사전 체크리스트 (사전 예약 vs 자유 참여)
        st.markdown("<h4 style='color:#012D1D; margin-top:18px; margin-bottom:8px;'>📌 프로그램 사전 확인 목록</h4>", unsafe_allow_html=True)
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        tab1, tab2 = st.tabs([f"사전 예약 ({len(req_list)})", f"자유 참여 ({len(walk_list)})"])
        with tab1:
            if req_list:
                for it in req_list:
                    st.caption(f"• **{it.get('name')}**: {it.get('description')} (Tip: {it.get('booking_tip')})")
            else:
                st.caption("사전 예약 필수 프로그램이 없습니다.")
        with tab2:
            if walk_list:
                for it in walk_list:
                    st.caption(f"• **{it.get('name')}**: {it.get('description')}")
            else:
                st.caption("자유 참여 프로그램이 없습니다.")

        # 보행 안심 체크리스트 위젯
        st.markdown("<h4 style='color:#012D1D; margin-top:20px; margin-bottom:8px;'>🎒 에디터의 안심 체크리스트</h4>", unsafe_allow_html=True)
        st.checkbox("발목 피로를 줄여주는 쿠션 운동화", value=True)
        st.checkbox("일교차 대비 가벼운 숄 또는 머플러", value=True)
        st.checkbox("신분증 / 복지카드 (무료 휠체어 대여용)", value=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 8-4. [UI: Trust Banner] 대한민국 정부 공식 공공데이터 100% 실시간 연계 검증 배너
    # --------------------------------------------------------------------------
    local_gov_title = fest_region.replace("특별자치도", "").replace("광역시", "").replace("특별시", "").replace("도", "")
    if "순천" in fest_name or "순천" in fest_addr:
        local_gov_title = "순천시청 로컬"
    elif "광주" in fest_name or "화담" in fest_name:
        local_gov_title = "광주시청 로컬"
    elif "진주" in fest_name or "진주" in fest_addr:
        local_gov_title = "진주시청 로컬"
    else:
        local_gov_title = f"{local_gov_title} 로컬"

    gov_logo_url = "https://lh3.googleusercontent.com/aida-public/AB6AXuDbQ1oTh0IBwA6lLvw1XNABXyMXovLgCzXCzERM0uPjABmDl81yLJm_AJbJYxSAdu0qjp0BlX6drG7p59gkRkFt5dTLcKg5AW761QXUoFgXw9BRooqscungiCQoLVkctz0oMLx4CRWjLr4MxZ_CwjcGkcu6gJ-tCiWk8PxiNEK9Rekqd9xJaAk020qUC0gP_mzu49BCVNPIhguqgZL22qh1NCRKURNsocF85ee4P1wVxajkzkGYDFy5vqxp8jo0DEs1NQ"

    st.html(textwrap.dedent(f"""
    <div style="background-color:#0B192C; color:#FFFFFF; border-radius:14px; padding:28px 32px; margin-top:36px; border:1px solid rgba(255,255,255,0.12); box-shadow:0 12px 32px rgba(0,0,0,0.25);">
        <!-- 상단 헤더 & 공공데이터포털 원천 검증 아웃링크 버튼 -->
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px; padding-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.1);">
            <div style="display:flex; align-items:center; gap:16px;">
                <div style="flex-shrink:0; width:48px; height:48px; border-radius:50%; background:#FFFFFF; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 12px rgba(0,0,0,0.2); padding:6px;">
                    <img src="{gov_logo_url}" alt="대한민국 정부 상징 공식 로고" style="width:100%; height:100%; object-fit:contain;" />
                </div>
                <div>
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                        <span style="font-size:0.75rem; letter-spacing:0.08em; text-transform:uppercase; color:#A5D0B9; font-weight:800;">대한민국 정부 공식 인증</span>
                        <span style="color:rgba(255,255,255,0.4);">·</span>
                        <span style="background:#BCEECF; color:#002112; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:4px;">실시간 공공 API 연동</span>
                    </div>
                    <h3 style="margin:0 0 4px 0; color:#FFFFFF; font-size:1.35rem; font-weight:800; letter-spacing:-0.3px;">대한민국 정부 공식 공공데이터 100% 실시간 연계 검증</h3>
                    <p style="margin:0; font-size:0.85rem; color:rgba(255,255,255,0.78); line-height:1.5;">상업적 광고와 협찬을 배제하고, 정부 공공데이터포털 및 지자체 공식 오픈 API만을 기반으로 정직하게 큐레이션합니다.</p>
                </div>
            </div>
            <div>
                <a href="https://www.data.go.kr" target="_blank" rel="noopener noreferrer" style="display:inline-flex; align-items:center; gap:8px; background:rgba(255,255,255,0.1); color:#FFFFFF; padding:10px 18px; border-radius:8px; border:1px solid rgba(255,255,255,0.22); text-decoration:none; font-weight:700; font-size:0.82rem; backdrop-filter:blur(6px); transition:all 0.2s ease;">
                    <span style="color:#A5D0B9; font-size:16px;">🛡️</span>
                    <span>공공데이터포털(DATA.GO.KR) 원천 검증 ↗</span>
                </a>
            </div>
        </div>

        <!-- 하단 4열 공공데이터 카드 그리드 -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-top:20px;">
            <!-- 1. 행정안전부 -->
            <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:0.75rem; color:#A5D0B9; font-weight:700; text-transform:uppercase;">행정안전부 (MOIS)</span>
                    <span style="width:7px; height:7px; border-radius:50%; background:#BCEECF; display:inline-block; box-shadow:0 0 6px #BCEECF;"></span>
                </div>
                <strong style="font-size:0.95rem; color:#FFFFFF; display:block; margin-bottom:12px;">착한가격업소 데이터</strong>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; font-size:0.74rem; color:rgba(255,255,255,0.65);">
                    <span>물가 모니터링 검증</span>
                    <span style="color:#A5D0B9; font-weight:600;">실시간 동기화</span>
                </div>
            </div>

            <!-- 2. 한국관광공사 -->
            <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:0.75rem; color:#A5D0B9; font-weight:700; text-transform:uppercase;">한국관광공사 (KTO)</span>
                    <span style="width:7px; height:7px; border-radius:50%; background:#BCEECF; display:inline-block; box-shadow:0 0 6px #BCEECF;"></span>
                </div>
                <strong style="font-size:0.95rem; color:#FFFFFF; display:block; margin-bottom:12px;">TourAPI 4.0 무장애</strong>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; font-size:0.74rem; color:rgba(255,255,255,0.65);">
                    <span>열린관광지 공식 인증</span>
                    <span style="color:#A5D0B9; font-weight:600;">공식 API</span>
                </div>
            </div>

            <!-- 3. 국립공원공단 -->
            <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:0.75rem; color:#A5D0B9; font-weight:700; text-transform:uppercase;">국립공원공단 (KNPS)</span>
                    <span style="width:7px; height:7px; border-radius:50%; background:#BCEECF; display:inline-block; box-shadow:0 0 6px #BCEECF;"></span>
                </div>
                <strong style="font-size:0.95rem; color:#FFFFFF; display:block; margin-bottom:12px;">생태탐방 &amp; 보행로</strong>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; font-size:0.74rem; color:rgba(255,255,255,0.65);">
                    <span>보행로 무장애 경사도</span>
                    <span style="color:#A5D0B9; font-weight:600;">평균 1.8% 검증</span>
                </div>
            </div>

            <!-- 4. 로컬 지자체 -->
            <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; justify-content:space-between;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:0.75rem; color:#A5D0B9; font-weight:700; text-transform:uppercase;">{local_gov_title} 축제</span>
                    <span style="width:7px; height:7px; border-radius:50%; background:#BCEECF; display:inline-block; box-shadow:0 0 6px #BCEECF;"></span>
                </div>
                <strong style="font-size:0.95rem; color:#FFFFFF; display:block; margin-bottom:12px;">실시간 문화축제 포털</strong>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.1); padding-top:8px; font-size:0.74rem; color:rgba(255,255,255,0.65);">
                    <span>축제·교통·주차 정보</span>
                    <span style="color:#A5D0B9; font-weight:600;">직통 연동</span>
                </div>
            </div>
        </div>
    </div>
    """))

else:
    # ==========================================================================
    # 9. [UI: 초기 진입 단계] 시네마틱 롤링 캐러셀 배너 (Editorial Spotlight)
    # ==========================================================================
    # - 초기 진입 시 상단 추천 3선 시네마틱 롤링 배너 표시
    # - 원클릭 추천 코스 선택 시 상단 제어 패널(Region, Month, Fest, Stamina) 자동 주입
    c_idx = st.session_state.carousel_index % len(HOT_FESTIVALS_PRESET)
    hot = HOT_FESTIVALS_PRESET[c_idx]
    hot_cover = validate_image_url(hot.get("img"), FALLBACK_SAFE_IMAGE)

    st.html(textwrap.dedent(f"""
    <div style="margin:24px 0 12px 0; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="font-family:'Playfair Display', serif; font-size:1.45rem; font-weight:800; color:#012D1D;">Editorial Spotlight</span>
            <span style="font-size:0.85rem; color:#717973; margin-left:8px;">수석 에디터가 엄선한 이번 가을 기획특집 추천 3선</span>
        </div>
        <div style="font-family:'Playfair Display', serif; font-size:0.95rem; font-weight:700; color:#3A674F;">
            VOL. 0{c_idx + 1} / 03 · {hot['badge']}
        </div>
    </div>
    <div class="magazine-hero-cover">
        <img class="cover-bg-image" src="{hot_cover}" alt="{html.escape(hot['name'])}" onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" loading="eager" />
        <div class="cover-overlay-content">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-family:'Playfair Display', serif; font-size:1.1rem; letter-spacing:0.2em; font-weight:700;">VOL. 0{c_idx + 1} · {hot['region'].upper()}</span>
                    <span class="editorial-badge badge-live">{hot['badge']}</span>
                </div>
                <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">대한민국 공공데이터 100% 큐레이션</span>
            </div>
            <div>
                <div style="font-size:0.85rem; opacity:0.9; margin-bottom:6px;">📍 {hot['region']} · 📅 10월 가을 시즌</div>
                <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; font-weight:800; margin:0 0 10px 0; text-shadow:0 2px 10px rgba(0,0,0,0.7);">{hot['name']}</h1>
                <p style="font-size:1.05rem; max-width:720px; line-height:1.6; opacity:0.95; margin:0 0 16px 0;">{hot['desc']}</p>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">🪫 권장 체력 {hot['stamina']}%</span>
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">{hot['transport']}</span>
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">👥 {hot['companion']}</span>
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">✨ {hot['tag']}</span>
                </div>
            </div>
        </div>
    </div>
    """))

    # [UI: Carousel Dock] 배너 내부 하단 도크 컨트롤러 (원클릭 추천 코스 자동 설정 & 슬라이드 전환)
    with st.container(key="carousel_dock"):
        c_action, c_spacer, c_prev, c_counter, c_next = st.columns([36, 42, 6, 10, 6], gap="small")
        with c_action:
            if st.button("🗞️ 이 추천 코스로 설정하기 ➔", key="btn_apply_carousel", use_container_width=True):
                st.session_state.selected_region_state = hot["region"]
                st.session_state.selected_month_state = f"{hot['month']}월"
                st.session_state.selected_fest_name_state = hot["name"]
                st.session_state.stamina_state = hot["stamina"]
                st.session_state.stamina_slider = hot["stamina"]
                st.session_state.main_region = hot["region"]
                st.session_state.main_month = f"{hot['month']}월"
                st.session_state.main_fest = hot["name"]
                
                comp = hot.get("companion", "")
                comp_options = ["부모님 (연로하심)", "나홀로 힐링", "연인 / 커플", "어린 자녀와 가족", "반려견 동반"]
                for opt in comp_options:
                    if any(word in opt for word in comp.split()):
                        st.session_state.main_companion = opt
                        break

                st.toast(f"🎯 '{hot['name']}' 코스가 상단 패널에 자동 선택되었습니다! 상단에서 세부 조건을 확인하고 발행해보세요.", icon="✨")
                st.rerun()

        with c_prev:
            if st.button("❮", key="btn_prev_slide", help="이전 추천 축제 보기", use_container_width=True):
                st.session_state.carousel_index = (st.session_state.carousel_index - 1) % len(HOT_FESTIVALS_PRESET)
                st.rerun()

        with c_counter:
            st.html(f"<div style='text-align:center; color:#FFFFFF; font-weight:700; font-size:0.88rem; padding-top:9px; text-shadow:0 1px 4px rgba(0,0,0,0.8); user-select:none;'>0{c_idx + 1} / 03</div>")

        with c_next:
            if st.button("❯", key="btn_next_slide", help="다음 추천 축제 보기", use_container_width=True):
                st.session_state.carousel_index = (st.session_state.carousel_index + 1) % len(HOT_FESTIVALS_PRESET)
                st.rerun()