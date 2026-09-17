"""
ui/control_deck.py
1집구석 스타일의 미니멀 세부 필터 덱 (대중교통 시간 / 페르소나 / 테마)
- st.html을 사용하여 순수 HTML 완벽 렌더링
"""

import streamlit as st

try:
    from config import PERSONAS
    from services.place_service import place_service
except ImportError:
    from hollo_test.config import PERSONAS
    from hollo_test.services.place_service import place_service


def render_control_deck() -> dict:
    """
    깔끔한 화이트 카드 형태로 접혀 있는 상세 필터 옵션을 렌더링합니다.
    """
    with st.expander("⚙️ 여행 세부 조건 필터 (시간 / 페르소나 / 테마)", expanded=False):
        c1, c2, c3 = st.columns([1.2, 1.1, 1.1])

        with c1:
            st.html("<b style='color:#111111; font-size:0.92rem;'>👤 여행 페르소나</b>")
            persona_keys = list(PERSONAS.keys())
            persona_options = ["전체 (모든 유형)"] + [f"{PERSONAS[k]['title']} ({PERSONAS[k]['tag']})" for k in persona_keys]
            selected_idx = st.selectbox("페르소나", range(len(persona_options)), format_func=lambda x: persona_options[x], label_visibility="collapsed")
            selected_persona = PERSONAS[persona_keys[selected_idx - 1]]["title"] if selected_idx > 0 else None

        with c2:
            st.html("<b style='color:#111111; font-size:0.92rem;'>🚆 편도 최대 이동시간</b>")
            max_transit = st.slider("이동시간(분)", 45, 180, 120, 15, label_visibility="collapsed")
            st.html(
                f"<div style='font-size:0.84rem; color:#056608; font-weight:700; margin-top:4px;'>최대 {max_transit}분 (약 {max_transit//60}시간 {max_transit%60}분) 이내</div>"
            )

        with c3:
            st.html("<b style='color:#111111; font-size:0.92rem;'>🏷️ 선호 테마</b>")
            themes = ["전체 (모든 테마)"] + place_service.get_themes()
            selected_theme_raw = st.selectbox("테마", themes, index=0, label_visibility="collapsed")
            selected_theme = None if "전체" in selected_theme_raw else selected_theme_raw

        st.html("<div style='margin-top:10px;'></div>")
        dev_mode = st.checkbox("🛠️ 디버그 정보 보기 (개발자 모드)", value=False)

        return {
            "persona": selected_persona,
            "max_transit": max_transit,
            "theme": selected_theme,
            "crowd_tolerance": "최대한 피하고 싶어요",
            "dev_mode": dev_mode,
        }

    return {
        "persona": None,
        "max_transit": 120,
        "theme": None,
        "crowd_tolerance": "최대한 피하고 싶어요",
        "dev_mode": False,
    }
