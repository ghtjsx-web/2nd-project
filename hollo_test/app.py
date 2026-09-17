"""
app.py
Hollo [홀로] - 1집구석(1hows.com) 감성의 1인 여행 & 쉼터 라이프스타일 큐레이션 플랫폼
- 메인 포인트 컬러: 딥 그린 (Deep Green, #056608)
- 배경 컬러: 산뜻한 오프 화이트 (#fafbfa) & 순백색 카드 (#ffffff)
- 텍스트: 선명한 젯 블랙 (#111111) & 딥 차콜 (#2b2b2b) - 가독성 100% 보장
- st.html을 사용하여 CSS 및 HTML 코드가 화면에 노출되지 않도록 완전 분리
"""

import os
import streamlit as st

try:
    from config import APP_TITLE, APP_SUBTITLE, APP_ICON
    from core.curator import hollo_curator
    from ui.control_deck import render_control_deck
    from ui.energy_input import render_energy_input
    from ui.recommendation_card import render_recommendation_cards
    from ui.map_view import render_map_view
except ImportError:
    from hollo_test.config import APP_TITLE, APP_SUBTITLE, APP_ICON
    from hollo_test.core.curator import hollo_curator
    from hollo_test.ui.control_deck import render_control_deck
    from hollo_test.ui.energy_input import render_energy_input
    from hollo_test.ui.recommendation_card import render_recommendation_cards
    from hollo_test.ui.map_view import render_map_view


# 1. Streamlit 페이지 설정
st.set_page_config(
    page_title=f"{APP_TITLE} - 혼자일 때 더 좋은 것들",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. 스타일시트 로드 (st.html 사용으로 마크다운 파싱 오류 및 코드 노출 방지)
css_path = os.path.join(os.path.dirname(__file__), "ui", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    st.html(f"<style>\n{css_content}\n</style>")

# 3. 1집구석 스타일 GNB 헤더 (로고, 서브타이틀, 찜 카운트)
if "liked_places" not in st.session_state:
    st.session_state.liked_places = set()

liked_count = len(st.session_state.liked_places)

st.html(
    f"""
    <div class="gnb-header">
        <div style="display:flex; align-items:center; gap:12px;">
            <span style="font-size:1.6rem; line-height:1;">{APP_ICON}</span>
            <div style="display:flex; align-items:baseline; gap:8px;">
                <span style="font-size:1.4rem; font-weight:900; color:#111111; letter-spacing:-0.5px;">{APP_TITLE}</span>
                <span style="font-size:0.85rem; color:#056608; font-weight:700; background:#eaf5ea; padding:3px 10px; border-radius:9999px;">
                    혼자일 때 더 좋은 것들
                </span>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:0.86rem; font-weight:700; color:#056608; background:#ffffff; border:1.5px solid #d2e6d2; padding:6px 16px; border-radius:9999px; box-shadow:0 2px 6px rgba(5,102,8,0.06);">
                ❤️ 찜한 쉼터 <b style="color:#056608; font-size:0.95rem; margin-left:4px;">{liked_count}</b>곳
            </div>
        </div>
    </div>
    """
)

# 4. 1집구석 시그니처 Hero 섹션 & 캡슐 필터 & 에너지 배터리
user_inputs = render_energy_input()

# 5. 미니멀 플로팅 컨트롤 덱 (세부 이동시간, 페르소나, 테마)
control_params = render_control_deck()

# 6. 세션 상태 관리 및 큐레이션 실행
if "curation_result" not in st.session_state:
    st.session_state.curation_result = None

# 검색 버튼 클릭 또는 최초 로드 시 큐레이션 실행
if user_inputs["run_clicked"] or st.session_state.curation_result is None:
    with st.spinner("🌿 오늘의 기분과 에너지에 맞는 나만의 쉼표를 고르고 있습니다..."):
        result = hollo_curator.curate(
            query=user_inputs["query"],
            energy_override=user_inputs["energy_key"],
            max_transit_override=control_params.get("max_transit"),
            theme_override=control_params.get("theme"),
        )
        st.session_state.curation_result = result

cur_result = st.session_state.curation_result

# 7. 큐레이터 감성 브리핑 (1집구석 에디터 편지)
if cur_result and cur_result.get("briefing"):
    st.html(
        f"""
        <div class="curator-note-card">
            <div class="curator-title">
                <span>💬</span> <span>에디터의 큐레이션 노트</span>
            </div>
            <div class="curator-body">
                {cur_result['briefing']}
            </div>
        </div>
        """
    )

# 8. 1hows 시그니처 매거진 카드 그리드 (3열)
if cur_result:
    render_recommendation_cards(cur_result.get("recommendations", []))

st.html("<hr style='margin:36px 0 24px 0; border:none; border-top:1.5px solid #e8ede8;'/>")

# 9. 미니멀 라이트 지도
if cur_result:
    render_map_view(cur_result.get("recommendations", []))

# 10. 개발자 디버그 모드 (필터 덱에서 체크 시)
if control_params.get("dev_mode") and cur_result:
    st.html("<hr style='margin:20px 0; border:none; border-top:1.5px solid #e8ede8;'/>")
    st.markdown("<h4 style='color:#111111;'>🛠️ [Debug Mode] 파이프라인 내부 상태</h4>", unsafe_allow_html=True)
    st.json({
        "query": cur_result.get("query"),
        "extracted_preferences": cur_result.get("preferences"),
        "liked_places": list(st.session_state.liked_places),
        "recommendation_count": len(cur_result.get("recommendations", [])),
    })
