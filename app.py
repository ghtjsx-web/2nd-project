"""
app.py - Fest & Rest (초개인화 로컬 축제 & 쉼터 큐레이션 에이전트)
어떤 브라우저/OS 테마에서도 완벽한 시인성(화이트 배경 + 딥 다크 텍스트)을 보장하는 Streamlit 프로토타입
"""

from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from data_tools import get_dummy_festivals, get_dummy_rests
from agents import generate_curation

# 1. 환경변수(.env) 로드
load_dotenv()

# 2. 페이지 설정
st.set_page_config(
    page_title="Fest & Rest | 초개인화 로컬 축제 & 쉼터 큐레이션",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. 세션 상태(Session State) 초기화
if "applied_feedback" not in st.session_state:
    st.session_state["applied_feedback"] = ""
if "feedback_history" not in st.session_state:
    st.session_state["feedback_history"] = []
if "feedback_input" not in st.session_state:
    st.session_state["feedback_input"] = ""

# 4. 커스텀 CSS: 
# [절대 규칙] 다크모드/라이트모드 무관하게 무조건 '순백색/연한 배경(#ffffff, #f8fafc)' 위에 '선명한 짙은 검정(#0f172a)' 텍스트 강제 적용
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');

    /* 1. 전체 앱 기본 배경 및 기본 글자색 고정 (다크모드 오염 원천 차단) */
    .stApp {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* 본문 및 기본 마크다운 텍스트 */
    .stApp p, .stApp span, .stApp div, .stApp label, .stApp li {
        color: #0f172a !important;
    }

    /* 2. 상단 헤더 영역 */
    .hero-container {
        padding: 8px 0 16px 0;
        border-bottom: 2px solid #e2e8f0;
        margin-bottom: 24px;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a !important;
        letter-spacing: -0.8px;
        margin-bottom: 6px;
    }
    .hero-title span {
        color: #0d9488 !important;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #334155 !important;
        font-weight: 500;
        line-height: 1.6;
    }

    /* 3. 에디터 브리핑 감성 레터 박스 (절대 시인성) */
    .editor-letter-box {
        background-color: #f8fafc !important;
        border: 1.5px solid #cbd5e1 !important;
        border-left: 6px solid #0d9488 !important;
        padding: 24px 28px;
        border-radius: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
    }
    .editor-letter-box * {
        color: #0f172a !important;
    }
    .editor-letter-box h1, .editor-letter-box h2, .editor-letter-box h3, .editor-letter-box h4 {
        color: #0f172a !important;
        font-weight: 800 !important;
        margin-top: 0;
        margin-bottom: 12px;
    }
    .editor-letter-box blockquote {
        background-color: #ffffff !important;
        border-left: 4px solid #f59e0b !important;
        border: 1px solid #e2e8f0;
        padding: 12px 16px;
        margin: 14px 0;
        border-radius: 6px;
    }
    .editor-letter-box blockquote * {
        color: #0f172a !important;
    }

    /* 4. 피드백 활성화 뱃지 */
    .feedback-active-badge {
        background-color: #ecfdf5 !important;
        border: 1.5px solid #10b981 !important;
        color: #065f46 !important;
        padding: 12px 18px;
        border-radius: 10px;
        font-weight: 700;
        margin-bottom: 16px;
        font-size: 0.95rem;
    }
    .feedback-active-badge * {
        color: #065f46 !important;
    }

    /* 5. 타임테이블 카드 */
    .time-card {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        height: 100%;
        min-height: 210px;
    }
    .time-card * {
        color: #0f172a !important;
    }
    .badge-pill {
        display: inline-block;
        font-size: 0.8rem !important;
        font-weight: 800 !important;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .badge-fest {
        background-color: #fee2e2 !important;
        color: #991b1b !important;
        border: 1.5px solid #f87171 !important;
    }
    .badge-rest {
        background-color: #dcfce7 !important;
        color: #166534 !important;
        border: 1.5px solid #4ade80 !important;
    }
    .badge-dine {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
        border: 1.5px solid #94a3b8 !important;
    }

    /* 6. 사용자 의견 입력 컨테이너 */
    .feedback-container {
        background-color: #f8fafc !important;
        border: 2px solid #0d9488 !important;
        border-radius: 14px;
        padding: 22px 24px;
        margin: 24px 0 16px 0;
        box-shadow: 0 4px 16px rgba(13, 148, 136, 0.06);
    }
    .feedback-container * {
        color: #0f172a !important;
    }
    .feedback-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f172a !important;
        margin-bottom: 6px;
    }
    .feedback-subtitle {
        font-size: 0.9rem;
        color: #334155 !important;
        margin-bottom: 12px;
    }

    /* 7. 이미지 규격 통일 (16:9 비율, 높이 220px 고정) */
    div[data-testid="stImage"] {
        width: 100% !important;
    }
    div[data-testid="stImage"] img {
        width: 100% !important;
        height: 220px !important;
        max-height: 220px !important;
        min-height: 220px !important;
        object-fit: cover !important;
        border-radius: 14px 14px 0 0 !important;
        display: block !important;
        border: 1.5px solid #cbd5e1 !important;
        border-bottom: none !important;
    }

    /* 이미지 카드 본문 */
    .spot-card-body {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-top: none !important;
        border-radius: 0 0 14px 14px;
        padding: 16px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        min-height: 185px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .spot-card-body * {
        color: #0f172a !important;
    }
    .spot-card-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0f172a !important;
        margin-bottom: 4px;
    }
    .spot-card-meta {
        font-size: 0.84rem;
        font-weight: 800;
        color: #0369a1 !important;
        margin-bottom: 8px;
    }
    .spot-card-desc {
        font-size: 0.88rem;
        color: #334155 !important;
        line-height: 1.55;
        margin-bottom: 10px;
    }
    .spot-card-query {
        background-color: #f1f5f9 !important;
        border: 1px dashed #94a3b8 !important;
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        color: #1e293b !important;
        font-weight: 700;
    }
    .spot-card-query * {
        color: #1e293b !important;
    }

    /* 8. 스트림릿 입력 컴포넌트(텍스트영역, 버튼 등) 시인성 */
    .stTextArea textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #94a3b8 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
    }
    .stTextArea textarea::placeholder {
        color: #64748b !important;
    }
    div[data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }

    /* 9. 사이드바 전체 가독성 강제 */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 2px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] p {
        color: #1e293b !important;
    }
    section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #0f172a !important;
        font-weight: 800 !important;
    }

    /* 버튼 기본 폰트 색상 및 테두리 */
    .stButton button {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        font-weight: 700 !important;
    }
    .stButton button:hover {
        border-color: #0d9488 !important;
        color: #0d9488 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. 사이드바: 기본 필터 및 상태 입력
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎪 **Fest & Rest**")
    st.caption("초개인화 로컬 축제 & 쉼터 큐레이터")
    st.success("🟢 **LLM & 웹 이미지 검색 활성화**")
    st.markdown("---")

    st.subheader("⚡ 나의 여행 프로필")

    # 1) 에너지 배터리
    battery = st.slider(
        "오늘 에너지 배터리 잔량 (%)",
        min_value=0,
        max_value=100,
        value=65,
        step=5,
        help="0에 가까울수록 조용한 쉼 중심, 100에 가까울수록 활발한 축제 중심"
    )

    if battery < 40:
        st.error("🪫 **방전 상태**: 인파를 피해 고즈넉한 쉼과 충전이 필요합니다.")
    elif battery <= 75:
        st.info("🔋 **균형 상태**: 축제의 기분 좋은 자극과 여유로운 쉼의 밸런스 코스입니다.")
    else:
        st.success("⚡ **에너지 완충**: 축제의 도파민과 나이트 라이프를 온몸으로 즐길 준비 완료!")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2) 동반자 선택
    companion = st.selectbox(
        "누구와 함께 떠나시나요?",
        options=["혼자", "연인", "가족"],
        index=0,
        help="동반자에 맞추어 이동 동선과 장소 테마가 최적화됩니다."
    )

    # 3) 선호하는 분위기 선택
    mood = st.radio(
        "오늘 가장 끌리는 분위기는?",
        options=["힙하고 트렌디한", "조용하고 아늑한", "자연친화적인"],
        index=0,
        help="LLM 에이전트가 이 분위기에 맞는 장소와 최적 검색 키워드를 생성합니다."
    )

    st.markdown("---")

    # 캐시 초기화 및 전체 재생성
    if st.button("🔄 기본 코스로 새로고침", width="stretch"):
        st.session_state["applied_feedback"] = ""
        st.session_state["feedback_input"] = ""
        st.cache_data.clear()
        st.rerun()

# -------------------------------------------------------------
# 6. LLM 에이전트 호출 (사용자 피드백 포함 캐싱)
# -------------------------------------------------------------
@st.cache_data(show_spinner="🤖 LLM 에이전트가 당신의 조건과 의견을 분석하여 맞춤 코스를 기획 중입니다...")
def cached_curation(battery_val: int, companion_val: str, mood_val: str, feedback_val: str):
    return generate_curation(
        battery=battery_val,
        companion=companion_val,
        mood=mood_val,
        user_feedback=feedback_val
    )

curation = cached_curation(
    battery,
    companion,
    mood,
    st.session_state["applied_feedback"]
)

briefing_md = curation["briefing"]
timetable = curation["timetable"]
recommended_spots = curation["recommended_spots"]

# -------------------------------------------------------------
# 7. 메인 화면 상단: 헤더 및 에디터 브리핑
# -------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Fest & Rest <span>Personal Curator</span> 🎪🌿</div>
    <div class="hero-subtitle">
        지친 일상의 소음 대신, 당신의 에너지 배터리와 취향에 딱 맞춘 <b>축제(Fest)와 쉼터(Rest)의 황금 비율</b>을 제안합니다.
    </div>
</div>
""", unsafe_allow_html=True)

# 현재 피드백이 적용되어 있는 경우 상단 알림 배너 표시
if st.session_state["applied_feedback"]:
    st.markdown(f"""
    <div class="feedback-active-badge">
        ✨ <b>현재 반영된 사용자 의견:</b> "{st.session_state['applied_feedback']}"
    </div>
    """, unsafe_allow_html=True)

# 1) 에디터 감성 브리핑 (화이트/소프트 배경 위의 딥다크 글씨 보장)
st.markdown(f'<div class="editor-letter-box">\n\n{briefing_md}\n\n</div>', unsafe_allow_html=True)

# 2) 3단계 다이내믹 타임테이블
st.markdown("### ⏱️ 맞춤 3단계 다이내믹 타임테이블")
st.caption("에너지 소모와 충전의 리듬을 고려하여 시간대별로 가장 이상적인 동선으로 배열했습니다.")

cols = st.columns(3)
for col, step in zip(cols, timetable):
    with col:
        badge_cls = "badge-fest" if "FESTIVAL" in step.get("category", "") else "badge-rest"
        if "DINE" in step.get("category", ""):
            badge_cls = "badge-dine"

        category_icon = "🔥" if "FESTIVAL" in step.get("category", "") else ("🌿" if "REST" in step.get("category", "") else "🍵")

        st.markdown(f"""
        <div class="time-card">
            <span class="badge-pill {badge_cls}">{category_icon} {step.get('category', 'SPOT')}</span>
            <span style="float:right; font-size:0.8rem; font-weight:700; color:#475569;">{step.get('tag', '')}</span>
            <div style="font-size:0.86rem; font-weight:800; color:#0369a1; margin-top:4px;">📍 {step.get('step', '')} · {step.get('time', '')}</div>
            <div style="font-size:1.1rem; font-weight:800; color:#0f172a; margin: 6px 0 8px 0;">{step.get('title', '')}</div>
            <div style="font-size:0.88rem; color:#334155; line-height:1.55;">{step.get('desc', '')}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 8. 사용자 루트 의견 / 피드백 입력 섹션
# -------------------------------------------------------------
st.markdown("""
<div class="feedback-container">
    <div class="feedback-title">💬 추천된 루트가 마음에 드시나요? 나만의 의견을 남겨주세요!</div>
    <div class="feedback-subtitle">
        "걷는 거리를 최소화해줘", "인디 버스킹보다 조용한 서재에 더 오래 머물고 싶어", "사진 잘 나오는 스팟 위주로 바꿔줘" 등<br>
        원하시는 점을 자유롭게 적으시면, <b>LLM 에디터가 당신의 의견을 즉시 반영하여 코스를 다시 짜드립니다.</b>
    </div>
</div>
""", unsafe_allow_html=True)

# 빠른 프리셋 선택 칩
preset_cols = st.columns([1.2, 1.2, 1.4, 3])
with preset_cols[0]:
    if st.button("👟 덜 걷는 코스로", width="stretch"):
        st.session_state["feedback_input"] = "다리가 아파서 이동 거리를 최소화하고 오래 앉아 쉴 수 있게 해주세요."
        st.rerun()
with preset_cols[1]:
    if st.button("📸 사진 명소 위주로", width="stretch"):
        st.session_state["feedback_input"] = "감성적인 인스타 사진을 남기기 좋은 예쁜 포토존 위주로 구성해주세요."
        st.rerun()
with preset_cols[2]:
    if st.button("🍵 차와 디저트 비중 확대", width="stretch"):
        st.session_state["feedback_input"] = "시끄러운 축제 대신 향긋한 차와 디저트를 음미하는 카페 시간을 늘려주세요."
        st.rerun()

# 피드백 입력 폼
with st.form(key="route_feedback_form"):
    user_opinion = st.text_area(
        label="✍️ 나만의 코스 요청사항 또는 피드백 입력",
        value=st.session_state.get("feedback_input", ""),
        placeholder="예시: 비가 올 것 같아서 실내 위주로 가고 싶어요 / 저녁에 한강 야경을 더 길게 보고 싶어요",
        height=90
    )

    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        submit_feedback = st.form_submit_button("🚀 내 의견 반영하여 코스 재구성하기", width="stretch")
    with btn_col2:
        clear_feedback = st.form_submit_button("↩️ 의견 초기화", width="stretch")

if submit_feedback:
    if user_opinion.strip():
        st.session_state["applied_feedback"] = user_opinion.strip()
        st.session_state["feedback_input"] = user_opinion.strip()
        st.session_state["feedback_history"].append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "feedback": user_opinion.strip()
        })
        st.success(f"✨ 사용자님의 의견을 접수했습니다! 코스를 다시 기획합니다.")
        st.rerun()
    else:
        st.warning("의견을 1자 이상 입력해주세요.")

if clear_feedback:
    st.session_state["applied_feedback"] = ""
    st.session_state["feedback_input"] = ""
    st.info("의견이 초기화되었습니다. 기본 추천 코스로 복구합니다.")
    st.rerun()

# 접이식 피드백 히스토리
if st.session_state["feedback_history"]:
    with st.expander("📜 내가 남긴 의견 히스토리 보기"):
        for item in reversed(st.session_state["feedback_history"]):
            st.markdown(f"- **[{item['timestamp']}]** {item['feedback']}")

st.markdown("<hr style='border-color:#e2e8f0;'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 9. 메인 화면 중단: 동일 규격의 실시간 검색 이미지 카드 갤러리
# -------------------------------------------------------------
st.markdown("### 📸 오늘의 추천 스팟 갤러리 (동일 규격 정렬)")
st.caption("LLM 에이전트가 각 장소의 분위기를 분석하여 생성한 검색 키워드로 실제 사진을 가져왔습니다.")

card_cols = st.columns(len(recommended_spots))

for col, spot in zip(card_cols, recommended_spots):
    with col:
        img_url = spot.get("display_image", spot.get("fallback_image", ""))

        # 규격 통일된 썸네일 이미지 (220px, 16:9 비율 크롭, width="stretch")
        st.image(img_url, width="stretch")

        category_label = "🔥 로컬 축제" if spot.get("category") == "festival" else "🌿 로컬 쉼터"

        # 카드 하단 설명 콘텐츠 박스
        st.markdown(f"""
        <div class="spot-card-body">
            <div>
                <div class="spot-card-title">{spot.get('name')}</div>
                <div class="spot-card-meta">{category_label} · {spot.get('theme')}</div>
                <div class="spot-card-desc">{spot.get('description')}</div>
            </div>
            <div>
                <div class="spot-card-query">🔍 <b>LLM 검색어:</b> {spot.get('search_query', spot.get('name'))}</div>
                <div style="font-size:0.8rem; font-weight:600; color:#64748b; margin-top:6px;">📍 {spot.get('address')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br><hr style='border-color:#e2e8f0;'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 10. 메인 화면 하단: st.map()을 활용한 위치 렌더링
# -------------------------------------------------------------
st.markdown("### 🗺️ 맞춤 동선 위치 지도")
st.caption("축제와 쉼터의 물리적 거리와 접근성을 지도에서 확인하세요.")

all_festivals = get_dummy_festivals()
all_rests = get_dummy_rests()
all_spots = all_festivals + all_rests

map_records = []
for s in all_spots:
    is_curated = any(rc["id"] == s["id"] for rc in recommended_spots)
    map_records.append({
        "latitude": s["lat"],
        "longitude": s["lon"],
        "name": s["name"],
        "category": s["category"],
        "is_curated": is_curated
    })

df_map = pd.DataFrame(map_records)

# Streamlit 내장 지도 렌더링
st.map(
    data=df_map,
    latitude="latitude",
    longitude="longitude",
    size=40,
    zoom=13
)

# 하단 데이터 테이블 요약
with st.expander("📋 전체 로컬 축제 & 쉼터 원본 데이터 보기"):
    st.dataframe(
        pd.DataFrame([
            {
                "구분": "🔥 축제" if s["category"] == "festival" else "🌿 쉼터",
                "장소명": s["name"],
                "테마": s["theme"],
                "에너지 소모": s["energy_cost"],
                "핵심 태그": s["tag"],
                "주소": s["address"]
            }
            for s in all_spots
        ]),
        width="stretch"
    )
