"""
=============================================================================
대한민국 축제 & 맞춤 여행 코스 추천 AI 에이전트 (Festival & Travel Route Agent)
=============================================================================
- 기술 스택: Python, Streamlit, Pandas, Plotly, Folium, streamlit-folium
- 주요 기능:
  1. 상단 2단 레이아웃 (50% Folium 지도 + 50% AI 추천 코스 요약)
  2. 상단 탭 분리: [🗺️ 여행 코스 & 축제 탐색] / [📊 축제 테마 분포 흐름도(도넛 차트)]
  3. 사이드바-본문 즉각 반응 및 단일 상태(selected_festival_id) 기반 무오류 양방향 연동
  4. '이 축제로 코스 생성' 클릭 시 전용 상세 페이지(view_mode="detail") 전체 전환 뷰
  5. 전국 주요 축제 10선 및 연계지(관광지/맛집/야경)의 실제 도로명 상세 주소(address) 매핑
  6. Folium 인터랙티브 말풍선(Popup) 및 일정표 텍스트 다운로드에 도로명 주소 완벽 표출
=============================================================================
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from foods_data import NATIONWIDE_50_FOODS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
GINSENG_POSTER = os.path.join(ASSETS_DIR, "geumsan_ginseng.jpg")
GINSENG_FOOD = os.path.join(ASSETS_DIR, "geumsan_fried_ginseng.jpg")
DOCENT_AUDIO = os.path.join(ASSETS_DIR, "soft_female_voice.mp3")
VIP_BGM_AUDIO = os.path.join(ASSETS_DIR, "vip_auto_playlist.mp3")

# =============================================================================
# 1. Streamlit 기본 페이지 설정
# =============================================================================
st.set_page_config(
    page_title="대한민국 축제 올인원 가이드 AI (Festival Navigator)",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. 커스텀 테마 CSS (그림자 있는 미색 헤더 & 사이드바 상단 정렬 및 규격화)
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
}

/* 메인 컨테이너 및 사이드바 상단 여백 완벽 수평 정렬 */
header[data-testid="stHeader"] {
    height: 0rem !important;
    min-height: 0rem !important;
    background: transparent !important;
    z-index: 100 !important;
}

.main .block-container {
    padding-top: 0.2rem !important;
    padding-bottom: 3.5rem;
    max-width: 1280px;
}

.main .block-container > div:first-child {
    margin-top: 0px !important;
    padding-top: 0px !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 0.2rem !important;
}

section[data-testid="stSidebar"] .block-container > div:first-child {
    margin-top: 0px !important;
    padding-top: 0px !important;
}

/* 1. 멀티셀렉트 태그: 헤더 다크 그라디언트 적용 */
span[data-baseweb="tag"], div[data-baseweb="tag"] {
    background: linear-gradient(135deg, #1E1E2F 0%, #2D1B4E 50%, #1A365D 100%) !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 2px 5px rgba(30, 30, 47, 0.25) !important;
    padding: 3px 8px !important;
}

span[data-baseweb="tag"] span, div[data-baseweb="tag"] span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}

span[data-baseweb="tag"] svg, div[data-baseweb="tag"] svg {
    fill: #CBD5E1 !important;
}

/* 2. 라디오 버튼 선택: 인디고 블루 톤 */
div[data-testid="stRadio"] [aria-checked="true"] > div:first-child {
    border-color: #4F46E5 !important;
}

div[data-testid="stRadio"] [aria-checked="true"] > div:first-child > div {
    background-color: #4F46E5 !important;
}

/* 3. Primary 버튼: 헤더 그라디언트 & 호버 입체감 */
button[kind="primary"], div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1E1E2F 0%, #2D1B4E 50%, #1A365D 100%) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    box-shadow: 0 4px 14px rgba(30, 30, 47, 0.35) !important;
    transition: all 0.25s ease-in-out !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
}

button[kind="primary"]:hover, div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2D1B4E 0%, #3B2D60 50%, #2563EB 100%) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
    transform: translateY(-2px) !important;
}

/* Secondary 버튼 스타일링 */
button[kind="secondary"], div.stButton > button[kind="secondary"] {
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease-in-out !important;
}

button[kind="secondary"]:hover, div.stButton > button[kind="secondary"]:hover {
    border-color: #4F46E5 !important;
    color: #4F46E5 !important;
    background-color: #F8FAFC !important;
}

/* 4. 상단 히어로 배너 (그림자 있는 고급 미색 테마) */
.hero-banner {
    background: linear-gradient(135deg, #FDFBF7 0%, #F9F6F0 50%, #F2EDE4 100%);
    border-radius: 20px;
    padding: 28px 34px;
    color: #1E293B;
    margin-top: 0px !important;
    margin-bottom: 20px;
    box-shadow: 0 12px 32px rgba(60, 50, 40, 0.08), 0 4px 12px rgba(60, 50, 40, 0.04);
    border: 1px solid rgba(222, 212, 198, 0.85);
    position: relative;
    overflow: hidden;
}

.hero-banner::after {
    content: "✈️";
    position: absolute;
    right: 25px;
    bottom: -15px;
    font-size: 95px;
    opacity: 0.12;
    pointer-events: none;
}

.hero-title {
    font-size: 1.95rem;
    font-weight: 800;
    margin: 6px 0 8px 0;
    letter-spacing: -0.5px;
    background: linear-gradient(90deg, #0F172A 0%, #1E1B4B 50%, #312E81 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 0.98rem;
    color: #475569;
    margin: 0 0 10px 0;
    font-weight: 500;
    line-height: 1.55;
}

.agent-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #065F46;
    padding: 4px 12px;
    border-radius: 30px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.agent-dot {
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
}

/* 사이드바 여행 큐레이터 설정 박스 (상단 맞춤 & 그림자 있는 미색 테마) */
.sidebar-curator-box {
    background: linear-gradient(135deg, #FDFBF7 0%, #F9F6F0 50%, #F2EDE4 100%);
    padding: 22px 20px 24px 20px;
    border-radius: 18px;
    margin-top: 0px !important;
    margin-bottom: 22px;
    border: 1px solid rgba(222, 212, 198, 0.85);
    box-shadow: 0 12px 28px rgba(60, 50, 40, 0.08), 0 4px 12px rgba(60, 50, 40, 0.04);
    position: relative;
    overflow: hidden;
}

.sidebar-curator-box::after {
    content: "🧭";
    position: absolute;
    right: 12px;
    bottom: 6px;
    font-size: 54px;
    opacity: 0.10;
    pointer-events: none;
}

.sidebar-curator-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #3730A3;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.sidebar-dot {
    width: 7px;
    height: 7px;
    background-color: #4F46E5;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(79, 70, 229, 0.5);
}

.sidebar-curator-title {
    margin: 8px 0 0 0;
    font-size: 1.32rem;
    font-weight: 800;
    letter-spacing: -0.4px;
    background: linear-gradient(90deg, #0F172A 0%, #1E1B4B 60%, #312E81 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.sidebar-curator-subtitle {
    margin: 8px 0 0 0;
    font-size: 0.88rem;
    color: #556987;
    line-height: 1.5;
    font-weight: 500;
}

/* 5. 카드 그리드 높이 완벽 통일 규격화 (490px) */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    height: 100% !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    min-height: 550px !important;
}

/* 카드 내 썸네일 이미지 규격화 */
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stImage"] img {
    height: 170px !important;
    width: 100% !important;
    object-fit: cover !important;
    border-radius: 10px !important;
}

/* 상세 뷰 전용 대형 포스터 배너 */
.detail-poster-img div[data-testid="stImage"] img {
    height: 330px !important;
    width: 100% !important;
    object-fit: cover !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15) !important;
}

/* 카드 텍스트 2줄 말줄임 클램핑 */
.card-text-clamp {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    min-height: 2.8rem;
    font-size: 0.84rem;
    color: #475569;
    line-height: 1.45;
}

/* 타임라인 카드 스타일 */
.timeline-item {
    background: #F8FAFC;
    border-left: 4px solid #4F46E5;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
}

.sidebar-timeline-step {
    border-left: 3px solid #4F46E5;
    padding-left: 10px;
    margin-bottom: 8px;
    font-size: 0.82rem;
}

/* 주소 안내 뱃지 */
.address-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.79rem;
    color: #475569;
    background: #F1F5F9;
    padding: 3px 8px;
    border-radius: 6px;
    margin-top: 4px;
    border: 1px solid #E2E8F0;
    word-break: break-all;
}

/* 6. 감성 여행 BGM 플레이어 & 오디오 비주얼라이저 */
.bgm-visual-box {
    background: linear-gradient(135deg, #1E1B4B 0%, #2D1B4E 50%, #1A365D 100%);
    border-radius: 14px;
    padding: 12px 14px;
    color: #FFFFFF;
    margin-bottom: 10px;
    box-shadow: 0 8px 18px rgba(30, 27, 75, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.15);
    display: flex;
    align-items: center;
    gap: 12px;
}

.vinyl-disc {
    width: 38px;
    height: 38px;
    min-width: 38px;
    border-radius: 50%;
    background: radial-gradient(circle, #0F172A 28%, #334155 30%, #0F172A 50%, #334155 52%, #1E293B 70%);
    border: 2px solid #CBD5E1;
    box-shadow: 0 0 8px rgba(0, 0, 0, 0.4);
    animation: spin 3s linear infinite;
    display: flex;
    align-items: center;
    justify-content: center;
}

.vinyl-center {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #F59E0B;
    border: 2px solid #FFFFFF;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.bgm-info {
    flex: 1;
}

.bgm-title {
    font-size: 0.84rem;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
    line-height: 1.3;
}

.bgm-desc {
    font-size: 0.72rem;
    color: #CBD5E1;
}

.equalizer-bar-container {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 20px;
}

.eq-bar {
    width: 3px;
    background: #38BDF8;
    border-radius: 2px;
    animation: bounce-bar 1.2s ease-in-out infinite alternate;
}

.eq-bar:nth-child(1) { height: 6px; animation-delay: 0.0s; }
.eq-bar:nth-child(2) { height: 16px; animation-delay: 0.2s; }
.eq-bar:nth-child(3) { height: 10px; animation-delay: 0.4s; }
.eq-bar:nth-child(4) { height: 20px; animation-delay: 0.1s; }
.eq-bar:nth-child(5) { height: 12px; animation-delay: 0.3s; }

@keyframes bounce-bar {
    0% { height: 4px; }
    100% { height: 20px; }
}

/* 7. 메트릭 카드 및 숫자 글씨 크기 최적화 (가독성 높은 크기로 조정) */
div[data-testid="stMetric"] {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.82rem !important;
    color: #475569 !important;
    font-weight: 600 !important;
}

div[data-testid="stMetricLabel"] p {
    font-size: 0.82rem !important;
    color: #475569 !important;
    font-weight: 600 !important;
    margin-bottom: 2px !important;
}

div[data-testid="stMetricValue"] {
    font-size: 1.18rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
}

div[data-testid="stMetricValue"] > div {
    font-size: 1.18rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    line-height: 1.35 !important;
    white-space: nowrap !important;
}

div[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    margin-top: 2px !important;
}

div[data-testid="stMetricDelta"] div {
    font-size: 0.78rem !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# 오디오 볼륨 자동 밸런싱 & 오디오 더킹(Ducking) 컨트롤러
# - BGM 볼륨: 15~20%로 잔잔하게 설정
# - 음성 브리핑: 100% 또렷한 볼륨
# - 음성 브리핑 재생 시: BGM이 5%로 자동 감쇄(Ducking)되어 목소리가 크고 명확하게 들림
# =============================================================================
components.html("""
<script>
function balanceAudioVolumes() {
    try {
        const pdoc = window.parent.document;
        // 1. 사이드바 BGM 음량을 20%로 부드럽게 고정
        const sidebarAudios = pdoc.querySelectorAll('section[data-testid="stSidebar"] audio');
        sidebarAudios.forEach(a => {
            if (!a.dataset.ducked && a.volume > 0.22) {
                a.volume = 0.20;
            }
        });

        // 2. 본문 AI 도슨트 음량 100% 설정 & 오디오 더킹(Audio Ducking) 리스너 등록
        const mainAudios = pdoc.querySelectorAll('.main audio');
        mainAudios.forEach(a => {
            a.volume = 1.0;
            if (!a.dataset.duckingListener) {
                a.dataset.duckingListener = "true";
                // 음성 재생 시 -> BGM을 5% 초미세 배경음으로 축소
                a.addEventListener('play', () => {
                    const bgms = pdoc.querySelectorAll('section[data-testid="stSidebar"] audio');
                    bgms.forEach(bgm => {
                        bgm.dataset.ducked = "true";
                        bgm.volume = 0.05;
                    });
                });
                // 음성 일시정지 또는 종료 시 -> BGM을 원래 잔잔한 20%로 복원
                const restoreBgm = () => {
                    const bgms = pdoc.querySelectorAll('section[data-testid="stSidebar"] audio');
                    bgms.forEach(bgm => {
                        bgm.dataset.ducked = "false";
                        bgm.volume = 0.20;
                    });
                };
                a.addEventListener('pause', restoreBgm);
                a.addEventListener('ended', restoreBgm);
            }
        });
    } catch(err) {}
}
setInterval(balanceAudioVolumes, 300);
balanceAudioVolumes();
</script>
""", height=0, width=0)


# =============================================================================
# 3. 전국 주요 축제 10선 & 지역 대표 음식 실데이터 구축 (도로명 상세 주소 포함)
# =============================================================================
FESTIVAL_DATABASE = [
    {
        "id": 1,
        "name": "보령 머드축제",
        "region": "충남",
        "period": "2026.07.17 ~ 2026.07.26",
        "theme": "야경/체험",
        "address": "충청남도 보령시 해수욕장10길 5 (대천해수욕장 머드광장)",
        "description": "세계인이 열광하는 글로벌 머드 체험! 대천해수욕장의 고운 머드로 온몸을 적시며 장애물 코스와 K-POP 콘서트를 만끽하는 대한민국 대표 여름 축제입니다.",
        "poster_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
        "homepage_url": "https://www.mudfestival.or.kr/",
        "lat": 36.3055,
        "lon": 126.5167,
        "tips": {
            "parking": "대천해수욕장 제1~3 임시공영주차장 무료 셔틀버스 상시 운행 (해변 제4주차장 권장)",
            "outfit": "머드 착색 대비 짙은 계열 여벌옷, 아쿠아슈즈, 스마트폰 방수팩 및 여벌 타월 필수"
        },
        "food": {
            "name": "대천 키조개삼합 & 해물칼국수",
            "category": "시원한 해산물/회",
            "price": "35,000원 ~ 50,000원 (2인)",
            "address": "충청남도 보령시 머드로 131 (대천해수욕장 먹거리타운)",
            "signature": "차돌박이 + 생키조개 관자 + 활전복 3합 철판구이 & 바지락 칼국수",
            "spot": "대천해수욕장 머드먹거리타운 / 오천항 수산물센터",
            "photo_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "개화예술공원 (감성 조각 & 온실 카페)", "category": "관광지", "address": "충청남도 보령시 성주면 개화포전길 177", "lat": 36.3298, "lon": 126.6540},
            {"name": "대천항 수산시장 (활어회 & 조개구이)", "category": "로컬맛집", "address": "충청남도 보령시 대천항지하길 13", "lat": 36.3265, "lon": 126.5050},
            {"name": "무창포 낙조전망대 (신비의 바닷길 & 일몰)", "category": "야경명소", "address": "충청남도 보령시 웅천읍 열린바다1길 78", "lat": 36.2422, "lon": 126.5368}
        ]
    },
    {
        "id": 2,
        "name": "금산 인삼축제",
        "region": "충남",
        "period": "2026.10.02 ~ 2026.10.11",
        "theme": "미식",
        "address": "충청남도 금산군 금산읍 인삼광장로 30 (금산인삼관 광장)",
        "description": "1,500년 전통의 고려인삼 종주지 금산에서 펼쳐지는 건강 힐링 축제! 인삼 캐기 체험과 보양식을 즐기며 활력을 재충전해보세요.",
        "poster_url": GINSENG_POSTER if os.path.exists(GINSENG_POSTER) else "assets/geumsan_ginseng.jpg",
        "homepage_url": "https://www.ginsengfestival.co.kr/",
        "lat": 36.1039,
        "lon": 127.4878,
        "tips": {
            "parking": "금산인삼관 뒤편 대형 임시주차장 무료 이용 가능 (수삼시장 도보 3분)",
            "outfit": "인삼 캐기 체험용 편안한 운동화 및 흙 묻어도 되는 바지, 챙 넓은 모자 권장"
        },
        "food": {
            "name": "금산 수삼튀김 & 원조 영양어죽",
            "category": "든든한 향토 한식",
            "price": "12,000원 ~ 18,000원",
            "address": "충청남도 금산군 제원면 금강로 588 (제원 어죽마을)",
            "signature": "바삭한 통수삼튀김(조청 디핑) & 진한 민물 보양 어죽",
            "spot": "금산 수삼시장 먹거리장터 / 제원면 어죽마을",
            "photo_url": GINSENG_FOOD if os.path.exists(GINSENG_FOOD) else "assets/geumsan_fried_ginseng.jpg"
        },
        "nearby_spots": [
            {"name": "월영산 출렁다리 (금강 파노라마 트레킹)", "category": "관광지", "address": "충청남도 금산군 제원면 천내리 168-5", "lat": 36.1432, "lon": 127.5670},
            {"name": "금산 수삼시장 삼계탕거리 (바삭 인삼튀김)", "category": "로컬맛집", "address": "충청남도 금산군 금산읍 인삼약초로 24", "lat": 36.1050, "lon": 127.4890},
            {"name": "천년고찰 보석사 (은행나무 힐링 야간 산책)", "category": "야경명소", "address": "충청남도 금산군 남이면 보석사길 30", "lat": 36.0350, "lon": 127.4420}
        ]
    },
    {
        "id": 3,
        "name": "강릉 커피축제",
        "region": "강원",
        "period": "2026.10.08 ~ 2026.10.11",
        "theme": "미식",
        "address": "강원특별자치도 강릉시 수리골길 102 (강릉아레나)",
        "description": "솔향과 파도 소리, 그윽한 에스프레소 향미가 어우러지는 낭만 축제! 국내 최고 마스터 바리스타들의 스페셜티 커피를 무료 시음할 수 있습니다.",
        "poster_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80",
        "homepage_url": "https://www.coffeefestival.net/",
        "lat": 37.7736,
        "lon": 128.9482,
        "tips": {
            "parking": "강릉 아레나 메인 주차장 무료 이용 및 안목해변 커피거리 무료 순환 셔틀 연계",
            "outfit": "해변 바닷바람 대비 얇은 윈드브레이커 및 커피거리 산책용 편안한 스니커즈"
        },
        "food": {
            "name": "초당 짬뽕순두부 & 순두부젤라또",
            "category": "든든한 향토 한식",
            "price": "13,000원 ~ 16,000원",
            "address": "강원특별자치도 강릉시 초당순두부길 77 (초당 순두부마을)",
            "signature": "불향 가득 얼큰 해물 짬뽕순두부 & 고소한 순두부젤라또",
            "spot": "강릉 초당 순두부마을 / 안목해변",
            "photo_url": "https://images.unsplash.com/photo-1547496502-affa22d38842?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "오죽헌 & 경포호수 (솔숲 역사 산책)", "category": "관광지", "address": "강원특별자치도 강릉시 율곡로3139번길 24 (죽헌동)", "lat": 37.7792, "lon": 128.8805},
            {"name": "초당 순두부마을 (짬뽕순두부 & 순두부젤라또)", "category": "로컬맛집", "address": "강원특별자치도 강릉시 초당순두부길 89-8", "lat": 37.7905, "lon": 128.9150},
            {"name": "안목해변 커피거리 (달빛 파도 감성 테라스)", "category": "야경명소", "address": "강원특별자치도 강릉시 창해로14번길 20-1", "lat": 37.7718, "lon": 128.9488}
        ]
    },
    {
        "id": 4,
        "name": "화천 산천어축제",
        "region": "강원",
        "period": "2027.01.09 ~ 2027.02.01",
        "theme": "야경/체험",
        "address": "강원특별자치도 화천군 화천읍 산천어길 137 (화천천 일원)",
        "description": "CNN이 '세계 겨울 7대 불가사의'로 극찬한 겨울 왕국! 40cm 얼음판을 뚫고 즐기는 산천어 얼음낚시와 짜릿한 눈썰매, 화려한 얼음조각 축제.",
        "poster_url": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=80",
        "homepage_url": "https://www.narafestival.com/",
        "lat": 38.1062,
        "lon": 127.7082,
        "tips": {
            "parking": "화천천 하류 제1~5 무료 축제 주차장 (빙판 낚시장 전용 주차타워 안내)",
            "outfit": "영하권 혹한 대비 방한화, 핫팩, 두툼한 패딩, 귀마개 및 휴대용 낚시의자"
        },
        "food": {
            "name": "화천 산천어 숯불회구이 & 수수부꾸미",
            "category": "시원한 해산물/회",
            "price": "15,000원 ~ 25,000원",
            "address": "강원특별자치도 화천군 화천읍 산천어길 137 (축제장 구이터)",
            "signature": "현장에서 갓 잡은 신선한 산천어 숯불구이 & 팥앙금 부꾸미",
            "spot": "화천천 축제장 구이터",
            "photo_url": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "실내 얼음조각광장 (하얼빈 빙등제 재현)", "category": "관광지", "address": "강원특별자치도 화천군 화천읍 상승로 103", "lat": 38.1055, "lon": 127.7050},
            {"name": "화천 산천어 구이터 (갓 잡은 산천어 숯불구이)", "category": "로컬맛집", "address": "강원특별자치도 화천군 화천읍 산천어길 150", "lat": 38.1080, "lon": 127.7120},
            {"name": "선등거리 루미나리에 (2만 7천 개 산천어 등불)", "category": "야경명소", "address": "강원특별자치도 화천군 화천읍 중앙로 38", "lat": 38.1070, "lon": 127.7065}
        ]
    },
    {
        "id": 5,
        "name": "순천만 갈대축제",
        "region": "전남",
        "period": "2026.11.06 ~ 2026.11.08",
        "theme": "힐링/자연",
        "address": "전라남도 순천시 순천만길 513-25 (순천만습지)",
        "description": "황금빛 갈대 숲과 붉은 칠면초 군락이 끝없이 펼쳐지는 생태의 보고! 흑두루미의 힘찬 날갯짓과 서정적인 갯벌의 숨결을 그대로 느껴보세요.",
        "poster_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&q=80",
        "homepage_url": "https://scbay.suncheon.go.kr/",
        "lat": 34.8872,
        "lon": 127.5083,
        "tips": {
            "parking": "순천만습지 전용 주차장 (일반 3,000원, 만차 시 순천만국가정원 서문 주차장 셔틀 이용)",
            "outfit": "끝없는 갈대 데크길(왕복 4km) 산책을 위한 편안한 트레킹화 및 일몰 체온 유지용 머플러"
        },
        "food": {
            "name": "순천만 꼬막정식 & 보양 짱뚱어탕",
            "category": "시원한 해산물/회",
            "price": "20,000원 ~ 25,000원",
            "address": "전라남도 순천시 순천만길 545 (순천만 꼬막마을)",
            "signature": "통꼬막 데침, 새콤달콤 꼬막무침, 꼬막전 & 깊은 갯벌 짱뚱어탕",
            "spot": "순천만습지 꼬막마을",
            "photo_url": "https://images.unsplash.com/photo-1617093727343-374698b1b08d?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "순천만 꼬막정식 & 보양 짱뚱어탕", "category": "로컬맛집", "address": "전라남도 순천시 순천만길 545", "lat": 34.8950, "lon": 127.5020},
            {"name": "순천만 국가정원 (세계 5대 연안습지 테마정원)", "category": "관광지", "address": "전라남도 순천시 국가정원1호길 47", "lat": 34.9315, "lon": 127.5090},
            {"name": "용산전망대 (S자 수로 황혼 노을 뷰포인트)", "category": "야경명소", "address": "전라남도 순천시 순천만길 513-25 (용산전망대 코스)", "lat": 34.8770, "lon": 127.5120}
        ]
    },
    {
        "id": 6,
        "name": "전주 비빔밥축제",
        "region": "전북",
        "period": "2026.10.23 ~ 2026.10.26",
        "theme": "미식",
        "address": "전북특별자치도 전주시 완산구 풍남문2길 80 (한옥마을 및 경기전 광장)",
        "description": "유네스코 음식창의도시 전주의 맛과 멋! 수천 명이 함께 비비는 초대형 비빔밥 퍼포먼스와 한옥마을 골목 곳곳에서 펼쳐지는 풍류 버스킹 축제입니다.",
        "poster_url": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=800&q=80",
        "homepage_url": "https://tour.jeonju.go.kr/",
        "lat": 35.8150,
        "lon": 127.1539,
        "tips": {
            "parking": "기린대로 노상 공영주차장 및 남부시장 천변 무료 공영주차장 이용 권장",
            "outfit": "한옥마을 골목길 투어용 가벼운 워킹화 & 한복 체험 추천 (편안한 이너웨어)"
        },
        "food": {
            "name": "전주 놋그릇 육회비빔밥 & 한옥 모주",
            "category": "든든한 향토 한식",
            "price": "14,000원 ~ 18,000원",
            "address": "전북특별자치도 전주시 완산구 어진길 119 (한국집)",
            "signature": "사골 육수 밥에 황포묵, 육회, 나물을 올린 놋그릇 비빔밥",
            "spot": "전주 한옥마을 한국집",
            "photo_url": "https://images.unsplash.com/photo-1553163147-622ab57be1c7?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "경기전 & 어진박물관 (고즈넉한 대나무 숲길)", "category": "관광지", "address": "전북특별자치도 전주시 완산구 태조로 44", "lat": 35.8147, "lon": 127.1526},
            {"name": "한국집 & 전주옥 (원조 놋그릇 육회비빔밥)", "category": "로컬맛집", "address": "전북특별자치도 전주시 완산구 어진길 119", "lat": 35.8160, "lon": 127.1510},
            {"name": "남부시장 야시장 & 청년몰 (피순대 & 불곱창)", "category": "야경명소", "address": "전북특별자치도 전주시 완산구 풍남문1길 19-3", "lat": 35.8118, "lon": 127.1479}
        ]
    },
    {
        "id": 7,
        "name": "진주 남강유등축제",
        "region": "경남",
        "period": "2026.10.10 ~ 2026.10.22",
        "theme": "야경/체험",
        "address": "경상남도 진주시 남강로 626 (진주성 및 남강 일원)",
        "description": "임진왜란 진주성 전투에서 유래한 수만 개의 빛의 향연! 남강 물결 위에 띄운 소망등과 웅장한 부교 위를 걸으며 황홀한 밤의 전설을 마주하세요.",
        "poster_url": "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=800&q=80",
        "homepage_url": "https://yudeung.com/",
        "lat": 35.1804,
        "lon": 128.0827,
        "tips": {
            "parking": "진주 혁신도시 공설운동장 무료 환승주차장 이용 후 남강 행사장 직행 셔틀 탑승",
            "outfit": "남강 강바람이 쌀쌀하므로 경량 패딩 또는 도톰한 겉옷 지참, 부교 산책용 운동화"
        },
        "food": {
            "name": "진주 70년 전통 육회비빔밥 & 육전냉면",
            "category": "든든한 향토 한식",
            "price": "11,000원 ~ 16,000원",
            "address": "경상남도 진주시 촉석로207번길 3 (천황식당)",
            "signature": "화반(花盤) 육회비빔밥과 고소한 쇠고기 육전 메밀냉면",
            "spot": "진주 중앙시장 천황식당",
            "photo_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "진주성 & 국립진주박물관 (역사 탐방)", "category": "관광지", "address": "경상남도 진주시 남강로 626 (본성동)", "lat": 35.1885, "lon": 128.0841},
            {"name": "천황식당 (80년 전통 진주비빔밥 & 석쇠불고기)", "category": "로컬맛집", "address": "경상남도 진주시 촉석로207번길 3 (대안동)", "lat": 35.1930, "lon": 128.0860},
            {"name": "망진산 봉수대 (남강 유등 파노라마 야경)", "category": "야경명소", "address": "경상남도 진주시 망경동 391-2", "lat": 35.1765, "lon": 128.0772}
        ]
    },
    {
        "id": 8,
        "name": "안동 국제탈춤페스티벌",
        "region": "경북",
        "period": "2026.09.25 ~ 2026.10.04",
        "theme": "전통문화",
        "address": "경상북도 안동시 육사로 239 (탈춤공원 일원)",
        "description": "신명 나는 해학과 풍자의 한마당! 국내외 탈춤 장인들의 공연과 하회별신굿탈놀이, 관객 모두가 탈을 쓰고 하나 되는 거리 대동난장 축제입니다.",
        "poster_url": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800&q=80",
        "homepage_url": "https://www.maskdance.com/",
        "lat": 36.5684,
        "lon": 128.7294,
        "tips": {
            "parking": "탈춤공원 내 축제 전용 주차장 및 낙동강변 둔치 무료 대형 주차장 완비",
            "outfit": "대동난장 댄스 참여를 위한 가벼운 캐주얼 복장과 미끄럼 방지 스니커즈"
        },
        "food": {
            "name": "안동 구시장 찜닭 & 헛제사밥",
            "category": "바삭 별미/육류",
            "price": "15,000원 ~ 32,000원",
            "address": "경상북도 안동시 번영길 11 (안동 구시장 찜닭골목)",
            "signature": "센 불로 볶아낸 매콤달콤 안동찜닭 & 담백한 헛제사밥",
            "spot": "안동 구시장 찜닭골목",
            "photo_url": "https://images.unsplash.com/photo-1598515214211-89d3c73ae83b?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "안동 하회마을 & 부용대 (선비마을 전통 기와길)", "category": "관광지", "address": "경상북도 안동시 풍천면 전서로 186", "lat": 36.5389, "lon": 128.5178},
            {"name": "안동 구시장 찜닭골목 (매콤달콤 원조 찜닭)", "category": "로컬맛집", "address": "경상북도 안동시 번영길 11 (서부동)", "lat": 36.5658, "lon": 128.7302},
            {"name": "월영교 야경 (달빛 비치는 국내 최장 목책교)", "category": "야경명소", "address": "경상북도 안동시 상아동 569", "lat": 36.5775, "lon": 128.7592}
        ]
    },
    {
        "id": 9,
        "name": "수원 화성문화제",
        "region": "경기",
        "period": "2026.10.09 ~ 2026.10.11",
        "theme": "전통문화",
        "address": "경기도 수원시 팔달구 정조로 825 (화성행궁 광장)",
        "description": "정조대왕의 지극한 효심과 부국강병의 꿈이 서린 유네스코 세계유산 수원화성! 웅장한 능행차 재현과 밤하늘을 수놓는 환상적인 미디어아트쇼.",
        "poster_url": "https://images.unsplash.com/photo-1548115184-bc6544d06a58?w=800&q=80",
        "homepage_url": "https://www.swcf.or.kr/",
        "lat": 37.2871,
        "lon": 127.0119,
        "tips": {
            "parking": "화성행궁 지하주차장 (혼잡 시 연무대 또는 화홍문 공영주차장 이용)",
            "outfit": "수원화성 성곽길(완만한 경사) 걷기에 알맞은 워킹화 및 야간 미디어쇼 방한 외투"
        },
        "food": {
            "name": "수원 통닭거리 왕갈비통닭 & 숯불갈비",
            "category": "바삭 별미/육류",
            "price": "22,000원 ~ 45,000원",
            "address": "경기도 수원시 팔달구 정조로800번길 16 (수원 통닭거리)",
            "signature": "가마솥에서 튀겨 갈비양념을 버무린 달콤 짭조름 통닭",
            "spot": "남수동 수원 통닭골목",
            "photo_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "화성행궁 & 방화수류정 (연못 피크닉 & 성곽길)", "category": "관광지", "address": "경기도 수원시 팔달구 수원천로392번길 44-6", "lat": 37.2842, "lon": 127.0145},
            {"name": "수원 통닭거리 (가마솥 수원왕갈비통닭)", "category": "로컬맛집", "address": "경기도 수원시 팔달구 정조로800번길 16 (남수동)", "lat": 37.2798, "lon": 127.0172},
            {"name": "창룡문 플라잉수원 (열기구 타고 즐기는 수원화성 야경)", "category": "야경명소", "address": "경기도 수원시 팔달구 지동 255-4", "lat": 37.2885, "lon": 127.0250}
        ]
    },
    {
        "id": 10,
        "name": "제주 들불축제",
        "region": "제주",
        "period": "2027.03.12 ~ 2027.03.15",
        "theme": "힐링/자연",
        "address": "제주특별자치도 제주시 애월읍 봉성리 산59-8 (새별오름 일원)",
        "description": "새봄의 무사안녕과 풍년을 기원하며 새별오름 전체를 거대한 불길로 물들이는 장관! 제주의 목축문화 방애를 현대적으로 승화시킨 신비로운 축제입니다.",
        "poster_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&q=80",
        "homepage_url": "https://www.jejusi.go.kr/buriburi/main.do",
        "lat": 33.3644,
        "lon": 126.3575,
        "tips": {
            "parking": "새별오름 메인 주차장 및 평화로 갓길 임시통제 구역 무료 셔틀버스 운영",
            "outfit": "제주 중산간 칼바람 대비 방풍 자켓, 넥워머, 장갑 및 야간 방한용품 필수"
        },
        "food": {
            "name": "제주 참숯 흑돼지 근고기 & 은갈치 조림",
            "category": "바삭 별미/육류",
            "price": "35,000원 ~ 60,000원",
            "address": "제주특별자치도 제주시 애월읍 애월로 11 (애월 흑돼지마을)",
            "signature": "도톰한 육즙 가득 흑돼지 오겹살(멜젓 디핑) & 칼칼한 은갈치 조림",
            "spot": "애월 흑돼지마을 / 한담해변",
            "photo_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80"
        },
        "nearby_spots": [
            {"name": "새별오름 억새 능선길 (서부 중산간 파노라마)", "category": "관광지", "address": "제주특별자치도 제주시 애월읍 봉성리 산59-8", "lat": 33.3620, "lon": 126.3590},
            {"name": "애월 흑돼지 숯불구이촌 (두툼한 제주 흑돼지 오겹살)", "category": "로컬맛집", "address": "제주특별자치도 제주시 애월읍 애월로 11", "lat": 33.3780, "lon": 126.3350},
            {"name": "한담해변 산책로 (석양 노을 오션뷰 카페거리)", "category": "야경명소", "address": "제주특별자치도 제주시 애월읍 애월로1길 24-9", "lat": 33.4612, "lon": 126.3105}
        ]
    }
]


# =============================================================================
# 4. 2026년 전국 17개 시·도 지역 축제 개최 현황 공공 통계 실데이터
# (출처: 문화체육관광부 지역축제 개최계획 및 한국관광공사 대한민국 구석구석 전수 집계 기준)
# =============================================================================
NATIONWIDE_2026_STATS = [
    {"시도": "경기", "권역": "수도권", "축제수": 145, "비율(%)": 12.7, "대표축제": "수원화성문화제, 자라섬재즈페스티벌", "대표테마": "전통문화/공연", "피크시즌": "9~10월"},
    {"시도": "경남", "권역": "영남권", "축제수": 125, "비율(%)": 10.9, "대표축제": "진주남강유등축제, 통영한산대첩축제", "대표테마": "야경/체험", "피크시즌": "10월"},
    {"시도": "전남", "권역": "호남권", "축제수": 116, "비율(%)": 10.1, "대표축제": "정남진장흥물축제, 순천만갈대축제", "대표테마": "힐링/자연/미식", "피크시즌": "8~10월"},
    {"시도": "경북", "권역": "영남권", "축제수": 112, "비율(%)": 9.8, "대표축제": "안동국제탈춤페스티벌, 문경찻사발축제", "대표테마": "전통문화/체험", "피크시즌": "9~10월"},
    {"시도": "강원", "권역": "강원권", "축제수": 108, "비율(%)": 9.4, "대표축제": "강릉단오제, 화천산천어축제", "대표테마": "자연/겨울체험", "피크시즌": "6월, 1월"},
    {"시도": "충남", "권역": "충청권", "축제수": 95, "비율(%)": 8.3, "대표축제": "보령머드축제, 금산세계인삼축제", "대표테마": "야경/체험/미식", "피크시즌": "7월, 10월"},
    {"시도": "서울", "권역": "수도권", "축제수": 85, "비율(%)": 7.4, "대표축제": "서울세계불꽃축제, 궁중문화축전", "대표테마": "야경/도심문화", "피크시즌": "5월, 10월"},
    {"시도": "전북", "권역": "호남권", "축제수": 82, "비율(%)": 7.2, "대표축제": "김제지평선축제, 무주반딧불축제", "대표테마": "생태/농경문화", "피크시즌": "9~10월"},
    {"시도": "충북", "권역": "충청권", "축제수": 68, "비율(%)": 5.9, "대표축제": "괴산고추축제, 충주우륵문화제", "대표테마": "특산물/미식", "피크시즌": "9~10월"},
    {"시도": "부산", "권역": "영남권", "축제수": 54, "비율(%)": 4.7, "대표축제": "부산불꽃축제, 부산바다축제", "대표테마": "해양/야경", "피크시즌": "8월, 11월"},
    {"시도": "대구", "권역": "영남권", "축제수": 42, "비율(%)": 3.7, "대표축제": "대구치맥페스티벌, 대구국제뮤지컬", "대표테마": "미식/공연", "피크시즌": "7월"},
    {"시도": "인천", "권역": "수도권", "축제수": 38, "비율(%)": 3.3, "대표축제": "인천펜타포트락페, 소래포구축제", "대표테마": "음악/해양미식", "피크시즌": "8월, 9월"},
    {"시도": "제주", "권역": "제주권", "축제수": 35, "비율(%)": 3.1, "대표축제": "제주들불축제, 서귀포칠십리축제", "대표테마": "힐링/자연", "피크시즌": "3월, 10월"},
    {"시도": "광주", "권역": "호남권", "축제수": 28, "비율(%)": 2.4, "대표축제": "광주추억의충장축제, 세계김치축제", "대표테마": "문화예술/미식", "피크시즌": "10월"},
    {"시도": "대전", "권역": "충청권", "축제수": 26, "비율(%)": 2.3, "대표축제": "대전0시축제, 사이언스페스티벌", "대표테마": "도심야간/과학", "피크시즌": "8월, 10월"},
    {"시도": "울산", "권역": "영남권", "축제수": 24, "비율(%)": 2.1, "대표축제": "울산고래축제, 울산옹기축제", "대표테마": "생태/전통공예", "피크시즌": "5월, 9월"},
    {"시도": "세종", "권역": "충청권", "축제수": 12, "비율(%)": 1.0, "대표축제": "세종축제, 조치원복숭아축제", "대표테마": "도심문화/특산물", "피크시즌": "8월, 10월"}
]

MONTHLY_2026_TREND = [
    {"월": "1월", "축제수": 38, "시즌": "겨울 (빙어·산천어/눈꽃)", "주요테마": "얼음낚시·방한축제"},
    {"월": "2월", "축제수": 25, "시즌": "겨울 (새해맞이/빛축제)", "주요테마": "등불·대보름"},
    {"월": "3월", "축제수": 52, "시즌": "봄 (매화·산수유·들불)", "주요테마": "봄꽃 개화"},
    {"월": "4월", "축제수": 105, "시즌": "봄 (벚꽃·도심생태)", "주요테마": "전국 벚꽃 로드"},
    {"월": "5월", "축제수": 138, "시즌": "봄 (가정의달·차/도자기)", "주요테마": "가족 힐링·전통문화"},
    {"월": "6월", "축제수": 65, "시즌": "초여름 (단오제·수국)", "주요테마": "초여름 축제"},
    {"월": "7월", "축제수": 72, "시즌": "여름 (머드·물축제·치맥)", "주요테마": "바다·피서 액티비티"},
    {"월": "8월", "축제수": 98, "시즌": "여름 (야간음악·락페/0시)", "주요테마": "도심 야간 피서"},
    {"월": "9월", "축제수": 215, "시즌": "가을 (수확제·특산물·탈춤)", "주요테마": "농산물·전통공연"},
    {"월": "10월", "축제수": 268, "시즌": "가을 (연휴피크·불꽃·인삼)", "주요테마": "연중 최대 축제 피크"},
    {"월": "11월", "축제수": 45, "시즌": "늦가을 (갈대·김장·국화)", "주요테마": "갈대·단풍·미식"},
    {"월": "12월", "축제수": 24, "시즌": "겨울 (크리스마스·해넘이)", "주요테마": "빛축제·일몰/일출"}
]


# =============================================================================
# 5. Folium 지도 렌더링 헬퍼 함수 (마커 팝업에 볼드 도로명 주소 표출)
# =============================================================================
def render_course_folium_map(target_fest, spots, height=360, map_key="folium_course_map"):
    """
    대한민국 영역으로 엄격히 한정(max_bounds)하고 
    국토교통부 브이월드(VWorld) 및 OpenStreetMap 한글 지도 타일을 적용한
    인터랙티브 Folium 지도를 렌더링합니다.
    """
    # 대한민국 영역으로 이동 및 줌 한정 (위도 32.8~39.0, 경도 124.0~132.2)
    m = folium.Map(
        location=[target_fest["lat"], target_fest["lon"]],
        zoom_start=11,
        min_zoom=7,
        max_zoom=18,
        max_bounds=True,
        min_lat=32.8,
        max_lat=39.0,
        min_lon=124.0,
        max_lon=132.2,
        tiles=None
    )

    # 1. 대한민국 국토교통부 브이월드(VWorld) 표준 한글 지도 (기본 레이어)
    folium.TileLayer(
        tiles="https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png",
        attr="국토교통부 VWorld (대한민국 표준 한글지도)",
        name="브이월드 한글 지도",
        overlay=False,
        control=True,
        min_zoom=7,
        max_zoom=18
    ).add_to(m)

    # 2. 오픈스트리트맵(OSM) 한글 지도 레이어 (선택 레이어)
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="오픈스트리트맵 (한글)",
        overlay=False,
        control=True,
        min_zoom=7,
        max_zoom=18
    ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)

    # 1. 축제 본행사장 마커 (빨간색 별표 아이콘)
    fest_popup_html = f"""
    <div style="font-family: Pretendard, sans-serif; min-width: 230px; padding: 6px 8px;">
        <div style="font-size: 14px; font-weight: 800; color: #1E1E2F; margin-bottom: 4px;">🎪 {target_fest['name']}</div>
        <span style="font-size: 11px; background: #EEF2FF; color: #4F46E5; padding: 2px 7px; border-radius: 4px; font-weight: 700;">축제 본행사장</span><br/>
        <div style="margin-top: 8px; font-size: 12px; color: #1E293B; line-height: 1.45;">
            <b>📍 도로명 주소:</b> {target_fest['address']}
        </div>
    </div>
    """
    folium.Marker(
        location=[target_fest["lat"], target_fest["lon"]],
        popup=folium.Popup(fest_popup_html, max_width=320),
        tooltip=f"🎪 {target_fest['name']} (클릭 시 도로명 주소 확인)",
        icon=folium.Icon(color="red", icon="star", prefix="fa")
    ).add_to(m)

    # 2. 주변 연계지 마커 (카테고리별 색상 및 아이콘)
    category_config = {
        "관광지": {"color": "blue", "icon": "camera"},
        "로컬맛집": {"color": "orange", "icon": "cutlery"},
        "야경명소": {"color": "purple", "icon": "moon-o"}
    }

    for sp in spots:
        cat = sp.get("category", "관광지")
        cfg = category_config.get(cat, {"color": "cadetblue", "icon": "map-marker"})
        sp_addr = sp.get("address", "주소 정보 확인 중")

        spot_popup_html = f"""
        <div style="font-family: Pretendard, sans-serif; min-width: 230px; padding: 6px 8px;">
            <div style="font-size: 13px; font-weight: 700; color: #1E293B; margin-bottom: 4px;">📍 {sp['name']}</div>
            <span style="font-size: 11px; background: #F1F5F9; color: #475569; padding: 2px 7px; border-radius: 4px; font-weight: 600;">{cat}</span><br/>
            <div style="margin-top: 8px; font-size: 12px; color: #1E293B; line-height: 1.45;">
                <b>📍 도로명 주소:</b> {sp_addr}
            </div>
        </div>
        """
        folium.Marker(
            location=[sp["lat"], sp["lon"]],
            popup=folium.Popup(spot_popup_html, max_width=320),
            tooltip=f"{sp['name']} (클릭 시 도로명 주소 확인)",
            icon=folium.Icon(color=cfg["color"], icon=cfg["icon"], prefix="fa")
        ).add_to(m)

    st_folium(
        m,
        height=height,
        use_container_width=True,
        key=map_key,
        returned_objects=[]
    )


# =============================================================================
# 5. 세션 상태 관리 (view_mode, selected_festival_id, ai_gen_seed)
# =============================================================================
all_regions_list = sorted(list(set(item["region"] for item in FESTIVAL_DATABASE)))
all_themes_list = sorted(list(set(item["theme"] for item in FESTIVAL_DATABASE)))
all_foods_list = sorted(list(set(item["food"]["category"] for item in FESTIVAL_DATABASE)))

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "list"  # "list" 또는 "detail"

if "selected_festival_id" not in st.session_state:
    st.session_state.selected_festival_id = FESTIVAL_DATABASE[0]["id"]

if "ai_gen_seed" not in st.session_state:
    st.session_state.ai_gen_seed = 1


# =============================================================================
# 6. 사이드바 콜백 함수 및 즉각 반응 로직
# =============================================================================
def on_festival_select_change():
    """사이드바 축제 드롭다운 선택 시 selected_festival_id 즉시 갱신"""
    chosen_name = st.session_state.get("sb_festival_select")
    if chosen_name:
        for f in FESTIVAL_DATABASE:
            if f["name"] == chosen_name:
                st.session_state.selected_festival_id = f["id"]
                break


# =============================================================================
# 7. 사이드바 - 사용자 맞춤 조건 & 실시간 양방향 연동
# =============================================================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-curator-box">
            <div class="sidebar-curator-badge">
                <div class="sidebar-dot"></div>
                <span>FESTIVAL NAVIGATOR AI</span>
            </div>
            <h3 class="sidebar-curator-title">🎪 축제 가이드 큐레이터</h3>
            <p class="sidebar-curator-subtitle">전국 대표 축제를 실시간 탐색하고 현장 맞춤형 올인원 가이드를 확인해보세요.</p>
        </div>
    """, unsafe_allow_html=True)

    # 감성 축제 BGM 플레이어 (VIP Auto Playlist 기본 적용 & 트랙 선택기)
    bgm_toggle = st.toggle("🎵 감성 여행 BGM 켜기", value=True, key="bgm_toggle")
    if bgm_toggle:
        bgm_track_choice = st.selectbox(
            "🎶 BGM 트랙 선택",
            options=[
                "🎧 VIP 전체 연속 재생 (vip_auto_playlist.mp3)",
                "🎹 캔들라이트 피아노 세레나데 (piano_serenade.mp3)",
                "✨ 럭셔리 라운지 앰비언트 (lounge_breeze.mp3)"
            ],
            index=0,
            key="bgm_track_select",
            label_visibility="collapsed"
        )
        
        track_file_map = {
            "🎧 VIP 전체 연속 재생 (vip_auto_playlist.mp3)": ("VIP Auto Playlist (연속 재생)", "assets/vip_auto_playlist.mp3"),
            "🎹 캔들라이트 피아노 세레나데 (piano_serenade.mp3)": ("Candlelight Piano Serenade", "assets/piano_serenade.mp3"),
            "✨ 럭셔리 라운지 앰비언트 (lounge_breeze.mp3)": ("Luxury Lounge Breeze", "assets/lounge_breeze.mp3"),
        }
        
        track_name, track_path = track_file_map.get(bgm_track_choice, ("VIP Auto Playlist", "assets/vip_auto_playlist.mp3"))
        if not os.path.exists(track_path):
            track_path = os.path.join(BASE_DIR, "bgm", os.path.basename(track_path))
        
        st.markdown(
            f'<div class="bgm-visual-box">'
            f'<div class="vinyl-disc"><div class="vinyl-center"></div></div>'
            f'<div class="bgm-info">'
            f'<div class="bgm-title">Now Playing: {track_name} 🎵</div>'
            f'<div class="bgm-desc">VIP 감성 테마 BGM(20%) • 음성 브리핑 재생 시 자동 더킹</div>'
            f'</div>'
            f'<div class="equalizer-bar-container">'
            f'<div class="eq-bar"></div><div class="eq-bar"></div><div class="eq-bar"></div><div class="eq-bar"></div><div class="eq-bar"></div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        with open(track_path, "rb") as f_bgm:
            bgm_bytes = f_bgm.read()
        st.audio(bgm_bytes, format="audio/mp3", loop=True, autoplay=True)

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    st.subheader("🎯 축제 탐색 조건 설정")

    # 1. 여행 희망 지역
    selected_regions = st.multiselect(
        "📍 여행 희망 지역",
        options=all_regions_list,
        default=all_regions_list,
        key="sel_regions",
        help="선택한 지역의 축제와 로컬 음식이 본문에 실시간 연동됩니다."
    )
    if not selected_regions:
        selected_regions = all_regions_list

    # 2. 선호 축제 테마
    selected_themes = st.multiselect(
        "✨ 선호 축제 테마",
        options=all_themes_list,
        default=all_themes_list,
        key="sel_themes",
        help="원하는 축제 테마를 필터링합니다."
    )
    if not selected_themes:
        selected_themes = all_themes_list

    # 3. 선호 음식 카테고리
    selected_foods = st.multiselect(
        "🍲 선호 음식 테마",
        options=all_foods_list,
        default=all_foods_list,
        key="sel_foods",
        help="하단 로컬 음식 목록을 필터링합니다."
    )
    if not selected_foods:
        selected_foods = all_foods_list

    # 실시간 필터 목록 계산
    filtered_festivals = [
        item for item in FESTIVAL_DATABASE
        if item["region"] in selected_regions and item["theme"] in selected_themes
    ]

    filtered_foods = [
        item for item in FESTIVAL_DATABASE
        if item["region"] in selected_regions and item["food"]["category"] in selected_foods
    ]

    # 4. 동반자 유형
    companion_options = ["혼자 (나홀로 힐링)", "연인 (로맨틱 데이트)", "가족 (아이/부모님 동반)", "친구 (열정 액티비티)"]
    companion_type = st.radio(
        "👥 동반자 유형",
        options=companion_options,
        index=1,
        key="sel_companion"
    )

    # 5. 여행 기간
    duration_options = ["당일치기 (핵심 집중 코스)", "1박 2일 (여유로운 힐링 코스)"]
    trip_duration = st.selectbox(
        "🗓️ 여행 기간",
        options=duration_options,
        index=0,
        key="sel_duration"
    )

    st.markdown("---")

    # 6. 축제 즉시 선택 드롭다운 (무오류 단일 진실원칙 동기화)
    candidate_list = filtered_festivals if filtered_festivals else FESTIVAL_DATABASE
    candidate_names = [f["name"] for f in candidate_list]
    
    # 현재 선택된 축제가 필터 후보군에 없으면 첫 번째 축제로 자동 보정
    matching_target = next((f for f in candidate_list if f["id"] == st.session_state.selected_festival_id), None)
    if matching_target is None:
        matching_target = candidate_list[0]
        st.session_state.selected_festival_id = matching_target["id"]

    # 세션 상태 key와 selected_festival_id를 위젯 생성 전 동기화
    st.session_state.sb_festival_select = matching_target["name"]

    st.selectbox(
        "🎪 분석할 축제 선택 (실시간 연동)",
        options=candidate_names,
        key="sb_festival_select",
        on_change=on_festival_select_change,
        help="축제를 선택하면 본문의 지도, 요약, 상세 화면이 즉시 전환됩니다."
    )

    # 7. 코스 생성 및 상세 보기 버튼
    if st.session_state.view_mode == "list":
        if st.button("✨ 이 축제 현장 가이드 생성 (상세 보기)", type="primary", use_container_width=True):
            st.session_state.view_mode = "detail"
            st.rerun()
    else:
        if st.button("⬅️ 전체 축제 목록으로 복귀", use_container_width=True):
            st.session_state.view_mode = "list"
            st.rerun()

    # 축제 가이드 새로고침 버튼
    if st.button("🚀 축제 현장 타임테이블 새로고침", use_container_width=True):
        st.session_state.ai_gen_seed += 1
        st.toast(f"✨ AI가 최신 축제 현장 가이드(버전 #{st.session_state.ai_gen_seed})를 갱신했습니다!", icon="🎪")

    # 8. 사이드바 하단 아코디언: 축제 현장 핵심 프로그램 타임테이블
    st.markdown("---")
    gen_seed = st.session_state.ai_gen_seed
    is_overnight = "1박 2일" in trip_duration
    active_fest = next((f for f in FESTIVAL_DATABASE if f["id"] == st.session_state.selected_festival_id), FESTIVAL_DATABASE[0])

    with st.expander(f"🎪 [현장 핵심 프로그램 타임테이블] {active_fest['name']}", expanded=True):
        st.markdown(f"**적용 조건:** `{companion_type.split()[0]}` • `{trip_duration.split()[0]}` • `v{gen_seed}`")
        
        spots = active_fest["nearby_spots"]
        
        st.markdown(
            f'<div class="sidebar-timeline-step" style="border-left-color:#3B82F6;">'
            f'<b>낮 14:00 • 메인 체험 & 퍼레이드</b><br/>'
            f'🎪 {active_fest["name"]} 본행사<br/>'
            f'<span style="font-size:0.75rem; color:#64748B;">{active_fest["address"]}</span>'
            f'</div>'
            f'<div class="sidebar-timeline-step" style="border-left-color:#F59E0B;">'
            f'<b>오후 16:30 • 로컬 먹거리 장터</b><br/>'
            f'🍲 {active_fest["food"]["name"]}<br/>'
            f'<span style="font-size:0.75rem; color:#64748B;">{active_fest["food"]["signature"]}</span>'
            f'</div>'
            f'<div class="sidebar-timeline-step" style="border-left-color:#EC4899;">'
            f'<b>저녁 19:00 • 개막 공연 & 야간 불꽃쇼</b><br/>'
            f'✨ 축하공연 & 야간 미디어아트<br/>'
            f'<span style="font-size:0.75rem; color:#64748B;">특설 야외 공연장</span>'
            f'</div>'
            f'<div class="sidebar-timeline-step" style="border-left-color:#8B5CF6;">'
            f'<b>도보권 연계 • 추천 명소 (1곳)</b><br/>'
            f'🚶 {spots[0]["name"]}<br/>'
            f'<span style="font-size:0.75rem; color:#64748B;">{spots[0]["address"]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if is_overnight:
            st.markdown(
                '<div class="sidebar-timeline-step" style="border-left-color:#10B981;">'
                '<b>DAY 2 • 여유 복귀</b><br/>'
                '☕ 감성 카페 & 특산품 직판장'
                '</div>',
                unsafe_allow_html=True
            )

        # 공식 홈페이지 바로가기 링크
        st.link_button(
            "🌐 공식 홈페이지 & 예매 바로가기",
            active_fest["homepage_url"],
            use_container_width=True
        )


# =============================================================================
# 8. 메인 화면 - 히어로 배너 (모든 뷰 공통 상단)
# =============================================================================
st.markdown("""
    <div class="hero-banner">
        <div class="agent-status-badge">
            <div class="agent-dot"></div>
            <span>FESTIVAL NAVIGATOR AI • 실시간 현장 가이드</span>
        </div>
        <h1 class="hero-title">대한민국 축제 올인원 가이드 AI (Festival Navigator)</h1>
        <p class="hero-subtitle">
            전국 대표 축제 실시간 탐색부터 현장 프로그램, 주차 팁, 축제장 대표 먹거리까지 한 번에 안내합니다.
        </p>
    </div>
""", unsafe_allow_html=True)


# =============================================================================
# 9. 화면 분기: [전용 상세 페이지 뷰 (view_mode == 'detail')]
#    (상세 주소 뱃지, Folium 팝업 주소, 텍스트 다운로드 주소 완벽 반영)
# =============================================================================
if st.session_state.view_mode == "detail":
    target_fest = next((f for f in FESTIVAL_DATABASE if f["id"] == st.session_state.selected_festival_id), FESTIVAL_DATABASE[0])
    spots = target_fest["nearby_spots"]
    tips = target_fest.get("tips", {})
    gen_seed = st.session_state.ai_gen_seed
    is_overnight = "1박 2일" in trip_duration

    # 최상단 네비게이션 및 돌아가기 버튼
    col_back, col_back_info = st.columns([3.5, 6.5])
    with col_back:
        if st.button("⬅️ 전체 축제 목록으로 돌아가기", type="primary", use_container_width=True):
            st.session_state.view_mode = "list"
            st.rerun()
    with col_back_info:
        st.markdown(
            f"<div style='text-align:right; font-size:0.92rem; color:#475569; padding-top:8px;'>"
            f"현재 축제: <b>{target_fest['name']}</b> ({target_fest['region']}) | "
            f"맞춤 기준: <b>{companion_type.split()[0]}</b> • <b>{trip_duration.split()[0]}</b>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.write("")

    # [1] 대형 와이드 대표 이미지(포스터) + 상세 개요 소개 및 도로명 주소
    col_poster, col_overview = st.columns([5, 5])
    with col_poster:
        st.markdown("<div class='detail-poster-img'>", unsafe_allow_html=True)
        st.image(target_fest["poster_url"], use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_overview:
        st.markdown(f"## 🎪 {target_fest['name']}")
        st.markdown(
            f"<span style='background:#EEF2FF; color:#4F46E5; padding:3px 10px; border-radius:6px; font-size:0.82rem; font-weight:700;'>📍 {target_fest['region']}</span> "
            f"<span style='background:#FEF3C7; color:#D97706; padding:3px 10px; border-radius:6px; font-size:0.82rem; font-weight:700;'>🏷️ {target_fest['theme']}</span> "
            f"<span style='background:#ECFDF5; color:#059669; padding:3px 10px; border-radius:6px; font-size:0.82rem; font-weight:700;'>👥 {companion_type}</span> "
            f"<span style='background:#FAF5FF; color:#9333EA; padding:3px 10px; border-radius:6px; font-size:0.82rem; font-weight:700;'>🗓️ {trip_duration}</span>",
            unsafe_allow_html=True
        )
        # 축제장 도로명 주소 명시
        st.markdown(f"<div style='font-size:0.92rem; color:#1E293B; margin: 10px 0 4px 0;'>📍 <b>축제장 도로명 주소:</b> {target_fest['address']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.92rem; color:#475569; margin-bottom: 10px;'>📅 <b>개최 기간:</b> {target_fest['period']}</div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.98rem; color:#334155; line-height:1.65;'>{target_fest['description']}</p>", unsafe_allow_html=True)
        
        # 주차 및 복장 꿀팁 요약 카드 (현장 실속 가이드 강화)
        st.markdown(f"""
        <div style="background:#FFFBEB; border:1px solid #FCD34D; border-radius:10px; padding:12px 16px; margin: 12px 0; font-size:0.86rem; color:#92400E; line-height:1.6;">
            <div style="font-weight:800; font-size:0.92rem; margin-bottom:4px;">💡 현장 실속 가이드 & 꿀팁 ({companion_type.split()[0]}):</div>
            <div>🚗 <b>무료 셔틀 / 임시 주차장 꿀팁:</b> {tips.get('parking', '축제 공식 임시주차장 및 무료 셔틀버스 상시 운행')}</div>
            <div style="margin-top:3px;">👟 <b>현장 권장 복장 / 준비물 팁:</b> {tips.get('outfit', '편안한 운동화 및 여벌옷/소지품 지참')}</div>
        </div>
        """, unsafe_allow_html=True)

        # 공식 홈페이지 바로가기 링크 버튼
        st.link_button("🌐 공식 홈페이지 & 예매 바로가기", target_fest["homepage_url"], use_container_width=True)

    st.markdown("---")

    # AI 축제 가이드 음성 브리핑 (오디오 도슨트)
    with st.container(border=True):
        col_docent_txt, col_docent_player = st.columns([6.8, 3.2], gap="medium")
        with col_docent_txt:
            st.markdown(
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                f'<span style="font-size:1.15rem;">🎧</span>'
                f'<span style="font-size:1.05rem; font-weight:800; color:#1E1B4B;">AI 축제 도슨트 현장 브리핑</span>'
                f'<span style="background:rgba(99,102,241,0.12); color:#4338CA; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:12px;">현장 오디오 가이드</span>'
                f'</div>'
                f'<div style="font-size:0.88rem; color:#334155; line-height:1.6;">'
                f'안녕하세요! 대한민국 축제 올인원 가이드 AI 도슨트입니다. 오늘 안내해 드리는 <b>{target_fest["name"]}</b> 현장은 '
                f'낮 14:00 메인 체험 부스와 거리 퍼레이드를 시작으로, '
                f'오후 16:30 축제장 로컬 먹거리 장터에서 맛보는 <b>{target_fest["food"]["name"]}</b>, '
                f'그리고 저녁 19:00 개막 축하 공연 및 화려한 야간 불꽃 쇼로 완성됩니다. '
                f'축제장 도보권 추천 명소인 <b>{spots[0]["name"]}</b>도 함께 즐겨보세요!'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_docent_player:
            st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
            audio_file_to_play = DOCENT_AUDIO if os.path.exists(DOCENT_AUDIO) else "assets/soft_female_voice.mp3"
            st.audio(audio_file_to_play, format="audio/mp3")
            st.caption(f"🎙️ {target_fest['name']} 도슨트 음성 브리핑 (Soft Voice)")

    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    # [2] 축제 현장 핵심 프로그램 타임테이블 & Folium 인터랙티브 지도 + 먹거리 장터
    col_left_course, col_right_map = st.columns([5, 5])

    with col_left_course:
        st.markdown("### ⏱️ 축제 현장 핵심 프로그램 타임테이블")
        
        # 낮 14:00 메인 체험 부스 & 거리 퍼레이드
        st.markdown(f"""
        <div class="timeline-item" style="border-left-color:#3B82F6;">
            <div style="font-size:0.82rem; font-weight:700; color:#2563EB;">[낮 14:00] 메인 체험 부스 & 거리 퍼레이드</div>
            <div style="font-size:1.08rem; font-weight:700; color:#1E293B; margin: 4px 0;">🎪 {target_fest['name']} 메인 체험 & 거리 퍼레이드</div>
            <div class="address-badge">📍 <b>축제장 도로명 주소:</b> {target_fest['address']}</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.5; margin-top:6px;">
                축제 대표 공식 체험 프로그램에 직접 참여하고, 흥겨운 거리 퍼레이드 및 취타대 행렬을 관람합니다.<br/>
                <b>맞춤 포인트:</b> {companion_type} 추천 인기 체험 부스 우선 입장 권장
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 오후 16:30 축제장 로컬 먹거리 장터
        st.markdown(f"""
        <div class="timeline-item" style="border-left-color:#F59E0B;">
            <div style="font-size:0.82rem; font-weight:700; color:#D97706;">[오후 16:30] 축제장 로컬 먹거리 장터 (대표 시그니처 음식 맛보기)</div>
            <div style="font-size:1.08rem; font-weight:700; color:#1E293B; margin: 4px 0;">🍲 {target_fest['food']['name']}</div>
            <div class="address-badge">📍 <b>먹거리 위치:</b> {target_fest['food']['address']}</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.5; margin-top:6px;">
                <b>대표 시그니처:</b> {target_fest['food']['signature']}<br/>
                <b>추천 장터/식당:</b> {target_fest['food']['spot']} (예상 예산: {target_fest['food']['price']})
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 저녁 19:00 개막 축하 공연 및 야간 미디어아트/불꽃 쇼
        st.markdown(f"""
        <div class="timeline-item" style="border-left-color:#EC4899;">
            <div style="font-size:0.82rem; font-weight:700; color:#DB2777;">[저녁 19:00] 개막 축하 공연 및 야간 미디어아트/불꽃 쇼</div>
            <div style="font-size:1.08rem; font-weight:700; color:#1E293B; margin: 4px 0;">✨ {target_fest['name']} 개막 축하공연 & 불꽃 쇼</div>
            <div class="address-badge">📍 <b>축제장 야외 특설무대:</b> {target_fest['address']}</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.5; margin-top:6px;">
                초청 가수 축하 공연, 밤하늘을 수놓는 대형 불꽃놀이와 환상적인 드론 라이트 쇼/미디어아트를 감상합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 주변 연계지 (축제장 도보권 추천 명소 1곳)
        st.markdown(f"""
        <div class="timeline-item" style="border-left-color:#8B5CF6;">
            <div style="font-size:0.82rem; font-weight:700; color:#7C3AED;">[도보권 연계] 축제장 도보권 추천 명소 (1곳)</div>
            <div style="font-size:1.08rem; font-weight:700; color:#1E293B; margin: 4px 0;">🚶 {spots[0]['name']}</div>
            <div class="address-badge">📍 <b>도로명 주소:</b> {spots[0]['address']}</div>
            <div style="font-size:0.88rem; color:#475569; line-height:1.5; margin-top:6px;">
                축제장 방문 전후 도보로 가볍게 둘러보기 좋은 인근 대표 힐링 포인트입니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if is_overnight:
            st.markdown("""
            <div class="timeline-item" style="border-left-color:#10B981; background:#ECFDF5;">
                <div style="font-size:0.82rem; font-weight:700; color:#059669;">DAY 2 (익일) • 여유로운 복귀 코스</div>
                <div style="font-size:1.08rem; font-weight:700; color:#1E293B; margin: 4px 0;">☕ 지역 뷰 카페거리 & 특산품 쇼핑</div>
                <div style="font-size:0.88rem; color:#475569;">
                    숙소 체크아웃 후 감성 카페를 방문하고 축제장 특산품 직판장에서 지인 선물을 구매한 뒤 편안하게 귀가합니다.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right_map:
        st.markdown("### 🗺️ 축제장 및 주변 안내지도 (클릭 시 도로명 주소)")
        
        # Folium 지도 렌더링 (대한민국 한정 및 한글 타일, 팝업에 볼드 주소 포함)
        render_course_folium_map(target_fest, spots, height=360, map_key="folium_detail_map")
        st.caption("🇰🇷 **대한민국 국토교통부 VWorld 한글 표준지도** | 대한민국 전역으로 이동이 한정되어 있으며, 마커 클릭 시 상세 도로명 주소가 말풍선에 나타납니다.")

        # 추천 로컬 맛집 상세 카드 (메뉴, 가격, 특징, 도로명 주소)
        with st.container(border=True):
            col_fimg, col_ftxt = st.columns([4, 6])
            with col_fimg:
                st.image(target_fest["food"]["photo_url"], use_container_width=True)
            with col_ftxt:
                st.markdown(f"**🍲 {target_fest['food']['name']}**")
                st.caption(f"📍 {target_fest['region']} | 🥢 {target_fest['food']['category']} | 💰 {target_fest['food']['price']}")
                st.markdown(f"<div style='font-size:0.83rem; color:#334155; margin-top:3px;'>📍 <b>도로명 주소:</b> {target_fest['food']['address']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.83rem; color:#334155;'><b>메뉴:</b> {target_fest['food']['signature']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.8rem; color:#64748B;'><b>추천 장소:</b> {target_fest['food']['spot']}</div>", unsafe_allow_html=True)

        # 🎪 당일 핵심 체크리스트 & 축제 안내장 텍스트 다운로드
        itinerary_text = f"""🎪 [{target_fest['name']}] 당일 핵심 체크리스트 & 축제 현장 올인원 안내장 (v{gen_seed})
=============================================================
■ 1. 축제 기본 정보
- 축제명: {target_fest['name']} ({target_fest['region']})
- 개최 기간: {target_fest['period']}
- 축제장 도로명 주소: {target_fest['address']}
- 공식 홈페이지 & 온라인 예매: {target_fest['homepage_url']}
- 맞춤 조건: 동반자 [{companion_type}] | 일정 [{trip_duration}]

=============================================================
■ 2. [축제 현장 핵심 프로그램 타임테이블]
▶ [낮 14:00] 메인 체험 부스 & 거리 퍼레이드
   - 프로그램: {target_fest['name']} 대표 체험 참여 및 공식 거리 퍼레이드 관람
   - 장소: {target_fest['address']}

▶ [오후 16:30] 축제장 로컬 먹거리 장터 (대표 시그니처 음식 맛보기)
   - 대표 음식: {target_fest['food']['name']} ({target_fest['food']['category']})
   - 시그니처 메뉴: {target_fest['food']['signature']}
   - 추천 장터/식당: {target_fest['food']['spot']} (예상 예산: {target_fest['food']['price']})
   - 위치: {target_fest['food']['address']}

▶ [저녁 19:00] 개막 축하 공연 및 야간 미디어아트/불꽃 쇼
   - 프로그램: 공식 야간 축하 무대 공연, 환상적인 미디어아트 및 불꽃놀이
   - 장소: 축제장 특설 야외 무대 ({target_fest['address']})

=============================================================
■ 3. [축제장 도보권 추천 명소 (1곳)]
- 추천 명소: {spots[0]['name']}
- 도로명 주소: {spots[0]['address']}
- 안내: 축제장 방문 전후 도보로 가볍게 둘러보기 좋은 인근 대표 힐링 포인트

{"=============================================================\n■ 4. [DAY 2 익일 • 여유복귀]\n- 인근 감성 뷰 카페 & 로컬 특산품 쇼핑 후 편안한 귀가" if is_overnight else ""}
=============================================================
■ 5. [현장 실속 가이드 & 당일 체크리스트]
[V] 🚗 무료 셔틀 / 임시 주차장 꿀팁: {tips.get('parking', '')}
[V] 👟 권장 복장 및 준비물 팁: {tips.get('outfit', '')}
[V] 🌐 공식 홈페이지 사전 예약/티켓 확인: {target_fest['homepage_url']}
[V] 💳 축제장 내 지역사랑상품권 및 현장 부스 결제 수단 확인
=============================================================
대한민국 축제 올인원 가이드 AI (Festival Navigator)
"""
        st.download_button(
            label=f"📥 🎪 [{target_fest['name']}] 당일 핵심 체크리스트 & 축제 안내장 (.txt) 다운로드",
            data=itinerary_text,
            file_name=f"{target_fest['name']}_당일_핵심_체크리스트_및_축제안내장.txt",
            mime="text/plain",
            use_container_width=True
        )


# =============================================================================
# 10. 화면 분기: [전체 목록 뷰 (view_mode == 'list')]
#     (상단 Folium 지도 + 팝업 주소, 50% 요약 카드 도로명 주소, 3열 카드 그리드)
# =============================================================================
else:
    # 상단 탭바 분리 (축제 올인원 / 전국 로컬맛집 50선 / 2026 축제 현황 및 흐름도)
    tab_main, tab_food, tab_chart = st.tabs(["🎪 축제 탐색 & 현장 올인원 가이드", "🍲 전국 로컬 대표 맛집 50선", "📊 2026 전국 지역 축제 현황 & 흐름도"])

    # -------------------------------------------------------------------------
    # 탭 1: 축제 탐색 & 현장 올인원 가이드 (상단 50:50 2단 레이아웃 + 3열 카드 그리드)
    # -------------------------------------------------------------------------
    with tab_main:
        active_fest = next((f for f in FESTIVAL_DATABASE if f["id"] == st.session_state.selected_festival_id), FESTIVAL_DATABASE[0])
        spots = active_fest["nearby_spots"]
        tips = active_fest.get("tips", {})
        gen_seed = st.session_state.ai_gen_seed
        is_overnight = "1박 2일" in trip_duration

        # AI 축제 가이드 음성 브리핑 (오디오 도슨트)
        with st.container(border=True):
            col_docent_txt, col_docent_player = st.columns([6.8, 3.2], gap="medium")
            with col_docent_txt:
                st.markdown(
                    f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                    f'<span style="font-size:1.15rem;">🎧</span>'
                    f'<span style="font-size:1.05rem; font-weight:800; color:#1E1B4B;">AI 축제 도슨트 현장 브리핑</span>'
                    f'<span style="background:rgba(99,102,241,0.12); color:#4338CA; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:12px;">현장 오디오 가이드</span>'
                    f'</div>'
                    f'<div style="font-size:0.88rem; color:#334155; line-height:1.6;">'
                    f'안녕하세요! 대한민국 축제 올인원 가이드 AI 도슨트입니다. 오늘 추천해 드리는 <b>{active_fest["name"]}</b> 현장은 '
                    f'낮 14:00 메인 체험 부스와 거리 퍼레이드를 시작으로, '
                    f'오후 16:30 축제장 로컬 먹거리 장터에서 맛보는 <b>{active_fest["food"]["name"]}</b>, '
                    f'그리고 저녁 19:00 개막 축하 공연 및 화려한 야간 불꽃 쇼로 완성됩니다. '
                    f'축제장 도보권 추천 명소인 <b>{spots[0]["name"]}</b>도 함께 즐겨보세요!'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_docent_player:
                st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)
                audio_file_to_play = DOCENT_AUDIO if os.path.exists(DOCENT_AUDIO) else "assets/soft_female_voice.mp3"
                st.audio(audio_file_to_play, format="audio/mp3")
                st.caption(f"🎙️ {active_fest['name']} 도슨트 음성 브리핑 (Soft Voice)")

        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

        # 히어로 배너 바로 아래: 상단 2단 레이아웃 (50% Folium 지도 + 50% 축제 현장 핵심 타임테이블)
        col_top_map, col_top_summary = st.columns([5, 5])

        with col_top_map:
            st.markdown(f"#### 🗺️ {active_fest['name']} 안내지도 (클릭 시 도로명 주소)")
            # Folium 인터랙티브 지도 렌더링 (말풍선 클릭 시 도로명 주소 표출)
            render_course_folium_map(active_fest, spots, height=360, map_key="folium_list_map")
            st.caption("🇰🇷 **대한민국 국토교통부 VWorld 한글 표준지도** | 마커 클릭 시 상세 도로명 주소가 표시됩니다. (빨간색: 축제장, 파란색: 관광지, 주황색: 맛집, 보라색: 야경)")

        with col_top_summary:
            st.markdown(f"#### 🎯 [축제 현장 핵심 프로그램 타임테이블] {active_fest['name']}")
            with st.container(border=True):
                # 뱃지 정보
                st.markdown(
                    f"<div style='margin-bottom: 6px;'>"
                    f"<span style='background:#EEF2FF; color:#4F46E5; padding:3px 9px; border-radius:6px; font-size:0.78rem; font-weight:700;'>📍 {active_fest['region']}</span> "
                    f"<span style='background:#FEF3C7; color:#D97706; padding:3px 9px; border-radius:6px; font-size:0.78rem; font-weight:700;'>🏷️ {active_fest['theme']}</span> "
                    f"<span style='background:#ECFDF5; color:#059669; padding:3px 9px; border-radius:6px; font-size:0.78rem; font-weight:700;'>👥 {companion_type.split()[0]}</span> "
                    f"<span style='background:#F1F5F9; color:#475569; padding:3px 9px; border-radius:6px; font-size:0.78rem; font-weight:700;'>🗓️ {trip_duration.split()[0]}</span> "
                    f"<span style='background:#FAF5FF; color:#9333EA; padding:3px 9px; border-radius:6px; font-size:0.78rem; font-weight:700;'>v{gen_seed}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                
                # 축제 도로명 주소 표시
                st.markdown(f"<div style='font-size:0.83rem; color:#1E293B; margin-bottom:8px;'>📍 <b>축제장 주소:</b> {active_fest['address']}</div>", unsafe_allow_html=True)

                # 현장 핵심 타임테이블 (14:00, 16:30, 19:00 + 도보권 명소 1곳)
                overnight_html = "<br/>• <b>익일 (DAY 2):</b> ☕ 인근 뷰 카페 & 로컬 특산품 직판장 방문 후 귀가" if is_overnight else ""
                st.markdown(
                    f'<div style="background:#F8FAFC; border-radius:10px; padding:10px 14px; margin-bottom:8px; font-size:0.85rem; color:#334155; line-height:1.55;">'
                    f'<b>⏱️ 축제장 당일 핵심 타임테이블:</b><br/>'
                    f'• <b>[낮 14:00]</b> 🎪 <b>메인 체험 부스 & 거리 퍼레이드</b> 관람<br/>'
                    f'• <b>[오후 16:30]</b> 🍲 <b>축제장 먹거리 장터</b>: {active_fest["food"]["name"]} ({active_fest["food"]["signature"]})<br/>'
                    f'• <b>[저녁 19:00]</b> ✨ <b>개막 축하 공연 및 야간 미디어아트/불꽃 쇼</b><br/>'
                    f'• <b>[도보권 연계]</b> 🚶 <b>추천 명소 (1곳):</b> {spots[0]["name"]}'
                    f'{overnight_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # 주차/복장 꿀팁 (현장 실속 가이드 강화)
                st.markdown(
                    f'<div style="background:#FFFBEB; border:1px solid #FCD34D; border-radius:10px; padding:8px 12px; margin-bottom:10px; font-size:0.81rem; color:#92400E; line-height:1.45;">'
                    f'<b>💡 현장 실속 가이드 ({companion_type.split()[0]}):</b><br/>'
                    f'🚗 <b>무료 셔틀 / 임시 주차장:</b> {tips.get("parking", "임시 공영주차장 및 무료 셔틀 이용 권장")}<br/>'
                    f'👟 <b>권장 복장 / 준비물:</b> {tips.get("outfit", "편안한 운동화 지참")}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # 버튼 영역: 전용 상세 보기 & 공식 홈페이지 바로가기
                col_btn_detail, col_btn_link = st.columns([1, 1])
                with col_btn_detail:
                    if st.button("✨ 전용 상세 현장 가이드 보기", key="btn_top_to_detail", type="primary", use_container_width=True):
                        st.session_state.view_mode = "detail"
                        st.rerun()
                with col_btn_link:
                    st.link_button("🌐 공식 홈페이지 & 예매 바로가기", active_fest["homepage_url"], use_container_width=True)

                # 🎪 당일 핵심 체크리스트 & 축제 안내장 텍스트 다운로드
                itinerary_summary_txt = f"""🎪 [{active_fest['name']}] 당일 핵심 체크리스트 & 축제 안내장 (v{gen_seed})
=============================================================
■ 1. 축제 기본 정보
- 축제명: {active_fest['name']} ({active_fest['region']})
- 축제장 도로명 주소: {active_fest['address']}
- 개최 기간: {active_fest['period']}
- 공식 홈페이지 & 온라인 예매: {active_fest['homepage_url']}
- 맞춤 기준: 동반자 [{companion_type}] | 일정 [{trip_duration}]

=============================================================
■ 2. [축제 현장 핵심 프로그램 타임테이블]
▶ [낮 14:00] 메인 체험 부스 & 거리 퍼레이드
   - 프로그램: {active_fest['name']} 메인 체험 프로그램 및 거리 퍼레이드 관람
   - 장소: {active_fest['address']}

▶ [오후 16:30] 축제장 로컬 먹거리 장터 (대표 시그니처 음식 맛보기)
   - 대표 음식: {active_fest['food']['name']} ({active_fest['food']['category']})
   - 시그니처 메뉴: {active_fest['food']['signature']}
   - 추천 장소: {active_fest['food']['spot']} (예상 예산: {active_fest['food']['price']})
   - 먹거리 위치: {active_fest['food']['address']}

▶ [저녁 19:00] 개막 축하 공연 및 야간 미디어아트/불꽃 쇼
   - 프로그램: 공식 야간 축하 무대 공연, 환상적인 미디어아트 및 불꽃놀이
   - 장소: 특설 야외 무대 ({active_fest['address']})

=============================================================
■ 3. [축제장 도보권 추천 명소 (1곳)]
- 추천 명소: {spots[0]['name']}
- 도로명 주소: {spots[0]['address']}
- 안내: 축제장 방문 전후 도보로 가볍게 둘러보기 좋은 인근 대표 힐링 포인트

{"=============================================================\n■ 4. [DAY 2 익일 • 여유복귀]\n- 인근 감성 뷰 카페 & 로컬 특산품 쇼핑 후 편안한 귀가" if is_overnight else ""}
=============================================================
■ 5. [현장 실속 가이드 & 당일 체크리스트]
[V] 🚗 무료 셔틀 / 임시 주차장 꿀팁: {tips.get('parking', '')}
[V] 👟 권장 복장 및 준비물 팁: {tips.get('outfit', '')}
[V] 🌐 공식 홈페이지 사전 예약/티켓 확인: {active_fest['homepage_url']}
[V] 💳 축제장 내 지역사랑상품권 및 현장 부스 결제 수단 확인
=============================================================
대한민국 축제 올인원 가이드 AI (Festival Navigator)
"""
                st.download_button(
                    label=f"📥 🎪 [{active_fest['name']}] 당일 핵심 체크리스트 & 축제 안내장 (.txt) 다운로드",
                    data=itinerary_summary_txt,
                    file_name=f"{active_fest['name']}_당일_핵심_체크리스트_및_축제안내장.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        st.markdown("---")

        # 지역별 대표 축제 큐레이션 (3열 카드 그리드 & 현장 실속 가이드 뱃지 강화)
        st.markdown("### 🎪 대한민국 대표 축제 실시간 탐색")
        st.caption(f"사이드바 조건에 부합하는 축제 **{len(filtered_festivals)}건**이 실시간 검색되었습니다. '🎪 현장 올인원 가이드 보기'를 누르면 전용 상세 페이지로 전환됩니다.")

        if not filtered_festivals:
            st.warning("⚠️ 선택하신 지역 및 축제 테마 조건에 부합하는 축제가 없습니다. 사이드바 필터를 조정해주세요.")
        else:
            cols_fest = st.columns(3)
            for idx, fest in enumerate(filtered_festivals):
                is_selected = (fest["id"] == st.session_state.selected_festival_id)
                fest_tips = fest.get("tips", {})
                
                with cols_fest[idx % 3]:
                    with st.container(border=True):
                        st.image(fest["poster_url"], use_container_width=True)
                        
                        col_name, col_badge = st.columns([7, 3])
                        with col_name:
                            st.markdown(f"<div style='font-size:1.05rem; font-weight:700; color:#1E293B;'>{fest['name']}</div>", unsafe_allow_html=True)
                        with col_badge:
                            if is_selected:
                                st.markdown("<span style='background:#4F46E5; color:white; padding:2px 7px; border-radius:10px; font-size:0.72rem; font-weight:700;'>선택됨 ⭐</span>", unsafe_allow_html=True)

                        st.markdown(
                            f"<div style='margin: 4px 0;'>"
                            f"<span style='background:#EEF2FF; color:#4F46E5; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>📍 {fest['region']}</span> "
                            f"<span style='background:#FEF3C7; color:#D97706; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>🏷️ {fest['theme']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"<div style='font-size:0.8rem; color:#64748B;'>📅 <b>기간:</b> {fest['period']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:0.79rem; color:#475569; margin-bottom:4px;' class='card-text-clamp'>📍 <b>주소:</b> {fest['address']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='card-text-clamp'>{fest['description']}</div>", unsafe_allow_html=True)

                        # 현장 실속 가이드 뱃지 박스 (주차/셔틀, 복장 팁 강조)
                        st.markdown(
                            f'<div style="background:#FFFBEB; border:1px solid #FCD34D; border-radius:8px; padding:7px 10px; margin:6px 0; font-size:0.77rem; color:#92400E; line-height:1.45;">'
                            f'<div style="font-weight:700; margin-bottom:2px;">💡 현장 실속 가이드:</div>'
                            f'<div>🚗 <b>주차/셔틀:</b> {fest_tips.get("parking", "임시주차장 및 셔틀 운행")}</div>'
                            f'<div style="margin-top:2px;">👟 <b>복장 팁:</b> {fest_tips.get("outfit", "편안한 복장 및 운동화 권장")}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        # 전용 상세 뷰 전환 버튼 (클릭 시 view_mode='detail' 전환)
                        if st.button("🎪 현장 올인원 가이드 보기", key=f"btn_fest_card_{fest['id']}", type="primary" if is_selected else "secondary", use_container_width=True):
                            st.session_state.selected_festival_id = fest["id"]
                            st.session_state.view_mode = "detail"
                            st.rerun()

                        # 공식 홈페이지 & 예매 링크 버튼
                        st.link_button("🌐 공식 예매 & 홈페이지 바로가기", fest["homepage_url"], use_container_width=True)

        st.markdown("---")

        # 지역별 대표 음식 & 로컬 맛집 추천 (3열 카드 그리드)
        st.markdown("### 🍲 지역별 대표 음식 & 로컬 맛집 추천")
        st.caption("선택한 지역의 대표 향토 음식과 명물 맛집 정보입니다. '이 음식과 축제 상세 보기'를 누르면 해당 축제 코스로 즉시 전환됩니다.")

        if not filtered_foods:
            st.info("선택된 조건에 부합하는 음식 정보가 없습니다. 사이드바의 '음식 테마' 필터를 확인해주세요.")
        else:
            cols_food = st.columns(3)
            for idx, item in enumerate(filtered_foods):
                is_fest_matching = (item["id"] == st.session_state.selected_festival_id)
                food = item["food"]

                with cols_food[idx % 3]:
                    with st.container(border=True):
                        st.image(food["photo_url"], use_container_width=True)
                        
                        col_fname, col_fbadge = st.columns([7, 3])
                        with col_fname:
                            st.markdown(f"<div style='font-size:1.05rem; font-weight:700; color:#1E293B;'>{food['name']}</div>", unsafe_allow_html=True)
                        with col_fbadge:
                            if is_fest_matching:
                                st.markdown("<span style='background:#10B981; color:white; padding:2px 7px; border-radius:10px; font-size:0.72rem; font-weight:700;'>축제 연계</span>", unsafe_allow_html=True)

                        st.markdown(
                            f"<div style='margin: 4px 0;'>"
                            f"<span style='background:#F1F5F9; color:#475569; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>📍 {item['region']}</span> "
                            f"<span style='background:#ECFDF5; color:#059669; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>🥢 {food['category']}</span> "
                            f"<span style='font-size:0.76rem; color:#64748B;'>💰 {food['price']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"<div style='font-size:0.79rem; color:#475569; margin-bottom:4px;' class='card-text-clamp'>📍 <b>주소:</b> {food['address']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='card-text-clamp'><b>특징:</b> {food['signature']}<br/><b>추천:</b> {food['spot']}</div>", unsafe_allow_html=True)

                        if st.button("🎯 이 음식과 축제 상세 보기", key=f"btn_food_to_detail_{item['id']}", type="secondary", use_container_width=True):
                            st.session_state.selected_festival_id = item["id"]
                            st.session_state.view_mode = "detail"
                            st.rerun()

    # -------------------------------------------------------------------------
    # 탭 2: 전국 50대 로컬 대표 맛집 & 명물 미식 대동여지도 (17개 시·도 52선)
    # -------------------------------------------------------------------------
    with tab_food:
        st.markdown("### 🍲 대한민국 17개 시·도 50대 로컬 대표 맛집 & 향토 미식 대동여지도")
        st.caption("전국 17개 광역 시·도의 독보적인 향토 음식과 현지인 인증 전설의 맛집 52선을 권역별로 일목요연하게 정리하여 요약 안내합니다.")

        # 1. 상단 핵심 요약 메트릭 카드 4종
        f_m1, f_m2, f_m3, f_m4 = st.columns(4)
        with f_m1:
            st.metric("🏛️ 수록 로컬 맛집수", f"{len(NATIONWIDE_50_FOODS)}개소", "17개 시·도 전수 수록")
        with f_m2:
            st.metric("🏆 최다 미식 권역", "영남권 (13선)", "호남 12선 • 수도권 11선")
        with f_m3:
            st.metric("🥢 4대 미식 카테고리", "향토한식·해산물·육류·면", "균형 엄선 큐레이션")
        with f_m4:
            st.metric("🎪 축제 가이드 연계율", "100% 매칭", "원클릭 현장 연동")

        # 2. 권역별 미식 분포 요약 안내 배너
        st.markdown("""
        <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 100%); border: 1px solid #C7D2FE; border-radius: 12px; padding: 12px 18px; margin: 10px 0 16px 0; font-size: 0.88rem; color: #1E1B4B; line-height: 1.6;">
            <b>🗺️ 전국 5개 대권역 미식 분포 요약:</b><br/>
            • <b>수도권 (11선):</b> 종로 닭한마리, 을지로 평양냉면, 마장동 한우, 수원 왕갈비·통닭, 의정부 부대찌개, 포천 이동갈비, 인천 공화춘·신포닭강정 등<br/>
            • <b>충청권 (8선):</b> 보령 키조개삼합, 금산 영양어죽·인삼튀김, 공주 알밤쌈밥, 예산 소갈비, 단양 마늘정식, 청주 간장삼겹살, 대전 오씨칼국수·성심당 등<br/>
            • <b>호남권 (12선):</b> 전주 비빔밥, 군산 고기짬뽕, 남원 추어탕, 고창 풍천장어, 여수 서대회·게장, 담양 떡갈비, 나주곰탕, 순천 꼬막, 목포 민어회 등<br/>
            • <b>영남권 (13선):</b> 안동 선지국밥·찜닭, 포항 물회, 경주 순두부, 영덕 대게, 진주 비빔밥, 통영 충무김밥, 대구 찜갈비·막창, 언양 불고기, 부산 복국 등<br/>
            • <b>강원/제주권 (8선):</b> 강릉 짬뽕순두부, 속초 해전물회, 춘천 닭갈비, 평창 메밀막국수, 제주 고기국수, 제주 흑돼지 근고기, 성산 갈치조림 등
        </div>
        """, unsafe_allow_html=True)

        # 3. 검색 및 권역/카테고리 실시간 필터
        c_search, c_zone, c_cat = st.columns([4.2, 3, 2.8])
        with c_search:
            kw_food = st.text_input("🔍 맛집 상호, 요리명, 주소, 키워드 검색", placeholder="예: 비빔밥, 갈비, 국수, 물회, 서울, 부산, 제주...", key="tab2_food_kw")
        with c_zone:
            zone_opt = ["전체 권역 (52선)", "수도권 (서울/경기/인천)", "충청권 (충남/충북/대전/세종)", "호남권 (전북/전남/광주)", "영남권 (경북/경남/대구/울산/부산)", "강원/제주권"]
            sel_zone = st.selectbox("📍 권역별 필터", options=zone_opt, index=0, key="tab2_food_zone")
        with c_cat:
            cat_opt = ["전체 카테고리", "든든한 향토 한식", "시원한 해산물/회", "바삭 별미/육류", "국수/면/이색별미"]
            sel_cat = st.selectbox("🥢 음식 테마 필터", options=cat_opt, index=0, key="tab2_food_cat")

        # 필터링 로직
        filtered_50 = NATIONWIDE_50_FOODS
        if sel_zone != "전체 권역 (52선)":
            zone_key = sel_zone.split()[0]
            filtered_50 = [f for f in filtered_50 if f["zone"] == zone_key]
        if sel_cat != "전체 카테고리":
            filtered_50 = [f for f in filtered_50 if f["category"] == sel_cat]
        if kw_food.strip():
            query = kw_food.strip().lower()
            filtered_50 = [
                f for f in filtered_50
                if query in f["name"].lower() or query in f["food_name"].lower() or query in f["signature"].lower() or query in f["address"].lower() or query in f["region"].lower()
            ]

        st.caption(f"선택하신 조건에 부합하는 전국 대표 로컬 맛집 **{len(filtered_50)}개소**가 검색되었습니다. 카드를 확인하고 '🎪 연계 축제 가이드 보기'를 누르면 관련 축제 정보로 바로 이동합니다.")

        # 4. 3열 반응형 맛집 카드 그리드 렌더링
        if not filtered_50:
            st.warning("⚠️ 검색 조건에 부합하는 맛집이 없습니다. 검색어 또는 필터를 변경해주세요.")
        else:
            cols_50 = st.columns(3)
            for idx, item in enumerate(filtered_50):
                with cols_50[idx % 3]:
                    with st.container(border=True):
                        st.image(item["photo_url"], use_container_width=True)
                        st.markdown(f"<div style='font-size:1.02rem; font-weight:700; color:#1E293B;'>{item['name']}</div>", unsafe_allow_html=True)
                        
                        st.markdown(
                            f"<div style='margin: 4px 0;'>"
                            f"<span style='background:#EEF2FF; color:#4F46E5; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>📍 {item['region']} ({item['zone']})</span> "
                            f"<span style='background:#ECFDF5; color:#059669; padding:2px 7px; border-radius:5px; font-size:0.75rem; font-weight:600;'>🥢 {item['category']}</span> "
                            f"<span style='font-size:0.75rem; color:#64748B;'>💰 {item['price']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(f"<div style='font-size:0.79rem; color:#1E293B; margin-bottom:4px;' class='card-text-clamp'>📍 <b>주소:</b> {item['address']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='card-text-clamp'><b>시그니처:</b> {item['signature']}</div>", unsafe_allow_html=True)

                        st.markdown(
                            f'<div style="background:#FFFBEB; border:1px solid #FCD34D; border-radius:8px; padding:6px 9px; margin:6px 0; font-size:0.76rem; color:#92400E; line-height:1.4;">'
                            f'💡 <b>로컬 팁:</b> {item["tip"]}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                        st.markdown(f"<div style='font-size:0.76rem; color:#4F46E5; margin-bottom:6px; font-weight:600;'>🎪 <b>연계 축제:</b> {item['fest_name']}</div>", unsafe_allow_html=True)

                        if st.button("🎪 이 맛집 & 축제 가이드 보기", key=f"btn_tab2_50_{item['id']}", use_container_width=True):
                            st.session_state.selected_festival_id = item["fest_link_id"]
                            st.session_state.view_mode = "detail"
                            st.rerun()

    # -------------------------------------------------------------------------
    # 탭 3: 2026 전국 지역 축제 현황 & 흐름도
    # -------------------------------------------------------------------------
    with tab_chart:
        st.markdown("### 📊 2026년 전국 17개 시·도 지역 축제 개최 현황 및 흐름도")
        st.caption("🏛️ 문화체육관광부 지역축제 개최계획 및 한국관광공사(대한민국 구석구석) 공공데이터 분석 실데이터 기반")

        # 1. 2026 전국 축제 핵심 통계 메트릭 (4열 카드)
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("🏛️ 2026 전국 총 축제수", "1,145개", help="전국 17개 광역 시·도 지자체 개최 예정 축제 전수")
        with m_col2:
            st.metric("🍂 연중 최대 성수기", "가을 (483건)", "9~10월 42.2% 집중")
        with m_col3:
            st.metric("🏆 최다 개최 지자체", "경기도 (145건)", "전국 12.7% 비중")
        with m_col4:
            st.metric("🏮 국가지정 문화관광축제", "20여 개소", "글로벌 대표 축제군")

        # 2. 2026 전국 지역별 현황 시각화 (좌: 시·도별 건수 바 차트, 우: 월별 개최 추이 영역 차트)
        df_nation = pd.DataFrame(NATIONWIDE_2026_STATS)
        df_monthly = pd.DataFrame(MONTHLY_2026_TREND)

        c_viz1, c_viz2 = st.columns([5.3, 4.7], gap="medium")
        with c_viz1:
            st.markdown("##### 🗺️ 2026 전국 17개 시·도별 축제 개최 건수 순위")
            fig_bar = px.bar(
                df_nation.sort_values(by="축제수", ascending=True),
                x="축제수",
                y="시도",
                orientation="h",
                color="권역",
                text="축제수",
                color_discrete_map={
                    "수도권": "#312E81",
                    "영남권": "#4F46E5",
                    "호남권": "#10B981",
                    "충청권": "#F59E0B",
                    "강원권": "#EC4899",
                    "제주권": "#06B6D4"
                }
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                height=420,
                margin=dict(t=10, b=10, l=10, r=25),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="개최 축제수 (건)",
                yaxis_title="",
                legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_viz2:
            st.markdown("##### 📈 2026 전국 월별 축제 개최 추이 흐름도")
            fig_line = px.area(
                df_monthly,
                x="월",
                y="축제수",
                markers=True,
                text="축제수",
                color_discrete_sequence=["#4F46E5"]
            )
            fig_line.update_traces(textposition="top center", line=dict(width=3))
            fig_line.update_layout(
                height=420,
                margin=dict(t=10, b=10, l=10, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="개최 월",
                yaxis_title="월별 축제수 (건)"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        # 3. 2026 전국 17개 시·도별 상세 실데이터 테이블
        with st.expander("📑 2026년 전국 17개 시·도별 축제 상세 통계 데이터 테이블 (클릭하여 펼치기)", expanded=False):
            st.dataframe(
                df_nation,
                column_config={
                    "시도": st.column_config.TextColumn("시·도명"),
                    "권역": st.column_config.TextColumn("행정권역"),
                    "축제수": st.column_config.NumberColumn("축제 건수", format="%d건"),
                    "비율(%)": st.column_config.ProgressColumn("전국 비중(%)", min_value=0, max_value=15, format="%.1f%%"),
                    "대표축제": st.column_config.TextColumn("대표 주요 축제"),
                    "대표테마": st.column_config.TextColumn("주력 테마"),
                    "피크시즌": st.column_config.TextColumn("성수기 월")
                },
                hide_index=True,
                use_container_width=True
            )

        st.markdown("---")

        # 4. 현재 선택된 필터 조건의 테마 분포 & 축제 핵심 요약 (기존 기능과 완벽 융합)
        st.markdown("#### 🎯 [선택 조건] 테마별 구성 비중 & 축제 핵심 요약 흐름")
        st.caption("사이드바에서 선택한 지역/테마 조건에 해당하는 축제들의 테마 비중과 상세 요약 카드입니다.")
        
        if filtered_festivals:
            col_chart_left, col_chart_right = st.columns([4.6, 5.4], gap="large")
            
            theme_color_map = {
                "미식": "#F59E0B",
                "야경/체험": "#EC4899",
                "힐링/자연": "#10B981",
                "전통문화": "#4F46E5"
            }
            
            with col_chart_left:
                st.markdown("##### 🍩 선택 테마별 구성 비중")
                theme_counts = pd.Series([f["theme"] for f in filtered_festivals]).value_counts().reset_index()
                theme_counts.columns = ["테마", "축제수"]

                fig_donut = px.pie(
                    theme_counts,
                    names="테마",
                    values="축제수",
                    hole=0.55,
                    color="테마",
                    color_discrete_map=theme_color_map
                )
                fig_donut.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    marker=dict(line=dict(color="#FFFFFF", width=2))
                )
                fig_donut.update_layout(
                    showlegend=True,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=300,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    )
                )
                st.plotly_chart(fig_donut, use_container_width=True)

                # 테마별 요약 뱃지 그리드 (마크다운 들여쓰기 코드블록 방지)
                theme_badges_html = "".join([
                    f'<div style="display:inline-flex; align-items:center; gap:6px; background:{theme_color_map.get(row["테마"], "#6B7280")}14; border:1px solid {theme_color_map.get(row["테마"], "#6B7280")}44; border-radius:10px; padding:6px 12px; margin:4px 6px 4px 0;"><span style="width:8px; height:8px; border-radius:50%; background:{theme_color_map.get(row["테마"], "#6B7280")}; display:inline-block;"></span><span style="font-size:0.84rem; font-weight:700; color:{theme_color_map.get(row["테마"], "#6B7280")};">{row["테마"]}</span><span style="font-size:0.80rem; font-weight:800; color:#1E293B; background:white; padding:1px 6px; border-radius:8px;">{row["축제수"]}곳</span></div>'
                    for _, row in theme_counts.iterrows()
                ])
                
                insight_html = (
                    f'<div style="background: linear-gradient(135deg, #FDFBF7 0%, #F9F6F0 50%, #F2EDE4 100%); border: 1px solid rgba(222, 212, 198, 0.85); border-radius: 14px; padding: 16px 18px; box-shadow: 0 4px 14px rgba(60, 50, 40, 0.05); margin-bottom: 15px;">'
                    f'<div style="font-size: 0.86rem; font-weight: 700; color: #1E293B; margin-bottom: 8px;">📊 필터 테마별 축제 현황</div>'
                    f'<div style="margin-bottom: 10px;">{theme_badges_html}</div>'
                    f'<div style="font-size: 0.82rem; color: #475569; line-height: 1.5; border-top: 1px dashed rgba(200, 190, 175, 0.6); padding-top: 8px;">'
                    f'💡 <b>AI 여행 큐레이터 팁:</b> 관심 테마의 축제를 우측 요약 카드에서 선택하시면 해당 축제와 연계 관광지, 로컬 맛집 중심의 맞춤 여행 동선이 즉각 재계산됩니다.'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(insight_html, unsafe_allow_html=True)

            with col_chart_right:
                st.markdown(f"##### 📋 검색된 축제 핵심 요약 ({len(filtered_festivals)}개)")
                
                # 축제 요약 카드 리스트 (마크다운 들여쓰기 코드블록 방지)
                for fest in filtered_festivals:
                    is_current = (fest["id"] == st.session_state.selected_festival_id)
                    badge_color = theme_color_map.get(fest["theme"], "#6B7280")
                    
                    selected_border = "border: 2px solid #4F46E5; box-shadow: 0 6px 18px rgba(79, 70, 229, 0.15);" if is_current else "border: 1px solid rgba(222, 212, 198, 0.85); box-shadow: 0 4px 12px rgba(60, 50, 40, 0.04);"
                    current_badge = f'<span style="background:#4F46E5; color:#FFFFFF; font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:10px; margin-left:6px;">🎯 현재 선택됨</span>' if is_current else ''
                    
                    card_html = (
                        f'<div style="background: linear-gradient(135deg, #FDFBF7 0%, #F9F6F0 50%, #F2EDE4 100%); {selected_border} border-radius: 14px; padding: 14px 18px; margin-bottom: 12px;">'
                        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 6px;">'
                        f'<div><span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">{fest["name"]}</span>{current_badge}</div>'
                        f'<div><span style="background:{badge_color}18; color:{badge_color}; border:1px solid {badge_color}44; font-size:0.74rem; font-weight:700; padding:2px 8px; border-radius:12px;">{fest["theme"]}</span>'
                        f'<span style="background:#E2E8F0; color:#334155; font-size:0.74rem; font-weight:700; padding:2px 8px; border-radius:12px; margin-left:4px;">{fest["region"]}</span></div>'
                        f'</div>'
                        f'<div style="font-size: 0.83rem; color: #334155; line-height: 1.5; margin-bottom: 6px;">'
                        f'🗓️ <b>기간:</b> {fest["period"]}<br/>'
                        f'📍 <b>주소:</b> {fest["address"]}<br/>'
                        f'🍲 <b>대표 음식:</b> {fest["food"]["name"]} <span style="color:#64748B;">({fest["food"]["price"]})</span>'
                        f'</div>'
                        f'<div style="font-size: 0.80rem; color: #475569; background: rgba(255,255,255,0.7); border: 1px solid rgba(226, 232, 240, 0.8); border-radius: 8px; padding: 6px 10px; line-height: 1.45;">'
                        f'💡 {fest["description"]}'
                        f'</div>'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # 액션 버튼 2열 배치
                    col_btn_a, col_btn_b = st.columns([1, 1])
                    with col_btn_a:
                        if st.button(f"🎯 {fest['name']} 선택", key=f"flow_pick_{fest['id']}", use_container_width=True):
                            st.session_state.selected_festival_id = fest["id"]
                            st.session_state.sb_festival_select = fest["name"]
                            st.rerun()
                    with col_btn_b:
                        st.link_button("🌐 공식 홈페이지", fest["homepage_url"], use_container_width=True)
                    
                    st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)
        else:
            st.info("선택된 조건에 표시할 축제 데이터가 없습니다. 사이드바에서 지역이나 테마를 추가로 선택해보세요.")


# =============================================================================
# 11. 푸터 영역
# =============================================================================
st.markdown("---")
st.markdown("""
    <div style="text-align:center; color:#94A3B8; font-size:0.85rem; padding: 10px 0;">
        🤖 <b>AI Agent 기반 지역 축제 & 맞춤 여행 코스 추천 시스템</b> | Demo Web Application<br/>
        Made with ❤️ using Streamlit & Plotly & Folium | Multi-Agent Architecture Prototype
    </div>
""", unsafe_allow_html=True)
