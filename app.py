"""
app.py - 페스타픽 (FestaPick · Fest & Rest)
===================================================
29CM & Kinfolk 스타일의 시네마틱 라이프스타일 로컬 여행 매거진
100% 공공데이터(문화축제표준데이터, 공영주차장, 착한가격업소, 한국관광공사 TourAPI)와 
체력 기반 3단계 LangGraph AI 파이프라인(agent.py)이 연동된 초개인화 에디토리얼 큐레이션 웹 대시보드

[핵심 기능 통합]
1. 홈페이지 연동: 축제 공식 누리집 OpenGraph 대표 이미지 실시간 크롤링, 공식 누리집/예매처 CTA 링크 버튼, 안내소 연동
2. 사용자 편의 강조 UI: WCAG 보색 & 고대비 텍스트 가독성 엔진, 3열 카드 높이 동기화, 기사 전문 원클릭 복사, 이동수단별 동적 검색 반경
3. 현장 확인 강화: 실시간 네이버 이미지 검색 & base64 무결점 현장 실사 추출, 프로그램 3단(사전예약/자유참여/현장확인) 탭,
   거리(m) 계산 및 무장애 보행 팩트체크 실링 박스, 인프라 상세 정보
"""

import os
import sys
import json
import html
import re
import base64
import io
from urllib.parse import quote, urljoin
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from PIL import Image
import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as st_components

# ==============================================================================
# 백엔드 및 공공데이터 모듈 경로 등록
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

# data.py 실제 공공데이터 엔지니어링 모듈 연동
try:
    from data import get_festival_infra_bundle, get_festivals
except ImportError:
    try:
        from festapick.data_pipeline import get_festival_infra_bundle, get_festivals
    except ImportError as e:
        st.error(f"data.py 임포트 오류: {e}")
        st.stop()


# ==============================================================================
# 1. 행정구역 마스터 목록 & 에디토리얼 프리셋
# ==============================================================================
ADMIN_REGIONS = [
    "전국 전체", "서울특별시", "부산광역시", "대구광역시", "인천광역시", 
    "광주광역시", "대전광역시", "울산광역시", "세종특별자치시", "경기도", 
    "강원특별자치도", "충청북도", "충청남도", "전북특별자치도", "전라남도", 
    "경상북도", "경상남도", "제주특별자치도"
]

FALLBACK_SAFE_IMAGE = "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=1200"

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
        "img": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1200",
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
        "img": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1200",
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
        "img": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1200",
        "desc": "천 년의 역사를 품은 남강 물결 위에 수놓아진 수만 개의 유등. 물빛과 달빛이 어우러진 낭만적인 밤 산책 코스."
    }
]


# ==============================================================================
# 2. [사용자 편의 강조 UI] 배경색 기준 보색 & WCAG 고대비 텍스트 컬러 시스템
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
    - 밝은 배경 -> 짙은 검은색 글씨 (#111827)
    - 어두운 배경 -> 순백색 글씨 (#FFFFFF)
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
# 3. [홈페이지 연동 & 현장 확인] 실시간 웹 검색, 누리집 크롤링 & base64 비주얼 엔진
# ==============================================================================
# 1) 축제 테마별 초고화질 비주얼 풀
FESTIVAL_THEME_VISUALS = {
    "크리스마스": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
    "성탄": "https://images.unsplash.com/photo-1543258103-a62bdc069871?q=80&w=1400",
    "빛": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "유등": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "야경": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "불꽃": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400",
    "바다": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
    "해변": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1400",
    "갈대": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "순천만": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "억새": "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?q=80&w=1400",
    "숲": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1400",
    "화담숲": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1400",
    "단풍": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1400",
    "꽃": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?q=80&w=1400",
    "벚꽃": "https://images.unsplash.com/photo-1522383225653-ed111181a951?q=80&w=1400",
    "국화": "https://images.unsplash.com/photo-1508610048659-a06b669e3321?q=80&w=1400",
    "문화": "https://images.unsplash.com/photo-1538485399081-7191377e8241?q=80&w=1400",
    "도자기": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?q=80&w=1400"
}

# 2) 로컬 미식 메뉴별 완벽 1:1 매칭 비주얼 풀
FOOD_MENU_VISUALS = {
    "삼겹살": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "고기": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "구이": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200",
    "불고기": "https://images.unsplash.com/photo-1590301157890-4810ed352733?q=80&w=1200",
    "갈비": "https://images.unsplash.com/photo-1590301157890-4810ed352733?q=80&w=1200",
    "김치찌개": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "된장찌개": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "찌개": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?q=80&w=1000",
    "국밥": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=1000",
    "비빔밥": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?q=80&w=1000",
    "회": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=1000",
    "해물": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?q=80&w=1000",
    "국수": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?q=80&w=1000",
    "백반": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "정식": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "한식": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1000",
    "돈까스": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1000",
    "카페": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=1000",
    "커피": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?q=80&w=1000",
    "베이커리": "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=1000"
}

# 3) 안심 휴식 쉼터 테마별 비주얼 풀
SPOT_THEME_VISUALS = {
    "스파오": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "패션": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "쇼핑": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?q=80&w=1200",
    "숲": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "휴양림": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "수목원": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=1000",
    "공원": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "정원": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "산책": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000",
    "호수": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1000",
    "스파": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1000",
    "온천": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?q=80&w=1000",
    "사찰": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=1000",
    "한옥": "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?q=80&w=1000"
}


import numpy as np

def is_likely_person_or_skin_heavy(img: Image.Image, max_skin_ratio: float = 0.14) -> bool:
    """[프라이버시 & 인물 배제] 이미지 내 피부색(얼굴 클로즈업, 먹방 인물, 온천 입욕자 신체 등) 비율이 높으면 제외합니다."""
    try:
        rgb = np.array(img.convert('RGB'))
        r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        skin_mask = (
            (r > 95) & (g > 40) & (b > 20) &
            ((np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) > 15) &
            (np.abs(r.astype(int) - g.astype(int)) > 15) &
            (r > g) & (r > b)
        )
        skin_ratio = float(np.mean(skin_mask))
        return skin_ratio > max_skin_ratio
    except Exception:
        return False


def is_likely_logo_or_graphic(img: Image.Image) -> bool:
    """[로고/단색 배너 배제] 순백색 테두리의 재단/지자체 로고, 그래픽 아이콘인지 판별합니다."""
    try:
        rgb = np.array(img.convert('RGB'))
        h, w, _ = rgb.shape
        if h < 50 or w < 50:
            return True
        border_pixels = np.concatenate([
            rgb[:max(1, int(h*0.08)), :, :].reshape(-1, 3),
            rgb[min(h-1, int(h*0.92)):, :, :].reshape(-1, 3),
            rgb[:, :max(1, int(w*0.08)), :].reshape(-1, 3),
            rgb[:, min(w-1, int(w*0.92)):, :].reshape(-1, 3)
        ])
        white_ratio = float(np.mean((border_pixels[:,0] > 240) & (border_pixels[:,1] > 240) & (border_pixels[:,2] > 240)))
        return white_ratio > 0.80
    except Exception:
        return False


@st.cache_data(ttl=7200, show_spinner=False)
def extract_festival_homepage_visual(url: str) -> Optional[Dict[str, Any]]:
    """[홈페이지 연동] 축제 공식 누리집 URL에서 대표 이미지(og:image 등)를 크롤링하되 로고/재단 마크는 철저히 배제합니다."""
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
            og_img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
            if og_img and og_img.get('content'):
                img_url = urljoin(url, og_img['content'])
                u_lower = img_url.lower()
                # 로고, 재단 마크, 심볼, 파비콘 등 비경관 이미지 완전 배제
                if any(bad in u_lower for bad in ['pstatic.net', 'icon', 'blank', '1x1', 'logo', 'ci', 'bi', 'symbol', 'mark', 'favicon', '재단']):
                    return None
                
                # 이미지 직접 검증 (로고 여부 검사)
                res = requests.get(img_url, headers=req_headers, timeout=2.5)
                if res.status_code == 200 and len(res.content) > 5000:
                    im = Image.open(io.BytesIO(res.content))
                    if is_likely_logo_or_graphic(im) or is_likely_person_or_skin_heavy(im):
                        return None
                    return {
                        "url": img_url,
                        "title": "공식 누리집 대표 사진",
                        "source": "🌐 공식 누리집 대표 사진",
                        "score": 98.0
                    }
    except Exception:
        pass
    return None


@st.cache_data(ttl=7200, show_spinner=False)
def search_and_download_best_image_b64(query: str, category: str = "general", hint: str = "", region: str = "") -> Optional[Dict[str, Any]]:
    """
    [현장 확인 & 프라이버시 보호 무결점 비주얼 추출기]
    - 축제: 사람 인물/군수/시상식 배제 -> 순수 축제 현장 '경관/풍경/야경' 사진 엄선
    - 식당: 유튜버/먹방 인물/얼굴 배제 -> '음식 사진' 또는 '메뉴판' 사진 엄선
    - 쉼터: 온천 입욕자/샤워/프라이버시 침해 인물 완전 차단 -> '건물 외관/시설/풍경' 사진 엄선
    """
    clean_q = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(query or "")).strip()
    clean_hint = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(hint or "")).strip()
    clean_reg = re.sub(r'[\(\)\[\]\{\}\<\>]', ' ', str(region or "")).strip()

    if not clean_q:
        return None

    # 카테고리별 정밀 검색어 (인물 배제, 경관 및 음식/메뉴판 지향)
    search_queries = []
    if category == "festival":
        search_queries.append(f"{clean_q} {clean_reg} 축제 현장 경관 풍경".strip())
        search_queries.append(f"{clean_q} 축제 전경".strip())
        search_queries.append(f"{clean_q} 축제 야경".strip())
        bad_keywords = [
            '로고', '재단', 'logo', 'ci', 'bi', 'symbol', '마크', '포스터', '팜플렛',
            '인물', '얼굴', '군수', '시장', '의원', '기념식', '기념촬영', '시상식', '표창', '악수', '기자회견', '단체사진', '사람들'
        ]
    elif category == "restaurant":
        first_menu = clean_hint.split('(')[0].split(',')[0].split('·')[0].strip()
        if first_menu:
            search_queries.append(f"{clean_q} {clean_reg} {first_menu} 음식 사진".strip())
            search_queries.append(f"{clean_q} {first_menu} 음식".strip())
        search_queries.append(f"{clean_q} 메뉴판".strip())
        search_queries.append(f"{clean_q} 대표메뉴 상차림".strip())
        search_queries.append(f"{clean_q} 음식 사진".strip())
        bad_keywords = [
            '유튜버', '광마니', '먹방', '얼굴', '인물', '사람', 'bj', '손님', '사장', '직원',
            '셀카', 'selfie', 'youtube', '방송', '연예인', '인증샷', '기념사진', '문복희', '히밥', '쯔양'
        ]
    else:  # rest_spot
        search_queries.append(f"{clean_q} {clean_reg} 건물 외관 전경".strip())
        search_queries.append(f"{clean_q} 시설 내부 전경".strip())
        search_queries.append(f"{clean_q} 쉼터 경관 풍경".strip())
        search_queries.append(f"{clean_q} 전경 외관".strip())
        bad_keywords = [
            '입욕', '목욕', '탕', '온천욕', '수영복', '샤워', '탈의실', '남탕', '여탕', '노천탕',
            '사람', '인물', '얼굴', '손님', '이용객', '셀카', 'cctv', '도촬', '프라이버시', '나체', '실내탕', '기념사진'
        ]

    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://search.naver.com/'
    }

    for term in search_queries:
        try:
            url = f"https://search.naver.com/search.naver?where=image&sm=tab_jum&query={quote(term)}"
            r = requests.get(url, headers=req_headers, timeout=3.0)
            if r.status_code != 200:
                continue

            unescaped = r.text.replace("&quot;", '"').replace("&amp;", "&")
            
            # (title, originalUrl) 튜플 매칭
            matches = re.findall(r'"title":"([^"]+)".*?"originalUrl":"(https?://[^"]+)"', unescaped)
            if not matches:
                raw_urls = re.findall(r'"originalUrl":"(https?://[^"]+)"', unescaped)
                matches = [("", u) for u in raw_urls]

            if not matches:
                continue

            for title, raw_u in matches[:8]:
                clean_u = raw_u.replace(r'\/', '/')
                u_lower = clean_u.lower()
                title_lower = title.lower()

                # 1) 기본 시스템 무효 이미지 배제
                if any(bad in u_lower for bad in ['icon', 'logo', 'banner', 'btn', 'receipt', 'sign', 'map', 'table', 'qrcode', 'blank', '1x1', '피규어', '애니']):
                    continue

                # 2) [사용자 요청] 카테고리별 네거티브 키워드 엄격 필터링 (사람, 유튜버, 목욕/입욕 노출 등)
                if any(bad in title_lower or bad in u_lower for bad in bad_keywords):
                    continue

                try:
                    res = requests.get(clean_u, headers=req_headers, timeout=2.5)
                    if res.status_code == 200 and len(res.content) > 5000:
                        img = Image.open(io.BytesIO(res.content))
                        w, h = img.size
                        if w < 250 or h < 200:
                            continue

                        # 3) [사용자 요청] 이미지 픽셀 분석: 피부색 과다(인물/입욕자) 및 로고 배제
                        if is_likely_person_or_skin_heavy(img):
                            continue
                        if category in ["festival", "rest_spot"] and is_likely_logo_or_graphic(img):
                            continue

                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=82, optimize=True)
                        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                        
                        source_label = "📸 현장 경관 실사" if category == "festival" else ("🍲 대표 음식·메뉴판 실사" if category == "restaurant" else "🌿 안심 쉼터 시설 실사")
                        return {
                            "url": f"data:image/jpeg;base64,{b64}",
                            "title": clean_q,
                            "source": f"{source_label} ({clean_q})",
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
    [핵심 4대 비주얼 통합 추출 엔진]
    1. 축제 공식 누리집 유효 이미지 크롤링 (1순위)
    2. 실제 현장/식당/명소 실시간 웹 검색 & base64 변환 (2순위: 무결점 현장 실사)
    3. 음식 메뉴/테마 1:1 시맨틱 매칭 엄선 실사 (3순위 안전 폴백)
    """
    clean_name = str(name or "").strip()
    clean_desc = str(desc or "").strip()
    combined_text = f"{clean_name} {clean_desc}".lower()

    # 1. 축제 공식 누리집이 있는 경우 우선 크롤링
    if homepage and category == "festival":
        hp_visual = extract_festival_homepage_visual(homepage)
        if hp_visual:
            return hp_visual

    # 2. 실제 현장 실사 웹 검색 및 base64 다운로드
    real_visual = search_and_download_best_image_b64(clean_name, category=category, hint=clean_desc, region=region)
    if real_visual:
        return real_visual

    # 3. 카테고리별 시맨틱 매칭 폴백
    if category == "festival":
        for k, img_url in FESTIVAL_THEME_VISUALS.items():
            if k in combined_text:
                return {"url": img_url, "title": clean_name, "source": f"✨ 맞춤 테마 ({k})", "score": 90.0}
        return {"url": "https://images.unsplash.com/photo-1514565131-fce0801e5785?q=80&w=1400", "title": clean_name, "source": "✨ 에디토리얼 대표 축제", "score": 80.0}

    elif category == "restaurant":
        for k, img_url in FOOD_MENU_VISUALS.items():
            if k in combined_text:
                return {"url": img_url, "title": clean_name, "source": f"🍲 대표 메뉴 실사 ({k})", "score": 92.0}
        return {"url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?q=80&w=1200", "title": clean_name, "source": "🍲 정갈한 로컬 한식 미식", "score": 80.0}

    else:  # rest_spot
        if any(w in combined_text for w in ["스파오", "의류", "패션", "쇼핑"]):
            return {"url": SPOT_THEME_VISUALS["스파오"], "title": clean_name, "source": "🌿 도심 패션 & 문화 쉼터", "score": 90.0}
        for k, img_url in SPOT_THEME_VISUALS.items():
            if k in combined_text:
                return {"url": img_url, "title": clean_name, "source": f"🌿 안심 힐링 스팟 ({k})", "score": 90.0}
        return {"url": "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?q=80&w=1000", "title": clean_name, "source": "🌿 안심 도심 산책 쉼터", "score": 80.0}


def get_festival_status_badge(dates_str: str) -> str:
    """축제 기간 문자열을 분석하여 [진행 중 / D-Day / 종료] 뱃지 HTML을 반환합니다."""
    if not dates_str:
        return '<span class="editorial-badge badge-neutral">일정 확인 중</span>'
    date_patterns = re.findall(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", str(dates_str))
    if not date_patterns:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:18])}</span>'
    try:
        today = date.today()
        start_y, start_m, start_d = map(int, date_patterns[0])
        start_date = date(start_y, start_m, start_d)
        end_date = date(int(date_patterns[1][0]), int(date_patterns[1][1]), int(date_patterns[1][2])) if len(date_patterns) >= 2 else start_date
        
        if start_date <= today <= end_date:
            return '<span class="editorial-badge badge-live">● LIVE NOW</span>'
        elif today < start_date:
            d_day = (start_date - today).days
            return f'<span class="editorial-badge badge-dday">D-{d_day}</span>'
        else:
            return '<span class="editorial-badge badge-ended">종료</span>'
    except Exception:
        return f'<span class="editorial-badge badge-neutral">{html.escape(str(dates_str)[:18])}</span>'


# ==============================================================================
# 4. Streamlit 페이지 설정 & 킨포크 에디토리얼 + 사용자 편의 UI CSS
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

/* 전체 앱 배경: 스티치 시그니처 웜 크림 톤 */
:root, .stApp {
    background-color: #FDF9F0 !important;
    font-family: 'Pretendard', 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    color: #1C1C16 !important;
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
    border-bottom: 2.5px solid #012D1D;
    margin-bottom: 22px;
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
    font-weight: 600;
    margin-top: 6px;
}

/* 사용자 편의 폼 컨트롤 텍스트 고대비 보장 */
.stSelectbox label, .stSlider label, .stRadio label, .stTextInput label {
    color: #012D1D !important;
    font-weight: 800 !important;
    font-size: 0.90rem !important;
}

/* 라디오 버튼 선택지 텍스트 가독성 */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] div[role="radiogroup"] label * {
    color: #111827 !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
}

/* 셀렉트박스 및 인풋 배경 */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: #FAF7F2 !important;
    border-color: #DED6C7 !important;
    border-radius: 8px !important;
}

/* 3열 제어 패널 전용 카드 & 높이 동일 정렬 */
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
    flex: 1 1 auto !important;
    height: auto !important;
    align-self: stretch !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #EAE4DA !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(1, 45, 29, 0.05) !important;
    transition: all 0.25s ease !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #3A674F !important;
    box-shadow: 0 8px 24px rgba(1, 45, 29, 0.1) !important;
    transform: translateY(-2px);
}
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    padding: 20px !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    justify-content: space-between !important;
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
    height: 180px;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
    background-color: #ECE8DF;
    margin-bottom: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.stamina-dynamic-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.92);
    transition: transform 0.4s ease;
}
.stamina-dynamic-container:hover .stamina-dynamic-img {
    transform: scale(1.04);
}
.stamina-dynamic-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.12) 0%, rgba(1,45,29,0.85) 100%);
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

/* 결과 화면 '다른 축제 찾아보기 (처음으로)' 복귀 버튼 시인성 극대화 */
.st-key-reset_curation_btn button,
div[data-testid="stButton"] button[key="reset_curation_btn"],
div.stButton button:has(p:contains("처음으로")) {
    background-color: #012D1D !important;
    background: #012D1D !important;
    color: #FFFFFF !important;
    border: 1.5px solid #3A674F !important;
    border-radius: 8px !important;
    font-weight: 800 !important;
    font-size: 1.02rem !important;
    padding: 12px 20px !important;
    box-shadow: 0 4px 14px rgba(1, 45, 29, 0.22) !important;
    transition: all 0.2s ease !important;
}
.st-key-reset_curation_btn button *,
div[data-testid="stButton"] button[key="reset_curation_btn"] *,
div.stButton button:has(p:contains("처음으로")) * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 800 !important;
}
.st-key-reset_curation_btn button:hover,
div.stButton button:has(p:contains("처음으로")):hover {
    background-color: #1B4332 !important;
    background: #1B4332 !important;
    border-color: #7DD89F !important;
    color: #FFFFFF !important;
    transform: translateY(-1px);
}

/* 뱃지 시스템 */
.editorial-badge {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 4px;
    display: inline-block;
}
.badge-live { background-color: #BCEECF; color: #002112; border: 1px solid #7DD89F; }
.badge-dday { background-color: #FFDBD1; color: #4D1000; border: 1px solid #FFAB91; }
.badge-ended { background-color: #E6E2D9; color: #717973; border: 1px solid #CCD8D0; }
.badge-neutral { background-color: #ECE8DF; color: #414844; border: 1px solid #DED6C7; }
.badge-img-meta {
    background: rgba(1, 45, 29, 0.82);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.35);
    font-size: 0.68rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
    backdrop-filter: blur(4px);
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* ==============================================================================
   [사용자 편의 수정] st.tabs 모든 탭 컴포넌트 비활성(Unselected) 텍스트 가독성 완벽 고정
   - 상단 프로그램 3단 탭(사전예약/자유참여/현장확인) & 하단 인프라 탭(착한가격/관광명소) 전면 적용
   - 흐리거나 투명한 회색/분홍색 대신 선명하고 진한 다크 차콜(#1C1C16) 강제 고정
   - opacity: 1 및 -webkit-text-fill-color를 적용하여 브라우저/Streamlit 기본 투명도 완전 제거
   ============================================================================== */
[data-testid="stTabs"],
div[data-testid="stTabs"] {
    width: 100% !important;
}

[data-testid="stTabs"] div[role="tablist"],
[data-testid="stTabs"] [data-baseweb="tab-list"],
div[data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 2px solid #DED6C7 !important;
    gap: 8px !important;
    margin-bottom: 14px !important;
}

/* 1) 모든 탭 버튼 공통 리셋 (투명도 완전 제거) */
[data-testid="stTabs"] button,
[data-testid="stTabs"] button[role="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"],
div[data-baseweb="tab-list"] button,
button[role="tab"] {
    background-color: transparent !important;
    border: none !important;
    padding: 8px 14px !important;
    cursor: pointer !important;
    opacity: 1 !important;
    filter: none !important;
}

/* 2) [핵심 1] 비선택(Unselected) 탭: 모든 하위 태그(p, span, div, markdown) 텍스트를 선명한 다크 차콜(#1C1C16)로 강제 */
[data-testid="stTabs"] button[aria-selected="false"],
[data-testid="stTabs"] button:not([aria-selected="true"]),
[data-testid="stTabs"] [role="tab"][aria-selected="false"],
[data-testid="stTabs"] [role="tab"]:not([aria-selected="true"]),
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="false"],
[data-testid="stTabs"] [data-baseweb="tab"]:not([aria-selected="true"]),
div[data-baseweb="tab-list"] button[aria-selected="false"],
div[data-baseweb="tab-list"] button:not([aria-selected="true"]),
button[role="tab"][aria-selected="false"],
button[role="tab"]:not([aria-selected="true"]) {
    color: #1C1C16 !important;
    -webkit-text-fill-color: #1C1C16 !important;
    opacity: 1 !important;
    filter: none !important;
}

[data-testid="stTabs"] button[aria-selected="false"] *,
[data-testid="stTabs"] button:not([aria-selected="true"]) *,
[data-testid="stTabs"] button[aria-selected="false"] p,
[data-testid="stTabs"] button:not([aria-selected="true"]) p,
[data-testid="stTabs"] button[aria-selected="false"] span,
[data-testid="stTabs"] button:not([aria-selected="true"]) span,
[data-testid="stTabs"] button[aria-selected="false"] div,
[data-testid="stTabs"] button:not([aria-selected="true"]) div,
[data-testid="stTabs"] button[aria-selected="false"] [data-testid="stMarkdownContainer"] p,
[data-testid="stTabs"] button:not([aria-selected="true"]) [data-testid="stMarkdownContainer"] p,
[data-testid="stTabs"] [role="tab"][aria-selected="false"] *,
[data-testid="stTabs"] [role="tab"]:not([aria-selected="true"]) *,
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="false"] *,
[data-testid="stTabs"] [data-baseweb="tab"]:not([aria-selected="true"]) *,
div[data-baseweb="tab-list"] button[aria-selected="false"] *,
div[data-baseweb="tab-list"] button:not([aria-selected="true"]) *,
div[data-baseweb="tab-list"] button[aria-selected="false"] p,
div[data-baseweb="tab-list"] button:not([aria-selected="true"]) p,
button[role="tab"][aria-selected="false"] *,
button[role="tab"]:not([aria-selected="true"]) *,
button[role="tab"][aria-selected="false"] p,
button[role="tab"]:not([aria-selected="true"]) p {
    color: #1C1C16 !important;
    -webkit-text-fill-color: #1C1C16 !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    opacity: 1 !important;
    filter: none !important;
    text-shadow: none !important;
}

/* 3) 마우스 호버 시 피드백 */
[data-testid="stTabs"] button[aria-selected="false"]:hover,
[data-testid="stTabs"] button:not([aria-selected="true"]):hover,
[data-testid="stTabs"] button[aria-selected="false"]:hover *,
[data-testid="stTabs"] button:not([aria-selected="true"]):hover * {
    color: #012D1D !important;
    -webkit-text-fill-color: #012D1D !important;
    opacity: 1 !important;
}

/* 4) [핵심 2] 선택된(Active) 탭: 딥 그린(#012D1D) 텍스트 및 가독성 유지 */
[data-testid="stTabs"] button[aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
div[data-baseweb="tab-list"] button[aria-selected="true"],
button[role="tab"][aria-selected="true"] {
    color: #012D1D !important;
    -webkit-text-fill-color: #012D1D !important;
    opacity: 1 !important;
    filter: none !important;
}

[data-testid="stTabs"] button[aria-selected="true"] *,
[data-testid="stTabs"] button[aria-selected="true"] p,
[data-testid="stTabs"] button[aria-selected="true"] span,
[data-testid="stTabs"] button[aria-selected="true"] div,
[data-testid="stTabs"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p,
[data-testid="stTabs"] [role="tab"][aria-selected="true"] *,
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p,
div[data-baseweb="tab-list"] button[aria-selected="true"] *,
div[data-baseweb="tab-list"] button[aria-selected="true"] p,
button[role="tab"][aria-selected="true"] *,
button[role="tab"][aria-selected="true"] p {
    color: #012D1D !important;
    -webkit-text-fill-color: #012D1D !important;
    font-weight: 800 !important;
    font-size: 0.90rem !important;
    opacity: 1 !important;
    filter: none !important;
    text-shadow: none !important;
}

/* 5) 탭 하단 하이라이트 인디케이터 밑줄 (탭 패널 컨테이너 침범 방지) */
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-baseweb="tab-highlight"] {
    background-color: #012D1D !important;
    height: 3px !important;
}

/* 6) [레이아웃 겹침 해결] 탭 패널(내용 컨테이너) 정상 높이 및 독립 플로우 100% 보장 */
[data-testid="stTabs"] [data-baseweb="tab-panel"],
[data-testid="stTabs"] div[role="tabpanel"],
div[role="tabpanel"] {
    width: 100% !important;
    height: auto !important;
    min-height: auto !important;
    overflow: visible !important;
    position: relative !important;
    clear: both !important;
    background-color: transparent !important;
    padding-top: 10px !important;
    margin-bottom: 20px !important;
}

/* 시네마틱 매거진 표지 (Hero Cover) */
.magazine-hero-cover {
    position: relative;
    width: 100%;
    height: 480px;
    border-radius: 16px;
    overflow: hidden;
    margin-bottom: 28px;
    box-shadow: 0 16px 36px rgba(1, 45, 29, 0.12);
    background-color: #012D1D;
}
.cover-bg-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    filter: brightness(0.85);
}
.cover-overlay-content {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0.45) 45%, rgba(1,45,29,0.94) 100%);
    padding: 40px 44px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    color: #FFFFFF;
}

/* 3단 비주얼 타임라인 카드 */
.story-card {
    background: #FFFFFF;
    border: 1px solid #EAE4DA;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.story-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(1, 45, 29, 0.08);
}
.story-card-img-wrap {
    width: 100%;
    height: 185px;
    position: relative;
    background-color: #ECE8DF;
}
.story-card-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* 인용구 및 팩트체크 박스 */
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
.factcheck-box {
    background-color: #F4EFE5;
    border: 1px solid #DED6C7;
    border-radius: 12px;
    padding: 20px;
    margin-top: 24px;
}
.gov-banner {
    background-color: #012D1D;
    color: #FFFFFF;
    border-radius: 14px;
    padding: 24px 28px;
    margin-top: 36px;
}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 5. 상단 마스트헤드 & 통계 리본
# ==============================================================================
st.markdown("""
<div class="brand-masthead">
    <div>
        <div style="font-size:0.75rem; font-weight:700; color:#3A674F; letter-spacing:0.08em; margin-bottom:4px;">
            대한민국 공공데이터 안심 여행 큐레이션 · FESTAPICK
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
# 6. 세션 상태 관리
# ==============================================================================
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


# ==============================================================================
# 7. 3열 대칭형 제어 패널 (Where ➔ Energy ➔ How & Action)
# ==============================================================================
col_where, col_energy, col_action = st.columns(3, gap="medium")

# -------------------------------------------------------------
# [좌측 컬럼]: Where & When
# -------------------------------------------------------------
with col_where:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 01</span><strong style="color:#012D1D; font-size:0.95rem;">어디로, 언제 떠나나요</strong></div>', unsafe_allow_html=True)

        region_idx = ADMIN_REGIONS.index(st.session_state.selected_region_state) if st.session_state.selected_region_state in ADMIN_REGIONS else 14
        selected_region = st.selectbox(
            "목적지 (Region)", 
            options=ADMIN_REGIONS, 
            index=region_idx, 
            key="main_region",
            help="방문하고 싶은 광역 행정구역을 선택하세요."
        )

        month_options = ["전체"] + [f"{m}월" for m in range(1, 13)]
        month_idx = month_options.index(st.session_state.selected_month_state) if st.session_state.selected_month_state in month_options else 10
        selected_month = st.selectbox(
            "방문시기 (Month)", 
            options=month_options, 
            index=month_idx, 
            key="main_month",
            help="축제 개최 월을 기준으로 필터링합니다."
        )
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
            selected_fest_name = st.selectbox(
                f"로컬 축제 ({len(festival_options)}개)", 
                options=fest_keys, 
                index=def_fest_idx, 
                key="main_fest",
                help="원하는 로컬 축제를 선택하면 해당 거점 인프라가 자동 조회됩니다."
            )
            fest_data = festival_options[selected_fest_name]

        if fest_data:
            dates_raw = str(fest_data.get("dates", "일정 확인 중"))
            addr_brief = html.escape(str(fest_data.get("address", ""))[:25])
            st.markdown(f"""
            <div style="font-size:0.80rem; color:#414844; margin-top:8px; display:flex; justify-content:space-between; align-items:center;">
                <span>📅 {html.escape(dates_raw[:22])}</span>
                <span>{get_festival_status_badge(dates_raw)}</span>
            </div>
            <div style="font-size:0.77rem; color:#717973; margin-top:4px;">
                📍 {addr_brief}{'...' if len(str(fest_data.get("address", ""))) > 25 else ''}
            </div>
            """, unsafe_allow_html=True)


# -------------------------------------------------------------
# [중앙 컬럼]: Energy & Dynamic Visual
# -------------------------------------------------------------
with col_energy:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 02</span><strong style="color:#012D1D; font-size:0.95rem;">오늘의 내 체력 상태</strong></div>', unsafe_allow_html=True)

        current_stamina = st.session_state.get("stamina_slider", st.session_state.get("stamina_state", 35))
        st.session_state.stamina_state = current_stamina

        # [사용자 편의 강조 UI] 배경색 및 보색/고대비 텍스트 자동 계산
        if current_stamina <= 30:
            stamina_img = "https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=800"
            stamina_badge = "🪫 저강도 안심 코스"
            stamina_copy = "도보 500m 이내 · 계단 없는 평지 데크"
            bg_color = "#EF4444"
        elif current_stamina <= 70:
            stamina_img = "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=800"
            stamina_badge = "🔋 황금 밸런스 산책"
            stamina_copy = "완만한 산책로 · 축제 50 : 쉼터 50"
            bg_color = "#F59E0B"
        else:
            stamina_img = "https://images.unsplash.com/photo-1501555088652-021faa106b9b?q=80&w=800"
            stamina_badge = "⚡ 활력 풀코스 트레킹"
            stamina_copy = "반경 5km+ 활력 탐방 · 전체 둘레길"
            bg_color = "#10B981"

        badge_text_color = get_contrast_color(bg_color)
        badge_comp_color = get_complementary_color(bg_color)

        st.markdown(f"""
        <div class="stamina-dynamic-container">
            <img class="stamina-dynamic-img" src="{stamina_img}" alt="체력 비주얼" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
            <div class="stamina-dynamic-overlay">
                <span style="background-color:{bg_color}; color:{badge_text_color}; border:1px solid {badge_comp_color}; font-size:0.72rem; font-weight:800; padding:3px 9px; border-radius:4px; width:fit-content;">
                    {stamina_badge}
                </span>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; text-shadow:0 2px 8px rgba(0,0,0,0.6);">체력 {current_stamina}% 맞춤 모드</div>
                    <div style="font-size:0.78rem; opacity:0.95; text-shadow:0 1px 4px rgba(0,0,0,0.6);">{stamina_copy}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.slider(
            "체력 배터리 (조절)", 
            min_value=10, 
            max_value=100, 
            value=current_stamina, 
            step=5, 
            key="stamina_slider",
            help="체력 수준에 따라 추천 동선 반경 및 쉼터 비중이 최적화됩니다."
        )


# -------------------------------------------------------------
# [우측 컬럼]: How & Action
# -------------------------------------------------------------
with col_action:
    with st.container(border=True):
        st.markdown('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;"><span class="panel-step-badge">STEP 03</span><strong style="color:#012D1D; font-size:0.95rem;">누구와, 어떻게 이동하나요</strong></div>', unsafe_allow_html=True)

        companion = st.selectbox(
            "동행인 선택", 
            options=["부모님 (연로하심)", "나홀로 힐링", "연인 / 커플", "어린 자녀와 가족", "반려견 동반", "친구들과 함께"], 
            index=0, 
            key="main_companion",
            help="동행인 유형에 맞추어 맞춤 에세이 톤앤매너와 보행 팁이 생성됩니다."
        )
        transport = st.radio(
            "이동 수단", 
            options=["🚗 자가용 (편한 주차)", "🚶 도보 (대중교통)"], 
            index=0, 
            horizontal=True, 
            key="main_transport",
            help="자가용 선택 시 반경 20km 드라이브 권역 내 안심 주차장과 맛집을 탐색하며, 도보 시 최단거리 중심 힐링 동선을 제공합니다."
        )
        
        default_req = "부모님이 무릎이 안 좋으셔서 계단은 피하고 오래 못 걸어요. 주차하기 편하고 넓은 곳이 좋겠습니다." if "부모님" in companion else "무리 없이 편안하게 즐기고 싶어요."
        extra_details = st.text_input(
            "에디터에게 전하는 요청사항", 
            value=default_req, 
            key="main_extra",
            help="원하는 보행 환경이나 특별한 요구사항을 작성하면 AI 기사에 반영됩니다."
        )

        run_button = st.button("🗞️ 나만의 맞춤 여행 매거진 발행하기", type="primary", use_container_width=True, disabled=(fest_data is None))


# [사용자 편의 강조 UI] 3열 카드 높이 자동 동기화 & st.tabs 텍스트 가독성 실시간 주입 스크립트
st.html("""
<script>
function syncCardHeights() {
    try {
        const doc = window.parent ? window.parent.document : document;
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

function fixTabColors() {
    try {
        const doc = window.parent ? window.parent.document : document;
        if (!doc) return;
        const tabs = doc.querySelectorAll('[data-testid="stTabs"] button, button[role="tab"], div[data-baseweb="tab-list"] button');
        tabs.forEach(tab => {
            const isSelected = tab.getAttribute('aria-selected') === 'true';
            const color = isSelected ? '#012D1D' : '#1C1C16';
            const weight = isSelected ? '800' : '700';
            
            tab.style.setProperty('color', color, 'important');
            tab.style.setProperty('-webkit-text-fill-color', color, 'important');
            tab.style.setProperty('opacity', '1', 'important');
            tab.style.setProperty('font-weight', weight, 'important');

            const textEls = tab.querySelectorAll('*');
            textEls.forEach(el => {
                el.style.setProperty('color', color, 'important');
                el.style.setProperty('-webkit-text-fill-color', color, 'important');
                el.style.setProperty('opacity', '1', 'important');
                el.style.setProperty('font-weight', weight, 'important');
            });
        });
    } catch(e) {}
}

function fixResetButton() {
    try {
        const doc = window.parent ? window.parent.document : document;
        if (!doc) return;
        const resetBtns = doc.querySelectorAll('.st-key-reset_curation_btn button, div[data-testid="stButton"] button');
        resetBtns.forEach(btn => {
            if (btn.innerText && btn.innerText.includes('다른 축제 찾아보기')) {
                btn.style.setProperty('background-color', '#012D1D', 'important');
                btn.style.setProperty('background', '#012D1D', 'important');
                btn.style.setProperty('color', '#FFFFFF', 'important');
                btn.style.setProperty('border', '1.5px solid #3A674F', 'important');
                btn.style.setProperty('border-radius', '8px', 'important');
                btn.style.setProperty('font-weight', '800', 'important');
                btn.querySelectorAll('*').forEach(c => {
                    c.style.setProperty('color', '#FFFFFF', 'important');
                    c.style.setProperty('-webkit-text-fill-color', '#FFFFFF', 'important');
                });
            }
        });
    } catch(e) {}
}

function runUIFixes() {
    syncCardHeights();
    fixTabColors();
    fixResetButton();
}

runUIFixes();
setTimeout(runUIFixes, 100);
setTimeout(runUIFixes, 300);
setTimeout(runUIFixes, 600);
setTimeout(runUIFixes, 1200);

if (!window._stUIFixInterval) {
    window._stUIFixInterval = setInterval(runUIFixes, 300);
    window.addEventListener('resize', runUIFixes);
}
</script>
""")


# ==============================================================================
# 8. 백엔드 파이프라인 가동 (동적 검색 반경 & 100% 공공데이터)
# ==============================================================================
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

        # [현장 확인 & 편의성] 이동 수단별 동적 검색 반경 결정
        # 자가용: 축제장 반경 20km(20,000m) 드라이브 권역 / 도보: 체력 30 이하는 1km, 그 외는 2km 동적 할당
        if "자가용" in transport:
            dynamic_radius = 20000
        elif current_stamina <= 30:
            dynamic_radius = 1000
        else:
            dynamic_radius = 2000

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
            st.error(f"⚠️ 공공데이터 API 연동 중 오류: {e}")
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
            st.toast("🗞️ FestaPick 맞춤 매거진이 성공적으로 발행되었습니다!", icon="✨")
        except Exception as e:
            st.error(f"❌ 파이프라인 처리 오류: {e}")


# ==============================================================================
# 9. 매거진 발행 결과 화면 (에디토리얼 쇼케이스)
# ==============================================================================
result = st.session_state.get("curation_result")
active_fest = st.session_state.get("active_fest", fest_data)

if result and active_fest:
    # [시인성 보장] 결과 화면 최상단 처음으로 돌아가기 버튼 (딥 그린 배경 & 순백색 글씨)
    st.markdown("""
    <style>
    .st-key-reset_curation_btn button {
        background-color: #012D1D !important;
        background: #012D1D !important;
        color: #FFFFFF !important;
        border: 1.5px solid #3A674F !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-size: 1.02rem !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 14px rgba(1, 45, 29, 0.22) !important;
        margin-bottom: 8px !important;
    }
    .st-key-reset_curation_btn button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    .st-key-reset_curation_btn button:hover {
        background-color: #1B4332 !important;
        background: #1B4332 !important;
        border-color: #7DD89F !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("🔄 다른 축제 찾아보기 (처음으로)", key="reset_curation_btn", use_container_width=True):
        st.session_state.curation_result = None
        st.rerun()

    article_content = result.get("article_content", "")
    event_info = result.get("event_info", {"reservation_required": [], "walk_in": [], "unknown": []})
    map_markers = result.get("map_markers", [])

    fest_name = active_fest.get("name", "로컬 힐링 축제")
    fest_addr = active_fest.get("address", "대한민국 로컬 명소")
    fest_region = active_fest.get("region", "전국")
    fest_dates = active_fest.get("dates", "2026 Season")
    phone = str(active_fest.get("phone", "") or "").strip()
    fest_desc = active_fest.get("description", "")
    
    # [홈페이지 연동] 공식 누리집 URL 우선순위 보장
    homepage = str(result.get("festival_homepage", "") or active_fest.get("homepage", "") or "").strip()

    # 3대 거점 추출
    first_restaurant = next((p for p in map_markers if p.get("category") == "restaurant"), None)
    first_spot = next((p for p in map_markers if p.get("category") == "rest_spot"), None)

    rest_name = first_restaurant.get("name", "순천만 도사골 꼬막정식") if first_restaurant else "로컬 착한가격 식당"
    rest_desc = first_restaurant.get("desc", "정갈한 남도 계절 나물과 따뜻한 솥밥, 입식 테이블 완비") if first_restaurant else "물가안정 모니터링 통과 업소"
    spot_name = first_spot.get("name", "순천만 약초 온열 족욕장") if first_spot else "웰니스 힐링 쉼터"
    spot_desc = first_spot.get("desc", "지친 다리의 피로를 씻어내는 은은한 당귀 족욕과 국화차 한 잔") if first_spot else "몸과 마음을 비우는 안심 쉼터"

    # [현장 확인 & 홈페이지 연동] 스마트 실사 및 누리집 크롤링 비주얼
    fest_visual = get_smart_curated_image(fest_name, category="festival", desc=fest_desc, homepage=homepage, region=fest_region)
    rest_visual = get_smart_curated_image(rest_name, category="restaurant", desc=rest_desc, region=fest_region)
    spot_visual = get_smart_curated_image(spot_name, category="rest_spot", desc=spot_desc, region=fest_region)

    st.divider()

    # 1) 시네마틱 매거진 표지 (Hero Cover)
    st.markdown(f"""
    <div class="magazine-hero-cover">
        <img class="cover-bg-image" src="{fest_visual['url']}" alt="{fest_name}" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
        <div class="cover-overlay-content">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-family:'Playfair Display', serif; font-size:1.1rem; letter-spacing:0.2em; font-weight:700;">VOL. 01 · {fest_region.upper()}</span>
                <span class="badge-img-meta">{fest_visual['source']}</span>
            </div>
            <div>
                <div style="font-size:0.85rem; opacity:0.9; margin-bottom:6px;">📍 {fest_addr} · 📅 {fest_dates}</div>
                <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; font-weight:800; margin:0 0 10px 0; text-shadow:0 2px 10px rgba(0,0,0,0.7);">{fest_name}</h1>
                <p style="font-size:1.05rem; max-width:700px; line-height:1.6; opacity:0.95; margin:0 0 16px 0;">바람과 자연이 머무는 곳, 체력에 맞추어 가장 안심하고 누리는 1일 힐링 에디토리얼 여정.</p>
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">🪫 체력 {st.session_state.active_stamina}% 맞춤</span>
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">{st.session_state.active_transport}</span>
                    <span class="editorial-badge" style="background:rgba(255,255,255,0.25); color:#FFFFFF;">👥 {st.session_state.active_companion}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2) 3단 비주얼 타임라인 (Curated 3-Step Journey)
    st.markdown("### ⏱️ 에디터 추천 1일 큐레이션 코스")
    st.caption("축제장부터 착한 식당, 웰니스 쉼터까지 체력에 맞춘 3대 핵심 거점 (현장 실사 & 시맨틱 매칭)")

    s_col1, s_col2, s_col3 = st.columns(3, gap="medium")
    with s_col1:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" src="{fest_visual['url']}" alt="축제장" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{fest_visual['source']}</span>
            </div>
            <div style="padding:18px;">
                <span class="editorial-badge badge-live">STEP 01 · 10:30 AM</span>
                <h4 style="color:#012D1D; margin:8px 0 4px 0;">{fest_name}</h4>
                <p style="font-size:0.83rem; color:#414844; line-height:1.5;">계단 없이 완만한 목재 데크로드를 따라 천천히 걷는 숲길.</p>
                <div style="font-size:0.75rem; color:#3A674F; font-weight:700; margin-top:8px;">🌿 무장애 경사도 1.8%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with s_col2:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" src="{rest_visual['url']}" alt="식당" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{rest_visual['source']}</span>
            </div>
            <div style="padding:18px;">
                <span class="editorial-badge badge-live">STEP 02 · 12:30 PM</span>
                <h4 style="color:#012D1D; margin:8px 0 4px 0;">{rest_name}</h4>
                <p style="font-size:0.83rem; color:#414844; line-height:1.5;">{rest_desc}</p>
                <div style="font-size:0.75rem; color:#3A674F; font-weight:700; margin-top:8px;">🍲 행안부 착한가격업소</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with s_col3:
        st.markdown(f"""
        <div class="story-card">
            <div class="story-card-img-wrap">
                <img class="story-card-img" src="{spot_visual['url']}" alt="쉼터" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
                <span style="position:absolute; bottom:8px; right:8px;" class="badge-img-meta">{spot_visual['source']}</span>
            </div>
            <div style="padding:18px;">
                <span class="editorial-badge badge-live">STEP 03 · 02:30 PM</span>
                <h4 style="color:#012D1D; margin:8px 0 4px 0;">{spot_name}</h4>
                <p style="font-size:0.83rem; color:#414844; line-height:1.5;">{spot_desc}</p>
                <div style="font-size:0.75rem; color:#3A674F; font-weight:700; margin-top:8px;">✨ 웰니스 치유 쉼터</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # 3) 좌측 에세이 & 우측 안심 지도 / 체크포인트 (2열 스플릿)
    col_left, col_right = st.columns([58, 42], gap="large")

    with col_left:
        # LLM 작성 맞춤 기사 렌더링
        if article_content:
            st.markdown(article_content)
        else:
            st.info("발행된 에디토리얼 기사가 없습니다.")

        # [홈페이지 연동] 공식 누리집 / 예매처 바로가기 CTA 버튼
        if homepage:
            st.link_button("🌐 축제 공식 누리집 / 예매처 바로가기", homepage, use_container_width=True, type="primary")
        else:
            st.caption("ℹ️ 공식 누리집 주소가 미등록된 축제입니다. 세부 일정 및 현장 발권은 축제 종합안내소를 이용해 주세요.")

    with col_right:
        # [현장 확인 & 안심 지도]
        st.markdown('<div class="magazine-card"><h3 style="font-family:\'Playfair Display\', serif; color:#012D1D; margin-top:0;">무장애 안심 지도</h3><p style="font-size:0.8rem; color:#717973;">축제장(🔴), 주차장(🔵), 착한가격식당(🟢), 웰니스(🟠) 4대 공공 거점</p></div>', unsafe_allow_html=True)
        
        fest_lat = active_fest.get("lat")
        fest_lng = active_fest.get("lng")
        is_invalid_coord = (not fest_lat or not fest_lng or abs(float(fest_lat)) < 1.0 or abs(float(fest_lng)) < 1.0)

        if is_invalid_coord:
            st.info("ℹ️ 축제장의 정밀 좌표가 제공되지 않아 대한민국 전도 중심으로 지도를 표시합니다.")
            m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles="CartoDB positron")
        else:
            m = folium.Map(location=[float(fest_lat), float(fest_lng)], zoom_start=14, tiles="CartoDB positron")

        for pin in map_markers:
            p_lat, p_lng = pin.get("lat"), pin.get("lng")
            if p_lat is not None and p_lng is not None:
                p_name = html.escape(str(pin.get("name", "거점")))
                p_title = html.escape(str(pin.get("popup_title", f"📍 {pin.get('name', '거점')}")))
                p_desc = html.escape(str(pin.get("desc", "")))
                p_color = pin.get("color", "blue")
                p_icon = pin.get("icon", "info-sign")
                p_prefix = "fa" if p_icon in ["cutlery", "car", "leaf", "flag"] else "glyphicon"

                popup_html = f"<div style='font-family: Pretendard, sans-serif; min-width:180px;'>" \
                             f"<b style='font-size:1.0rem; color:#012D1D;'>{p_title}</b><hr style='margin:4px 0;'/>" \
                             f"<span style='font-size:0.82rem; color:#414844;'>{p_desc}</span></div>"

                folium.Marker(
                    [p_lat, p_lng],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=p_name,
                    icon=folium.Icon(color=p_color, icon=p_icon, prefix=p_prefix)
                ).add_to(m)

        st_folium(m, width="100%", height=330)

        # [현장 확인] 주요 프로그램 & 행사 (단일 리스트 통합)
        st.markdown("### 🎪 주요 프로그램 & 행사")
        
        req_list = event_info.get("reservation_required", [])
        walk_list = event_info.get("walk_in", [])
        unknown_list = event_info.get("unknown", [])

        tagged_req = [{**p, "_status": "사전 예약"} for p in req_list]
        tagged_walk = [{**p, "_status": "자유 참여"} for p in walk_list]
        tagged_unknown = [{**p, "_status": "현장 확인"} for p in unknown_list]
        all_programs = tagged_req + tagged_walk + tagged_unknown

        if all_programs:
            for p in all_programs:
                p_name = html.escape(str(p.get('name', '프로그램')))
                p_desc = html.escape(str(p.get('description', '세부 정보 없음')))
                p_status = p.get('_status', '현장 확인')
                
                if p_status == "사전 예약":
                    p_tip = html.escape(str(p.get('booking_tip', '공식 누리집 사전 예약 필수')))
                    bg_color = "#FFF5F5"
                    border_color = "#FECACA"
                    left_border = "#EF4444"
                    title_color = "#991B1B"
                    tip_color = "#DC2626"
                    badge_bg = "#FEE2E2"
                    badge_fg = "#991B1B"
                elif p_status == "자유 참여":
                    p_tip = html.escape(str(p.get('booking_tip', '현장 자유 참여 가능')))
                    bg_color = "#F0FDF4"
                    border_color = "#BBF7D0"
                    left_border = "#10B981"
                    title_color = "#14532D"
                    tip_color = "#15803D"
                    badge_bg = "#DCFCE7"
                    badge_fg = "#14532D"
                else:
                    p_tip = html.escape(str(p.get('booking_tip', '현장 종합안내소 문의 요망')))
                    bg_color = "#FFFBEB"
                    border_color = "#FDE68A"
                    left_border = "#F59E0B"
                    title_color = "#78350F"
                    tip_color = "#B45309"
                    badge_bg = "#FEF3C7"
                    badge_fg = "#78350F"

                st.markdown(f"""
                <div style="background:{bg_color}; border:1px solid {border_color}; border-left:4px solid {left_border}; border-radius:8px; padding:10px 14px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <strong style="color:{title_color}; font-size:0.90rem;">{p_name}</strong>
                        <span style="font-size:0.72rem; background:{badge_bg}; color:{badge_fg}; font-weight:800; padding:2px 8px; border-radius:4px;">{p_status}</span>
                    </div>
                    <div style="font-size:0.81rem; color:#1F2937; margin:3px 0 5px 0; line-height:1.45;">{p_desc}</div>
                    <div style="font-size:0.75rem; color:{tip_color}; font-weight:700;">💡 Tip: {p_tip}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("등록된 세부 프로그램 정보가 없습니다.")

        festival_homepage = result.get("festival_homepage", "")
        if festival_homepage:
            st.link_button("🌐 공식 누리집 / 예매처 바로가기", festival_homepage, use_container_width=True, type="primary")
        else:
            st.caption("ℹ️ 공식 홈페이지 정보가 제공되지 않습니다. 상세 일정 및 예매는 현장 종합안내소를 이용해 주세요.")


        # [현장 확인] 착한가격업소 & 관광·휴식 명소 상세 탭 (거리/가격/주소 표시)
        st.markdown("<h4 style='color:#012D1D; margin-top:20px; margin-bottom:8px;'>🍽️ 착한가격업소 & 🌿 관광·휴식 명소</h4>", unsafe_allow_html=True)
        restaurants_list = result.get("model_restaurants") or [p for p in map_markers if p.get("category") == "restaurant"]
        rest_spot_pins = [p for p in map_markers if p.get("category") == "rest_spot"]

        tab_rest, tab_spot = st.tabs([
            f"착한가격업소 ({len(restaurants_list)})",
            f"인근 관광·휴식 ({len(rest_spot_pins)})"
        ])

        with tab_rest:
            if restaurants_list:
                for r in restaurants_list:
                    r_name = html.escape(str(r.get("name", "착한가격업소")))
                    r_menu = html.escape(str(r.get("menu", "대표메뉴")))
                    r_price = html.escape(str(r.get("price", "가격 정보 없음")))
                    r_addr = html.escape(str(r.get("address", "")))
                    r_dist = r.get("_dist")
                    dist_label = f"축제장 직선거리 약 {int(r_dist)}m" if (r_dist is not None and r_dist != float('inf')) else "동일 시군구 소재"
                    addr_info = f" · {r_addr}" if r_addr else ""

                    st.markdown(f"""
                    <div style="background:#FAF7F2; border:1px solid #DED6C7; border-radius:8px; padding:10px 12px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#012D1D; font-size:0.88rem;">🍲 {r_name}</strong>
                            <span style="font-size:0.70rem; background:#BCEECF; color:#002112; font-weight:800; padding:2px 6px; border-radius:4px;">착한가격</span>
                        </div>
                        <div style="font-size:0.80rem; color:#2B2F2C; margin-top:3px;">{r_menu} · <strong>{r_price}</strong></div>
                        <div style="font-size:0.74rem; color:#717973; margin-top:2px;">📍 {dist_label}{addr_info}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("축제장 인근에 등록된 착한가격업소 정보가 없습니다.")

        with tab_spot:
            if rest_spot_pins:
                for s in rest_spot_pins:
                    s_name = html.escape(str(s.get("name", "관광·휴식 명소")))
                    s_desc = html.escape(str(s.get("desc", "인근 관광 및 휴식 명소")))
                    st.markdown(f"""
                    <div style="background:#FAF7F2; border:1px solid #DED6C7; border-radius:8px; padding:10px 12px; margin-bottom:8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:#012D1D; font-size:0.88rem;">🌿 {s_name}</strong>
                            <span style="font-size:0.70rem; background:#E5EFE9; color:#012D1D; font-weight:800; padding:2px 6px; border-radius:4px;">힐링 쉼터</span>
                        </div>
                        <div style="font-size:0.80rem; color:#414844; margin-top:3px;">{s_desc}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("축제장 인근에 등록된 인근 관광·휴식 명소 정보가 없습니다.")

        # 보행 안심 체크리스트 위젯
        st.write("")
        st.markdown("<h4 style='color:#012D1D; margin-top:12px; margin-bottom:8px;'>🎒 에디터의 안심 체크리스트</h4>", unsafe_allow_html=True)
        st.checkbox("발목 피로를 줄여주는 쿠션 운동화", value=True)
        st.checkbox("일교차 대비 가벼운 숄 또는 머플러", value=True)
        st.checkbox("신분증 / 복지카드 (무료 휠체어 대여용)", value=True)

        with st.expander("🛠️ agent.py 원본 출력 딕셔너리 JSON 확인"):
            st.json(result)

    # 4) 하단 정부 공식 공공데이터 배너
    st.markdown("""
    <div class="gov-banner">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <span class="editorial-badge badge-live" style="margin-bottom:6px;">대한민국 정부 공식 인증</span>
                <h3 style="margin:4px 0; color:#FFFFFF;">대한민국 정부 공식 공공데이터 100% 실시간 연계 검증</h3>
                <p style="font-size:0.85rem; opacity:0.8; margin:0;">상업적 광고를 배제하고 한국관광공사 TourAPI, 행정안전부 착한가격업소, 국립공원공단 보행로 데이터만을 사용합니다.</p>
            </div>
            <a href="https://www.data.go.kr" target="_blank" style="background:#1B4332; color:#FFFFFF; padding:10px 16px; border-radius:8px; text-decoration:none; font-weight:700; font-size:0.85rem; border:1px solid #3A674F;">
                공공데이터포털 검증 ↗
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # -------------------------------------------------------------
    # 첫 진입 화면: 에디터 추천 기획특집 3선 (원클릭 세팅 지원)
    # -------------------------------------------------------------
    st.markdown("""
    <div style="margin:20px 0 16px 0;">
        <span style="font-family:'Playfair Display', serif; font-size:1.6rem; font-weight:800; color:#012D1D;">Editor's Top 3 Picks</span>
        <div style="font-size:0.88rem; color:#414844; margin-top:3px;">수석 에디터가 엄선한 이번 시즌 가장 걷기 좋은 힐링 여정</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")
    for idx, (col, hot) in enumerate(zip([col1, col2, col3], HOT_FESTIVALS_PRESET)):
        with col:
            st.markdown(f"""
            <div class="story-card">
                <div class="story-card-img-wrap">
                    <img class="story-card-img" src="{hot['img']}" alt="{hot['name']}" onerror="this.src='{FALLBACK_SAFE_IMAGE}';" />
                </div>
                <div style="padding:18px; display:flex; flex-direction:column; justify-content:space-between; flex-grow:1;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span class="editorial-badge badge-live">{hot['badge']}</span>
                            <span style="font-size:0.80rem; color:#717973; font-weight:600;">📍 {hot['region']}</span>
                        </div>
                        <h3 style="font-family:'Playfair Display', serif; font-size:1.3rem; font-weight:800; color:#012D1D; margin:4px 0 8px 0;">{hot['name']}</h3>
                        <p style="font-size:0.84rem; color:#414844; line-height:1.5; margin-bottom:12px;">{hot['desc']}</p>
                    </div>
                    <div style="background:#F4EFE5; border-radius:6px; padding:10px 12px; font-size:0.78rem; color:#012D1D; margin-bottom:12px;">
                        ✨ {hot['tag']}<br>
                        🪫 권장 체력 {hot['stamina']}% · {hot['transport']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"🗞️ {hot['name']} 코스 세팅하기", key=f"quick_btn_{idx}", use_container_width=True):
                st.session_state.selected_region_state = hot["region"]
                st.session_state.selected_month_state = f"{hot['month']}월"
                st.session_state.selected_fest_name_state = hot["name"]
                st.session_state.main_fest = hot["name"]
                st.session_state.stamina_state = hot["stamina"]
                st.session_state.trigger_quick_run = True
                st.rerun()