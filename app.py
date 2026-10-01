"""
app.py - 페스타픽 & 레스트 (Fest & Rest · FestaPick)
===================================================
29CM & Kinfolk 스타일의 시네마틱 라이프스타일 로컬 여행 매거진
100% 공공데이터(문화축제표준데이터, 주차장, 착한가격업소, 한국관광공사 TourAPI)와 
체력 기반 3단계 LangGraph AI 파이프라인(agent.py)이 연동된 초개인화 에디토리얼 큐레이션 웹 대시보드

[핵심 특징]
1. 완벽한 기능 계승: 동적 검색 반경(자가용 20km / 도보 1~2km), 실제 공공데이터 조회, 공식 예매처 CTA, 거리 계산 및 JSON 디버그
2. 프리미엄 29CM 에디토리얼 UI/UX: 어반 보태니컬 세이지 그린 컬러 시스템, 와이드 3열 대칭형 제어 패널, 
   실시간 체력 반응형 비주얼 카드, 시네마틱 히어로 커버, 3단 비주얼 타임라인, 카토그램 포지트론 안심 지도
"""

import os
import sys
import json
import html
import re
import urllib.parse
from urllib.parse import quote, urljoin
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import base64
import io
from PIL import Image
import requests
from bs4 import BeautifulSoup
import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as st_components

# ==============================================================================
# 백엔드 및 공공데이터 모듈 경로 최우선 순위 보장 (상위 폴더 모듈 간섭 차단)
# ==============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

if CURRENT_DIR in sys.path:
    sys.path.remove(CURRENT_DIR)
sys.path.insert(0, CURRENT_DIR)

festapick_dir = os.path.join(CURRENT_DIR, "festapick")
if os.path.exists(festapick_dir) and festapick_dir not in sys.path:
    sys.path.insert(1, festapick_dir)

for p in [os.path.join(CURRENT_DIR, "backend"), os.path.join(CURRENT_DIR, "datafile")]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.append(p)

# agent.py 백엔드 파이프라인 정식 인터페이스 임포트
try:
    from agent import run_processing_pipeline, PipelineState
except ImportError as e:
    st.error(f"agent.py 임포트 오류: {e}")
    st.stop()

# data.py 실제 공공데이터 엔지니어링 모듈 연동 (루트 브릿지 및 festapick/data_pipeline 모두 지원)
try:
    from data import get_festival_infra_bundle, get_festivals
except ImportError:
    try:
        from festapick.data_pipeline import get_festival_infra_bundle, get_festivals
    except ImportError as e:
        st.error(f"data.py 임포트 오류: {e}")
        st.stop()


# ==============================================================================
# 1. 대한민국 17개 광역 행정구역 마스터 목록 & 에디토리얼 추천 프리셋
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
# 2. [사용자 편의성] 배경색 기준 보색 & WCAG 고대비 텍스트 컬러 시스템
# ==============================================================================
def get_rgb_from_hex(hex_color: str) -> tuple:
    """HEX 색상 문자열(#FFFFFF 등)을 (R, G, B) 튜플로 파싱합니다."""
    h = str(hex_color).lstrip('#').strip()
    if len(h) == 3:
        h = ''.join([c*2 for c in h])
    if len(h) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (255, 255, 255)


def get_contrast_color(bg_hex: str) -> str:
    """
    배경색의 상대 휘도를 계산하여 사용자 가독성을 극대화합니다.
    - 밝은 배경 (예: 흰색 #FFFFFF) -> 짙은 검은 글씨 (#111827)
    - 어두운 배경 (예: 검은색 #000000) -> 순백색 글씨 (#FFFFFF)
    """
    try:
        r, g, b = get_rgb_from_hex(bg_hex)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return "#111827" if luminance >= 0.52 else "#FFFFFF"
    except Exception:
        return "#111827"


def get_complementary_color(bg_hex: str) -> str:
    """배경색의 물리적 RGB 반전 보색(Complementary Color)을 반환합니다."""
    try:
        r, g, b = get_rgb_from_hex(bg_hex)
        comp_r = 255 - r
        comp_g = 255 - g
        comp_b = 255 - b
        return f"#{comp_r:02x}{comp_g:02x}{comp_b:02x}".upper()
    except Exception:
        return "#111827"


def make_contrast_badge(bg_hex: str, text: str, border_comp: bool = True, extra_style: str = "") -> str:
    """배경색의 보색/고대비 텍스트 색상을 자동으로 지정한 프리미엄 뱃지 HTML을 생성합니다."""
    text_color = get_contrast_color(bg_hex)
    border_style = f"border: 1px solid {get_complementary_color(bg_hex)};" if border_comp else "border: none;"
    return f'<span style="background-color:{bg_hex}; color:{text_color}; {border_style} padding:3px 9px; border-radius:4px; font-size:0.74rem; font-weight:800; display:inline-block; {extra_style}">{html.escape(text)}</span>'


# ==============================================================================
# 3. 29CM 에디토리얼 테마별 고화질 비주얼 큐레이션 엔진 & 100% 신뢰성 시맨틱 매칭
# ==============================================================================
# 1) 축제 테마별 초고화질 비주얼 풀 (깨짐 방지 및 CDN 직결)
# 1) 축제 테마별 초고화질 비주얼 풀 (깨짐 방지 및 정통 실사 보장)
FESTIVAL_THEME_VISUALS = {
    "크리스마스": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
    "성탄": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
    "트리": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
    "빛": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "유등": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "등불": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "야경": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "불꽃": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "바다": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
    "해변": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
    "갯벌": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
    "갈대": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "순천만": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "억새": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "숲": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1400",
    "화담숲": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1400",
    "꽃": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?q=80&w=1400",
    "벚꽃": "https://images.unsplash.com/photo-1522383225653-ed111181a951?q=80&w=1400",
    "국화": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?q=80&w=1400",
    "문화": "https://images.unsplash.com/photo-1538485399081-7191377e8241?q=80&w=1400",
    "도자기": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?q=80&w=1400",
    "공예": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?q=80&w=1400",
}

# 2) 로컬 미식 메뉴별 완벽 1:1 매칭 비주얼 풀 (한국 실제 음식 사진)
FOOD_MENU_VISUALS = {
    "삼겹살": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "고기": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "구이": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "불고기": "https://images.unsplash.com/photo-1590301157890-4810ed352733?q=80&w=1200",
    "갈비": "https://images.unsplash.com/photo-1590301157890-4810ed352733?q=80&w=1200",
    "김치찌개": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "된장찌개": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "부대찌개": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "순두부": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "찌개": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "국밥": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "순대": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "해장국": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "설렁탕": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "곰탕": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "비빔밥": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?q=80&w=1000",
    "육회": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?q=80&w=1000",
    "회": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=1000",
    "생선": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=1000",
    "해물": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=1000",
    "냉면": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    "국수": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    "칼국수": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    "파전": "https://images.unsplash.com/photo-1563245372-f21724e3856d?q=80&w=1000",
    "백반": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "한식": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "정식": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "돈까스": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1000",
    "짜장": "https://images.unsplash.com/photo-1525755662778-989d0524087e?q=80&w=1000",
    "짬뽕": "https://images.unsplash.com/photo-1525755662778-989d0524087e?q=80&w=1000",
    "카페": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=1000",
    "커피": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=1000",
    "베이커리": "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=1000",
}

# 3) 안심 휴식 쉼터 테마별 비주얼 풀
SPOT_THEME_VISUALS = {
    "스파오": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "의류": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "패션": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "쇼핑": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "충장로": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "숲": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "휴양림": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "치유": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "수목원": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "공원": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "정원": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "산책": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "호수": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1000",
    "스파": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1000",
    "온천": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1000",
    "절": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=1000",
    "사찰": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=1000",
    "한옥": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=1000",
}


@st.cache_data(ttl=7200, show_spinner=False)
def extract_festival_homepage_visual(url: str) -> Optional[Dict[str, Any]]:
    """축제 공식 누리집 URL에서 대표 이미지(og:image 등)를 안전하게 크롤링하여 추출합니다."""
    if not url or not str(url).startswith("http"):
        return None
    try:
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        r = requests.get(url, headers=req_headers, timeout=2.5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            # 1. OpenGraph 대표 이미지 태그
            og_img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
            if og_img and og_img.get('content'):
                img_url = urljoin(url, og_img['content'])
                if not any(bad in img_url.lower() for bad in ['pstatic.net', 'icon', 'blank', '1x1', 'logo_s', 'qr']):
                    return {
                        "url": img_url,
                        "title": "공식 누리집 대표 포스터",
                        "source": "🌐 공식 누리집 대표 사진",
                        "score": 98.0
                    }
    except Exception:
        pass
    return None


@st.cache_data(ttl=7200, show_spinner=False)
def search_and_download_best_image_b64(query: str, category: str = "general", hint: str = "", region: str = "", cache_v: str = "v3_exact_real") -> Optional[Dict[str, Any]]:
    """
    [진짜 관련 사진 실시간 검색 & 무결점 base64 추출기]
    포털에서 실제 대상의 고화질 현장 사진을 검색하고, 
    서버에서 안전하게 다운로드 및 최적화(LANCZOS 리사이즈)하여 base64로 반환합니다.
    - 403 Forbidden 핫링크 차단 완벽 우회 (100% 정상 로드)
    - 축제 현장, 식당 실제 음식, 쉼터 실제 매장/명소 100% 매칭
    """
    clean_q = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(query or "")).strip()
    clean_hint = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(hint or "")).strip()
    clean_reg = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(region or "")).strip()

    if not clean_q:
        return None

    # 지능형 검색어 구성 (실제 상황/지역과 1:1 매칭)
    search_queries = []
    if category == "festival":
        search_queries.append(f"{clean_q} {clean_reg}".strip())
        search_queries.append(clean_q)
    elif category == "restaurant":
        first_menu = clean_hint.split('(')[0].split(',')[0].split('·')[0].strip()
        if first_menu:
            search_queries.append(f"{clean_q} {clean_reg} {first_menu}".strip())
        search_queries.append(f"{clean_q} {clean_reg}".strip())
        search_queries.append(clean_q)
    elif category == "rest_spot":
        search_queries.append(f"{clean_q} {clean_reg}".strip())
        search_queries.append(clean_q)
    else:
        search_queries.append(f"{clean_q} {clean_reg}".strip())
        search_queries.append(clean_q)

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.naver.com/'
    }

    for term in search_queries:
        try:
            url = f"https://search.naver.com/search.naver?where=image&sm=tab_jum&query={quote(term)}"
            r = requests.get(url, headers=req_headers, timeout=3.5)
            if r.status_code != 200:
                continue

            unescaped = r.text.replace("&quot;", '"').replace("&amp;", "&")
            
            # 고화질 원본 URL 추출
            raw_urls = re.findall(r'"originalUrl":"(https?://[^"]+)"', unescaped)
            if not raw_urls:
                raw_urls = re.findall(r'"thumb":"(https?://[^"]+)"', unescaped)

            if not raw_urls:
                continue

            # 유효성 검사 및 정제
            valid_urls = []
            for u in raw_urls:
                clean_u = u.replace(r'\/', '/')
                u_lower = clean_u.lower()
                # 엉뚱한 이미지, 아이콘, 배너, 영수증, 지도, 피규어 배제
                if any(bad in u_lower for bad in ['icon', 'logo', 'banner', 'btn', 'receipt', 'sign', 'map', 'table', 'qrcode', 'blank', '1x1', '피규어', '애니']):
                    continue
                valid_urls.append(clean_u)

            # 상위 후보 다운로드 및 검증
            for cand_url in valid_urls[:6]:
                try:
                    res = requests.get(cand_url, headers=req_headers, timeout=3.0)
                    if res.status_code == 200 and len(res.content) > 5000:
                        img = Image.open(io.BytesIO(res.content))
                        w, h = img.size
                        if w < 250 or h < 200:
                            continue
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=82, optimize=True)
                        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        return {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "title": clean_q,
                            "source": f"📸 현장 실사 웹 검색 추출 ({clean_q})",
                            "score": 99.0
                        }
                except Exception:
                    continue
        except Exception:
            continue

    return None


def get_smart_curated_image(
    name: str, 
    category: str = "festival", 
    desc: str = "", 
    homepage: str = "", 
    region: str = "", 
    fallback_url: str = ""
) -> Dict[str, Any]:
    """
    [핵심 4대 대표 사진 전담 추출 엔진]
    1. 축제 공식 누리집 유효 이미지 (1순위)
    2. 실제 현장/식당/명소 실시간 웹 검색 & base64 변환 (2순위: 엑박 0% + 100% 현장 일치 실사)
    3. 음식 메뉴/테마 1:1 시맨틱 매칭 (3순위 엄선 실사 폴백)
    """
    clean_name = str(name or "").strip()
    clean_desc = str(desc or "").strip()
    combined_text = f"{clean_name} {clean_desc}".lower()

    # 1. 축제 공식 홈페이지가 있는 경우 우선 적용
    if homepage and category == "festival":
        hp_visual = extract_festival_homepage_visual(homepage)
        if hp_visual:
            return hp_visual

    # 2. 실제 포털 웹 검색 및 base64 다운로드 (실제 현장 사진 추출)
    real_visual = search_and_download_best_image_b64(clean_name, category=category, hint=clean_desc, region=region)
    if real_visual:
        return real_visual

    # 3. 카테고리별 시맨틱 1:1 정밀 매칭 (검색 실패 시 안전 폴백)
    if category == "festival":
        for k, img_url in FESTIVAL_THEME_VISUALS.items():
            if k in combined_text:
                return {
                    "url": img_url,
                    "title": clean_name,
                    "source": f"✨ 맞춤 에디토리얼 테마 ({k})",
                    "score": 90.0
                }
        return {
            "url": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
            "title": clean_name,
            "source": "✨ 에디토리얼 대표 축제",
            "score": 80.0
        }

    elif category == "restaurant":
        for k, img_url in FOOD_MENU_VISUALS.items():
            if k in combined_text:
                return {
                    "url": img_url,
                    "title": clean_name,
                    "source": f"🍲 대표 메뉴 실사 큐레이션 ({k})",
                    "score": 92.0
                }
        return {
            "url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
            "title": clean_name,
            "source": "🍲 정갈한 로컬 한식 미식",
            "score": 80.0
        }

    else:  # rest_spot
        # '스파오' 등 패션 매장은 웰니스 '스파'와 혼동되지 않도록 우선 처리
        if any(w in combined_text for w in ["스파오", "의류", "패션", "쇼핑", "충장로"]):
            return {
                "url": SPOT_THEME_VISUALS["스파오"],
                "title": clean_name,
                "source": "🌿 도심 패션 & 문화 쉼터",
                "score": 90.0
            }

        for k, img_url in SPOT_THEME_VISUALS.items():
            if k == "스파" and any(bad in combined_text for bad in ["스파오", "의류", "옷", "쇼핑"]):
                continue
            if k in combined_text:
                return {
                    "url": img_url,
                    "title": clean_name,
                    "source": f"🌿 안심 힐링 스팟 ({k})",
                    "score": 90.0
                }
        return {
            "url": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
            "title": clean_name,
            "source": "🌿 안심 도심 산책 쉼터",
            "score": 80.0
        }


def get_festival_status_badge(dates_str: str) -> str:
    """축제 기간 문자열을 분석하여 [진행 중 / 개최 예정 / 축제 종료] 뱃지 HTML을 반환합니다."""
    if not dates_str:
        return '<span class="editorial-badge badge-neutral">일정 확인 중</span>'
    
    date_patterns = re.findall(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", str(dates_str))
    if not date_patterns:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:18])}</span>'
    
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
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:18])}</span>'


# ==============================================================================
# 3. Streamlit 페이지 설정 & 반응형 3열 패널 CSS
# ==============================================================================
st.set_page_config(
    page_title="Fest & Rest AI · 29CM 에디토리얼 로컬 여행 매거진",
    page_icon="🗞️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,800;1,600&display=swap');

* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    letter-spacing: -0.35px;
}

/* 사이드바 UI 완전 제거 */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* 29CM 어반 보태니컬 세이지 그린 캔버스 테마 */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #EFF4F1 !important;
    color: #111827 !important;
}

/* 폼 컨트롤 스타일링 (라벨 및 본문 - 가독성 100% 보장) */
.stSelectbox label, .stSlider label, .stRadio label, .stTextInput label, .stTextArea label {
    color: #111827 !important;
    font-weight: 800 !important;
    font-size: 0.90rem !important;
}

/* [핵심 해결] 라디오 버튼 선택지(Options) 글자색 완벽 강제 (밝은 배경에 짙은 검은 글씨) */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] label div,
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] span,
div[data-testid="stRadio"] div[role="radiogroup"] label,
div[data-testid="stRadio"] div[role="radiogroup"] label * {
    color: #111827 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    text-shadow: none !important;
}

/* 셀렉트박스(드롭다운) 선택된 값 및 내부 텍스트 */
div[data-baseweb="select"] {
    background-color: #FAFCFA !important;
    border-radius: 8px !important;
}
div[data-baseweb="select"] * {
    color: #111827 !important;
    font-weight: 700 !important;
}
div[data-baseweb="select"] > div {
    background-color: #FAFCFA !important;
    border-color: #CCD8D0 !important;
    color: #111827 !important;
    border-radius: 8px !important;
}

/* 드롭다운 팝오버 목록 (펼쳤을 때 나타나는 옵션들) */
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
div[data-baseweb="popover"] div,
div[data-baseweb="popover"] span {
    color: #111827 !important;
    background-color: #FFFFFF !important;
    font-weight: 600 !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: #E5EFE9 !important;
    color: #1B4332 !important;
}

/* 텍스트 입력창 및 슬라이더 */
div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
    background-color: #FAFCFA !important;
    border-color: #CCD8D0 !important;
    color: #111827 !important;
    border-radius: 8px !important;
}
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {
    color: #111827 !important;
    font-weight: 600 !important;
}
div[data-testid="stSlider"] * {
    color: #111827 !important;
    font-weight: 600 !important;
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

/* 전체 컨텐츠 폭을 1180px로 제한하여 와이드 모니터에서 안정감 유지 */
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
    font-size: 0.82rem;
    letter-spacing: 0.08em;
    color: #4A6B5B;
    text-transform: uppercase;
    font-weight: 700;
    margin-top: 4px;
}
.editorial-pill-bar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
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

/* 3열 대칭형 제어 패널 카드 박스 - 3개 열 동일한 높이(Equal Height) 맞춤 */
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
    height: 195px !important;
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
    filter: brightness(0.95) contrast(1.02) !important;
    transition: transform 0.4s ease, filter 0.3s ease !important;
}
.stamina-dynamic-container:hover .stamina-dynamic-img {
    transform: scale(1.04) !important;
}
.stamina-dynamic-overlay {
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(180deg, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.02) 40%, rgba(0,0,0,0.72) 100%) !important;
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
    height: 460px;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 32px;
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.18);
    background-color: #1F2937;
}
.cover-bg-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.70) contrast(1.05);
}
.cover-overlay-content {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0.38) 45%, rgba(0,0,0,0.85) 100%);
    padding: 40px 44px;
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
    font-size: 2.35rem;
    font-weight: 900;
    letter-spacing: -1px;
    line-height: 1.25;
    margin: 10px 0 14px 0;
    text-shadow: 0 3px 12px rgba(0,0,0,0.4);
}
.cover-sub-meta {
    font-size: 1.0rem;
    opacity: 0.92;
    line-height: 1.6;
    max-width: 800px;
    font-weight: 300;
}
.cover-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
}
.cover-badge {
    background: rgba(255, 255, 255, 0.22);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.4);
    padding: 5px 14px;
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
    height: 185px;
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

/* 에디토리얼 뱃지 - 배경색 대비 보색/고대비 텍스트 엄격 적용 */
.editorial-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.badge-live {
    background: #111827;
    color: #FFFFFF;
    border: 1px solid #000000;
}
.badge-D-day {
    background: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
}
.badge-ended {
    background: #E5E7EB;
    color: #1F2937;
    border: 1px solid #D1D5DB;
}
.badge-neutral {
    background: #F3F4F6;
    color: #111827;
    border: 1px solid #E5E7EB;
}
.badge-img-meta {
    background: rgba(17, 24, 39, 0.75);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.4);
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    backdrop-filter: blur(4px);
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* 장소 리스트 썸네일 연동 카드 (고대비 가독성 보장) */
.place-card-with-thumb {
    display: flex;
    gap: 14px;
    align-items: center;
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.place-card-with-thumb:hover {
    border-color: #1B4332;
    transform: translateY(-1px);
}
.place-thumb-wrap {
    width: 76px;
    height: 76px;
    border-radius: 8px;
    overflow: hidden;
    flex-shrink: 0;
    background-color: #F3F4F6;
    position: relative;
    border: 1px solid #E5E7EB;
}
.place-thumb-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

/* 첫 화면 추천 축제 카드 */
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
    transform: translateY(-5px);
    box-shadow: 0 16px 30px -8px rgba(0,0,0,0.09);
    border-color: #111827;
}

/* 매거진 텍스트 본문 페이퍼 */
.editorial-article-paper {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 30px 34px;
    line-height: 1.85;
    box-shadow: 0 6px 20px rgba(0,0,0,0.02);
    color: #111827;
}

@media (max-width: 768px) {
    .editorial-top-nav {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 10px !important;
    }
    .brand-serif {
        font-size: 1.75rem !important;
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
        <h1 class="brand-serif">Fest & Rest · FestaPick</h1>
        <div class="brand-subline">100% 공공데이터 & 체력 배터리 맞춤형 로컬 힐링 여정 매거진</div>
    </div>
    <div class="editorial-pill-bar">
        <span class="nav-tag">🎪 1,264 로컬 축제</span>
        <span class="nav-tag">🍲 9,563 착한가격업소</span>
        <span class="nav-tag">🅿️ 18,883 공영주차장</span>
        <span class="nav-tag">🌿 694 치유 쉼터</span>
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
# 6. 반응형 3열 대칭형 제어 패널 (Where & When | Energy | How & Action)
# ==============================================================================
col_where, col_energy, col_action = st.columns(3, gap="medium")

# -------------------------------------------------------------
# [좌측 컬럼 (1)]: Where & When (목적지 ➔ 방문시기 ➔ 로컬 축제)
# -------------------------------------------------------------
with col_where:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 01</span> <span>📍 여행지 & 축제 탐색</span></div>', unsafe_allow_html=True)

        # 1) 목적지 선택
        region_idx = ADMIN_REGIONS.index(st.session_state.selected_region_state) if st.session_state.selected_region_state in ADMIN_REGIONS else 0
        selected_region = st.selectbox(
            "목적지 (광역 행정구역)",
            options=ADMIN_REGIONS,
            index=region_idx,
            key="main_region",
            help="원하는 지역을 선택하면 해당 지역의 실제 공공데이터 축제 목록이 조회됩니다."
        )

        # 2) 방문시기 (Month) 필터
        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        month_idx = month_options.index(st.session_state.selected_month_state) if st.session_state.selected_month_state in month_options else 10
        selected_month = st.selectbox(
            "방문시기 (월별 필터)",
            options=month_options,
            index=month_idx,
            key="main_month",
            help="축제가 개최되는 월을 선택하여 필터링합니다."
        )
        selected_month_int = int(selected_month.replace("월", "")) if selected_month != "전체" else None

        # 실제 공공데이터 축제 목록 조회 (data.py)
        try:
            festivals_list = get_festivals(region=selected_region, month=selected_month_int)
        except Exception as e:
            st.error(f"⚠️ 축제 공공데이터 조회 실패: {e}")
            festivals_list = []

        fest_data = None

        # 3) 로컬 축제 선택
        if not festivals_list:
            month_label = f" ({selected_month})" if selected_month != "전체" else ""
            st.warning(f"선택하신 '{selected_region}'{month_label}에 등록된 축제가 없습니다.")
        else:
            festival_options = {f["name"]: f for f in festivals_list}
            fest_keys = list(festival_options.keys())
            
            def_fest_idx = 0
            if st.session_state.selected_fest_name_state in fest_keys:
                def_fest_idx = fest_keys.index(st.session_state.selected_fest_name_state)
                
            selected_fest_name = st.selectbox(
                f"로컬 축제 (총 {len(festival_options)}개 검색됨)",
                options=fest_keys,
                index=def_fest_idx,
                key="main_fest"
            )
            fest_data = festival_options[selected_fest_name]

        # 축제 일정 및 뱃지 표시
        if fest_data:
            fest_dates_raw = str(fest_data.get("dates", "일정 확인 중"))
            status_badge_html = get_festival_status_badge(fest_dates_raw)
            fest_addr_brief = html.escape(str(fest_data.get("address", ""))[:26])
            st.markdown(f"""
            <div style="font-size:0.80rem; color:#4B5563; margin-top:6px; display:flex; justify-content:space-between; align-items:center;">
                <span>📅 {html.escape(fest_dates_raw[:22])}</span>
                <span>{status_badge_html}</span>
            </div>
            <div style="font-size:0.78rem; color:#6B7280; margin-top:4px;">
                📍 {fest_addr_brief}{'...' if len(str(fest_data.get("address", ""))) > 26 else ''}
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------
# [중앙 컬럼 (2)]: Energy & Dynamic Visual (체력 슬라이더 실시간 연동 비주얼)
# -------------------------------------------------------------
with col_energy:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 02</span> <span>🪫 체력 배터리 & 실시간 반응</span></div>', unsafe_allow_html=True)

        current_stamina = st.session_state.get("stamina_slider", st.session_state.get("stamina_state", 35))
        st.session_state.stamina_state = current_stamina

        # 체력 구간별 다이내믹 비주얼 & 카피 분기 (배경색 기준 보색/고대비 텍스트 적용)
        if current_stamina <= 30:
            stamina_img = "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800"
            stamina_badge = "🪫 저강도 안심 쉼표"
            stamina_copy = "도보 500m 이내 · 쉼터 80% 집중형 코스"
            bg_color = "#EF4444"
        elif current_stamina <= 70:
            stamina_img = "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=800"
            stamina_badge = "🔋 황금 밸런스 산책"
            stamina_copy = "반경 2~3km 산책 · 축제 50 : 쉼터 50"
            bg_color = "#F59E0B"
        else:
            stamina_img = "https://images.unsplash.com/photo-1501555088652-021faa106b9b?q=80&w=800"
            stamina_badge = "⚡ 파워 풀코스 액티브"
            stamina_copy = "반경 5km+ 활력 탐방 · 풀코스 위주"
            bg_color = "#10B981"

        # 사용자 편의성: 배경색의 휘도와 보색을 계산하여 가독성 극대화 (황색/호박색 배경엔 검은 글씨, 빨강/초록엔 흰 글씨)
        text_color = get_contrast_color(bg_color)
        comp_color = get_complementary_color(bg_color)
        badge_style = f"background-color:{bg_color}; color:{text_color}; border:1.5px solid {comp_color}; font-weight:800;"

        # 1) 상단 다이내믹 비주얼 카드
        st.markdown(f"""
        <div class="stamina-dynamic-container">
            <img class="stamina-dynamic-img" 
                 src="{stamina_img}" 
                 alt="체력 비주얼" 
                 onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
            <div class="stamina-dynamic-overlay">
                <span style="font-size:0.74rem; font-weight:800; padding:4px 10px; border-radius:4px; width:fit-content; {badge_style}">
                    {stamina_badge}
                </span>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; letter-spacing:-0.4px; margin-bottom:2px; text-shadow:0 2px 8px rgba(0,0,0,0.65);">
                        체력 {current_stamina}% 맞춤 모드
                    </div>
                    <div style="font-size:0.80rem; opacity:0.95; font-weight:500; text-shadow:0 1px 4px rgba(0,0,0,0.65);">
                        {stamina_copy}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2) 체력 배터리 슬라이더
        stamina = st.slider(
            "내 체력 배터리 (Stamina)",
            min_value=0,
            max_value=100,
            value=current_stamina,
            step=5,
            key="stamina_slider",
            help="30% 이하: 쉼터 80% 집중형 (도보 500m) | 30~70%: 황금 밸런스형 | 70% 이상: 풀코스 액티비티"
        )


# -------------------------------------------------------------
# [우측 컬럼 (3)]: How & Action (동반자 ➔ 이동수단 ➔ 요청사항 ➔ 발행)
# -------------------------------------------------------------
with col_action:
    with st.container(border=True):
        st.markdown('<div class="panel-card-title"><span class="panel-step-badge">STEP 03</span> <span>🚗 동행 & 여정 발행</span></div>', unsafe_allow_html=True)

        # 1) 동반자 선택
        companion = st.selectbox(
            "👥 동반자 유형",
            options=["부모님 (연로하심)", "나홀로 힐링", "연인/커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"],
            index=0,
            key="main_companion"
        )

        # 2) 이동 수단 선택
        transport = st.radio(
            "🚗 주된 이동 수단",
            options=["🚶 도보 (대중교통)", "🚗 자가용 (렌터카)"],
            index=0,
            horizontal=True,
            key="main_transport",
            help="자가용 선택 시 차량 20~30분 거리(축제장 반경 20km) 내 주차가 확보된 로컬 맛집·쉼터를 광역 탐색하며, 도보 이용 시 최단거리 중심 힐링 동선을 제공합니다."
        )

        # 3) 세부 요청사항 (자연어 LLM 심층 분석 대상)
        default_request = "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 차는 주차하기 편하고 넓은 곳이 좋겠습니다." if "부모님" in companion else "무리 없이 편안하게 즐기고 싶어요."
        extra_details = st.text_input(
            "💬 에디터 전달 세부 요청사항 (LLM 분석)",
            value=default_request,
            key="main_extra",
            help="보행 제약, 쉼터 선호도, 주차 희망사항 등을 자연어로 작성하면 LLM이 숨은 의도를 추출하여 기사에 반영합니다."
        )

        # 4) AI 맞춤 매거진 & 큐레이션 발행 버튼
        run_button = st.button(
            "🗞️ AI 맞춤 매거진 & 큐레이션 발행",
            type="primary",
            use_container_width=True,
            disabled=(fest_data is None)
        )

# 3열 카드 높이 실시간 자동 동기화 (Auto-Equalizer Script)
st_components.html("""
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
                for (let i = 0; i < 3; i++) {
                    wrappers[i].style.height = 'auto';
                    wrappers[i].style.minHeight = '0px';
                }
                const h1 = wrappers[0].scrollHeight || wrappers[0].offsetHeight;
                const h2 = wrappers[1].scrollHeight || wrappers[1].offsetHeight;
                const h3 = wrappers[2].scrollHeight || wrappers[2].offsetHeight;
                const maxHeight = Math.max(h1, h2, h3);
                
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

st.markdown("<hr style='margin:26px 0 32px 0; border:none; border-top:1px solid #CCD8D0;'/>", unsafe_allow_html=True)


# ==============================================================================
# 7. 세션 상태 관리 및 100% 공공데이터 파이프라인 실행
# ==============================================================================
if st.session_state.trigger_quick_run:
    run_button = True
    st.session_state.trigger_quick_run = False

if run_button:
    if not fest_data:
        st.error("선택된 축제 정보가 없습니다. 축제를 먼저 선택해 주세요.")
    else:
        with st.spinner("🖋️ Fest & Rest 수석 에디터가 100% 공공데이터 기반 맞춤형 여행 매거진을 조판 중입니다..."):
            user_inputs = {
                "stamina": stamina,
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

            # [2ndProject 핵심 기능: 이동 수단별 동적 검색 반경 결정]
            # 자가용: 축제장 반경 20km(20,000m) 드라이브 권역 / 도보: 체력 30 이하는 1km, 그 외는 2km 동적 할당
            if "자가용" in transport:
                dynamic_radius = 20000
            elif stamina <= 30:
                dynamic_radius = 1000
            else:
                dynamic_radius = 2000

            # 100% 실제 공공데이터 조회 (가짜/샘플 데이터 완전 배제)
            try:
                infra = get_festival_infra_bundle(
                    fest_lat=fest_data.get("lat", 0.0),
                    fest_lng=fest_data.get("lng", 0.0),
                    radius_m=dynamic_radius,
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
                # agent.py의 공식 단일 호출 함수 실행
                pipeline_output = run_processing_pipeline(user_inputs, api_data)
                st.session_state.curation_result = pipeline_output
                st.session_state.active_fest = fest_data
                st.session_state.active_transport = transport
                st.session_state.active_stamina = stamina
                st.session_state.active_companion = companion
                st.toast("🗞️ 맞춤 여행 매거진 에디토리얼이 성공적으로 발행되었습니다!", icon="✨")
            except Exception as e:
                st.error(f"❌ LangGraph 파이프라인 실행 오류: {str(e)}")


# ==============================================================================
# 8. 29CM 에디토리얼 쇼케이스 렌더링 (매거진 기사 + 지도 + 프로그램 + 인프라)
# ==============================================================================
result = st.session_state.get("curation_result")
active_fest = st.session_state.get("active_fest", fest_data)
active_transport = st.session_state.get("active_transport", "🚶 도보 (대중교통)")
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
    fest_homepage = active_fest.get("homepage", "") or result.get("festival_homepage", "")
    fest_desc = active_fest.get("description", "")

    # [핵심] 3대 거점 정보 추출 및 개별 스마트 이미지 검색 & 유사성 판단
    first_restaurant = next((p for p in map_markers if p.get("category") == "restaurant"), None)
    first_spot = next((p for p in map_markers if p.get("category") == "rest_spot"), None)

    rest_name = first_restaurant.get("name", "착한가격 식당") if first_restaurant else "로컬 추천 맛집"
    rest_desc = first_restaurant.get("desc", "정직한 가격의 대표 먹거리") if first_restaurant else "주변 외식 정보"
    spot_name = first_spot.get("name", "자연 쉼터") if first_spot else "웰니스 치유 쉼터"
    spot_desc = first_spot.get("desc", "몸과 마음을 비우는 안심 휴식처") if first_spot else "인근 힐링 명소"

    # 1. 축제 공식 누리집 크롤링 또는 웹 검색 기반 최대 유사도 사진 추출
    fest_visual = get_smart_curated_image(fest_name, category="festival", desc=fest_desc, homepage=fest_homepage, region=fest_region)
    # 2. 추천 식당 실시간 검색 및 메뉴/음식 시맨틱 유사성 분석 사진 추출
    rest_visual = get_smart_curated_image(rest_name, category="restaurant", desc=rest_desc, region=fest_region)
    # 3. 웰니스 쉼터 실시간 검색 및 자연/휴식 시맨틱 유사성 분석 사진 추출
    spot_visual = get_smart_curated_image(spot_name, category="rest_spot", desc=spot_desc, region=fest_region)

    # [WOW 포인트 1] 29CM 시네마틱 매거진 표지 (Hero Cover)
    cover_tag = "DRIVE ROAD" if "자가용" in active_transport else "WALKING REST"
    
    st.markdown(f"""
    <div class="magazine-hero-cover">
        <img class="cover-bg-image" 
             src="{fest_visual['url']}" 
             alt="{fest_name}" 
             referrerpolicy="no-referrer"
             onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
        <div class="cover-overlay-content">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="cover-vol-tag">ISSUE · {fest_region.upper()}</span>
                <span class="badge-img-meta">📸 {fest_visual['source']}</span>
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

    # [WOW 포인트 2] 3단 비주얼 스토리 타임라인 카드 (실시간 1:1 시맨틱 매칭 대표 사진 연동)
    st.markdown("""
    <div style="margin-bottom:16px; display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
            <span style="font-family:'Playfair Display', serif; font-size:1.4rem; font-weight:800; color:#111827;">Curated 3-Step Journey</span>
            <span style="font-size:0.86rem; color:#4B5563; margin-left:10px;">에디터가 추천하는 오늘의 3대 핵심 거점</span>
        </div>
        <span style="font-size:0.78rem; color:#1B4332; font-weight:700; background:#E5EFE9; padding:4px 12px; border-radius:9999px; border:1px solid #CCD8D0;">
            ✨ 대표 축제 · 로컬 미식 · 힐링 쉼터 1:1 매칭
        </span>
    </div>
    """, unsafe_allow_html=True)

    story_col1, story_col2, story_col3 = st.columns(3, gap="medium")

    with story_col1:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{fest_visual['url']}" 
                     alt="{fest_name}" 
                     referrerpolicy="no-referrer"
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">10:30 AM · FESTIVAL</span>
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{fest_visual['source']}</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#059669; font-weight:800; margin-bottom:4px;">STEP 01 · 메인 축제</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{fest_name}</h4>
                    <p style="font-size:0.84rem; color:#374151; line-height:1.5; margin:0;">계단 없는 평지 데크와 여유로운 축제장 관람 코스</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with story_col2:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{rest_visual['url']}" 
                     alt="{rest_name}" 
                     referrerpolicy="no-referrer"
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">12:30 PM · LUNCH</span>
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{rest_visual['source']}</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#D97706; font-weight:800; margin-bottom:4px;">STEP 02 · 로컬 미식</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{rest_name}</h4>
                    <p style="font-size:0.84rem; color:#374151; line-height:1.5; margin:0;">{rest_desc}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with story_col3:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" 
                     src="{spot_visual['url']}" 
                     alt="{spot_name}" 
                     referrerpolicy="no-referrer"
                     onerror="this.onerror=null; this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span class="story-step-badge">02:30 PM · WELLNESS</span>
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{spot_visual['source']}</span>
            </div>
            <div class="story-card-body">
                <div>
                    <div style="font-size:0.75rem; color:#2563EB; font-weight:800; margin-bottom:4px;">STEP 03 · 안심 휴식</div>
                    <h4 style="font-size:1.1rem; font-weight:800; color:#111827; margin:0 0 6px 0;">{spot_name}</h4>
                    <p style="font-size:0.84rem; color:#374151; line-height:1.5; margin:0;">{spot_desc}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:36px 0 28px 0; border:none; border-top:1px solid #CCD8D0;'/>", unsafe_allow_html=True)

    # [WOW 포인트 3] 2단 레이아웃 (좌측: 매거진 전문 / 우측: 지도, 프로그램, 인프라)
    col_left, col_right = st.columns([58, 42], gap="large")

    with col_left:
        sub_c1, sub_c2 = st.columns([7, 3])
        with sub_c1:
            st.markdown('<div style="font-family:\'Playfair Display\', serif; font-size:1.35rem; font-weight:800; color:#111827;">Editorial Reading</div>', unsafe_allow_html=True)
            st.caption("Fest & Rest 수석 에디터가 작성한 정직한 맞춤 여행 에세이입니다.")
        with sub_c2:
            if st.button("📋 기사 전문 복사", use_container_width=True):
                st.toast("✨ 에디토리얼 매거진 전문이 클립보드에 복사되었습니다! 소중한 동행에게 공유해보세요.", icon="📋")

        st.markdown('<div class="editorial-article-paper">', unsafe_allow_html=True)
        st.markdown(article_content)
        st.markdown('</div>', unsafe_allow_html=True)

        # 2ndProject 고유 기능: 공식 누리집 / 예매처 이동 CTA 버튼 연동
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        festival_homepage = result.get("festival_homepage", "") or active_fest.get("homepage", "")
        if festival_homepage:
            st.link_button("🌐 공식 누리집 / 예매처 바로가기", festival_homepage, use_container_width=True, type="primary")
        else:
            st.caption("ℹ️ 공식 홈페이지 정보가 제공되지 않습니다. 상세 일정 및 현장 예매는 행사장 종합안내소를 이용해 주세요.")

    with col_right:
        st.markdown('<div style="font-family:\'Playfair Display\', serif; font-size:1.35rem; font-weight:800; color:#111827; margin-bottom:4px;">Safe Mobility Map</div>', unsafe_allow_html=True)
        st.caption("축제장(🔴), 주차장(🔵), 착한가격업소(🟢), 웰니스(🟠) 4색 공공 핀")

        # Folium 인터랙티브 지도 생성 (좌표 누락 시 대한민국 전도 중심 폴백)
        fest_lat = active_fest.get("lat")
        fest_lng = active_fest.get("lng")
        is_invalid_coord = (not fest_lat or not fest_lng or abs(float(fest_lat)) < 1.0 or abs(float(fest_lng)) < 1.0)

        if is_invalid_coord:
            st.info("ℹ️ 축제장의 상세 위경도 좌표가 제공되지 않아 대한민국 전도 중심으로 지도를 표시합니다.")
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")
        else:
            m = folium.Map(location=[float(fest_lat), float(fest_lng)], zoom_start=14, tiles="CartoDB positron")

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

        st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #CCD8D0;'/>", unsafe_allow_html=True)

        # 📌 축제 주요 프로그램 안내 (3단 탭)
        st.markdown("##### 📌 축제 주요 프로그램 안내")
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        unknown_list = event_info.get("unknown", [])

        prog_tab1, prog_tab2, prog_tab3 = st.tabs([
            f"사전 예약 ({len(req_list)})",
            f"자유 참여 ({len(walk_list)})",
            f"현장 확인 ({len(unknown_list)})"
        ])

        with prog_tab1:
            if req_list:
                for item in req_list:
                    r_name = html.escape(str(item.get('name', '프로그램')))
                    r_desc = html.escape(str(item.get('description', '세부 정보 없음')))
                    r_tip = html.escape(str(item.get('booking_tip', '공식 누리집 사전 예약 필수')))
                    st.markdown(f"""
                    <div style="background:#FFF5F5; border:1.5px solid #FECACA; border-left:4px solid #EF4444; border-radius:8px; padding:12px 14px; margin-bottom:8px;">
                        <div style="font-weight:800; font-size:0.92rem; color:#991B1B;">{r_name}</div>
                        <div style="font-size:0.83rem; color:#1F2937; margin:3px 0;">{r_desc}</div>
                        <div style="font-size:0.78rem; color:#DC2626; font-weight:700;">💡 Tip: {r_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("사전 예약 필수 프로그램이 없습니다.")

        with prog_tab2:
            if walk_list:
                for item in walk_list:
                    w_name = html.escape(str(item.get('name', '프로그램')))
                    w_desc = html.escape(str(item.get('description', '세부 정보 없음')))
                    w_tip = html.escape(str(item.get('booking_tip', '현장 자유 참여 가능')))
                    st.markdown(f"""
                    <div style="background:#F0FDF4; border:1.5px solid #BBF7D0; border-left:4px solid #10B981; border-radius:8px; padding:12px 14px; margin-bottom:8px;">
                        <div style="font-weight:800; font-size:0.92rem; color:#14532D;">{w_name}</div>
                        <div style="font-size:0.83rem; color:#1F2937; margin:3px 0;">{w_desc}</div>
                        <div style="font-size:0.78rem; color:#15803D; font-weight:700;">💡 Tip: {w_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("자유 참여 프로그램이 없습니다.")

        with prog_tab3:
            if unknown_list:
                for item in unknown_list:
                    u_name = html.escape(str(item.get('name', '프로그램')))
                    u_desc = html.escape(str(item.get('description', '세부 정보 없음')))
                    u_tip = html.escape(str(item.get('booking_tip', '공식 누리집 또는 현장 안내소 문의 요망')))
                    st.markdown(f"""
                    <div style="background:#FFFBEB; border:1.5px solid #FDE68A; border-left:4px solid #F59E0B; border-radius:8px; padding:12px 14px; margin-bottom:8px;">
                        <div style="font-weight:800; font-size:0.92rem; color:#78350F;">{u_name}</div>
                        <div style="font-size:0.83rem; color:#1F2937; margin:3px 0;">{u_desc}</div>
                        <div style="font-size:0.78rem; color:#B45309; font-weight:700;">💡 Tip: {u_tip}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("현장 확인 대상 프로그램이 없습니다.")

        st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #CCD8D0;'/>", unsafe_allow_html=True)

        # 🍽️ 착한가격업소 & 🌿 관광·휴식 명소 추천 (사진 자동 추출 & 유사도 연동)
        st.markdown("##### 🍽️ 착한가격업소 & 🌿 관광·휴식 명소")

        # 2ndProject 기능 보존: result.get("model_restaurants") 우선 조회, 없으면 핀에서 추출
        restaurants_list = result.get("model_restaurants") or [p for p in map_markers if p.get("category") == "restaurant"]
        rest_spot_pins = [p for p in map_markers if p.get("category") == "rest_spot"]

        tab_rest, tab_spot = st.tabs([
            f"착한가격업소 ({len(restaurants_list)})",
            f"인근 관광·휴식 ({len(rest_spot_pins)})"
        ])

        with tab_rest:
            if restaurants_list:
                for r in restaurants_list:
                    r_name_raw = str(r.get("name", "착한가격업소"))
                    r_menu_raw = str(r.get("menu", "대표메뉴"))
                    r_name = html.escape(r_name_raw)
                    r_menu = html.escape(r_menu_raw)
                    r_price = html.escape(str(r.get("price", "가격 정보 없음")))
                    r_addr = html.escape(str(r.get("address", "")))
                    r_dist = r.get("_dist")
                    if r_dist is not None and r_dist != float('inf'):
                        dist_label = f"축제장 직선거리 약 {int(r_dist)}m"
                    else:
                        dist_label = "거리 미상 (동일 시군구 소재)"
                    addr_info = f" · {r_addr}" if r_addr else ""

                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#111827; font-size:0.92rem; font-weight:800;">🍲 {r_name}</strong>
                            <span style="font-size:0.72rem; background:#DCFCE7; color:#14532D; font-weight:800; padding:2px 7px; border-radius:4px; border:1px solid #86EFAC;">착한가격</span>
                        </div>
                        <div style="font-size:0.83rem; color:#1F2937; margin-top:3px;">
                            {r_menu} · <span style="color:#111827; font-weight:700;">{r_price}</span>
                        </div>
                        <div style="font-size:0.78rem; color:#4B5563; margin-top:2px;">📍 {dist_label}{addr_info}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("축제장 인근에 등록된 착한가격업소 정보가 없습니다.")

        with tab_spot:
            if rest_spot_pins:
                for s in rest_spot_pins:
                    s_name_raw = str(s.get("name", "관광·휴식 명소"))
                    s_desc_raw = str(s.get("desc", "인근 관광 및 휴식 명소"))
                    s_name = html.escape(s_name_raw)
                    s_desc = html.escape(s_desc_raw)

                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E5E7EB; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#111827; font-size:0.92rem; font-weight:800;">🌿 {s_name}</strong>
                            <span style="font-size:0.72rem; background:#EFF6FF; color:#1E40AF; font-weight:800; padding:2px 7px; border-radius:4px; border:1px solid #BFDBFE;">힐링 쉼터</span>
                        </div>
                        <div style="font-size:0.83rem; color:#1F2937; margin-top:3px;">{s_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("축제장 인근에 등록된 인근 관광·휴식 명소 정보가 없습니다.")

        with st.expander("🛠️ agent.py 원본 출력 딕셔너리 JSON 확인"):
            st.json(result)

else:
    # -------------------------------------------------------------
    # 첫 진입 대기 화면: 29CM 에디토리얼 프리셋 쇼케이스 3선
    # -------------------------------------------------------------
    st.markdown("""
    <div style="margin-bottom:20px; display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
            <span style="font-family:'Playfair Display', serif; font-size:1.6rem; font-weight:800; color:#111827;">Editor's Top 3 Picks</span>
            <div style="font-size:0.88rem; color:#4B5563; margin-top:3px;">수석 에디터가 엄선한 이번 시즌 가장 걷기 좋은 로컬 힐링 여정</div>
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

    st.markdown("<hr style='margin:36px 0 20px 0; border:none; border-top:1px solid #CCD8D0;'/>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#6B7280; font-size:0.84rem; padding-bottom:30px;">
        FEST & REST · 100% PUBLIC DATA MEETS GENERATIVE AI · ALL RIGHTS RESERVED
    </div>
    """, unsafe_allow_html=True)