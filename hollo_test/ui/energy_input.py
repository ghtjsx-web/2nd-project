"""
ui/energy_input.py
1집구석(1hows.com) 스타일의 라이프스타일 Hero, 카테고리 캡슐 칩 & 배터리 선택기
- 고대비 젯블랙(#111111) & 딥그린(#056608) 포인트
- st.html을 사용하여 순수 HTML 완벽 렌더링
"""

import streamlit as st

try:
    from config import ENERGY_LEVELS
except ImportError:
    from hollo_test.config import ENERGY_LEVELS


def render_energy_input() -> dict:
    """
    1집구석 감성의 Hero, 테마 캡슐 칩(Pill), 슬림 검색창, 배터리 선택기를 렌더링합니다.
    """
    # 1. 1집구석 시그니처 Hero 헤더 (st.html 사용)
    st.html(
        """
        <div style="text-align: center; padding: 18px 0 20px 0;">
            <div style="display:inline-block; padding: 5px 16px; background: #eaf5ea; border: 1px solid #d2e6d2; border-radius: 9999px; font-size: 0.8rem; font-weight: 800; color: #056608; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 14px;">
                SOLO · DISCOVER · CURATED
            </div>
            <h1 style="font-size: 2.6rem; font-weight: 900; color: #111111; margin: 0 0 10px 0; letter-spacing: -1px; line-height: 1.25;">
                “오늘, 혼자 뭐하지?”
            </h1>
            <p style="font-size: 1.05rem; color: #374151; margin: 0 auto; max-width: 580px; line-height: 1.65; font-weight: 500;">
                소음 가득한 일상에서 벗어나, 혼자일 때 비로소 온전해지는 나만의 쉼표를 골라드립니다.
            </p>
        </div>
        """
    )

    # 2. 1집구석 시그니처: 가로형 라이프스타일 캡슐 칩 (Pill Chips)
    if "selected_mood_chip" not in st.session_state:
        st.session_state.selected_mood_chip = "ALL"

    mood_chips = [
        {"id": "ALL", "label": "🌿 전체 쉼터", "query": "서울에서 이번 주말에 혼자 가기 좋은 고요한 쉼터 추천해줘.", "energy": "LOW"},
        {"id": "SEA", "label": "🌊 고요한 바다멍", "query": "서울에서 이번 주말에 혼자 바다 보러 가고 싶어. 사람 많은 데 말고 조용한 곳으로.", "energy": "LOW"},
        {"id": "FOREST", "label": "🌲 숲길 · 피톤치드", "query": "환승 없이 전철 하나로 바로 갈 수 있는 피톤치드 숲길과 산책로 걷고 싶어.", "energy": "LOW"},
        {"id": "BOOK", "label": "📖 북카페 · 서점", "query": "주말에 혼자 조용히 책 읽고 멍때리기 좋은 북카페나 문화 공간 추천해줘.", "energy": "MEDIUM"},
        {"id": "REST", "label": "🪫 완전 방전 쉼", "query": "회사에서 너무 지쳤어. 아무것도 안 하고 조용한 자연에서 물소리 새소리만 들으며 멍때리고 싶어.", "energy": "EMPTY"},
    ]

    st.html("<div style='margin-bottom: 6px;'></div>")
    cols = st.columns(len(mood_chips))

    for i, chip in enumerate(mood_chips):
        with cols[i]:
            is_active = (st.session_state.selected_mood_chip == chip["id"])
            btn_type = "primary" if is_active else "secondary"
            if st.button(chip["label"], key=f"chip_{chip['id']}", type=btn_type, use_container_width=True):
                st.session_state.selected_mood_chip = chip["id"]
                st.session_state.selected_energy = chip["energy"]
                st.session_state.current_query = chip["query"]
                st.rerun()

    # 3. 슬림 캡슐 검색창 (Pill Search Bar)
    st.html("<div style='margin-top: 12px;'></div>")
    
    if "current_query" not in st.session_state:
        st.session_state.current_query = "서울에서 이번 주말에 혼자 쉴 수 있는 조용한 바다나 숲길 추천해줘."

    search_col1, search_col2 = st.columns([5, 1.2])
    with search_col1:
        user_query = st.text_input(
            "검색창",
            value=st.session_state.current_query,
            placeholder="어떤 하루를 보내고 싶으신가요? (예: 전철 타고 가는 조용한 숲길, 혼밥 편한 곳)",
            label_visibility="collapsed",
        )
    with search_col2:
        run_curation = st.button("🔍 맞춤 큐레이션", type="primary", use_container_width=True)

    # 4. 4단계 에너지 배터리 선택기
    st.html(
        """
        <div style="display:flex; align-items:center; gap:8px; margin-top:16px; margin-bottom:8px;">
            <span style="font-size:0.92rem; font-weight:800; color:#111111;">🔋 지금 내 에너지 배터리 상태:</span>
            <span style="font-size:0.82rem; color:#056608; font-weight:600;">(상태에 따라 코스 밀도와 추천 장소가 자동으로 조정됩니다)</span>
        </div>
        """
    )

    energy_items = [
        {"key": "EMPTY", "label": "🪫 15% 방전 (단순 휴식)", "sub": "무리한 이동 없이 멍때리기"},
        {"key": "LOW", "label": "🔋 40% 잔잔 (느린 산책)", "sub": "가벼운 숲길과 바람 쐬기"},
        {"key": "MEDIUM", "label": "🔋 70% 보통 (사색&독서)", "sub": "동네 서점, 조용한 카페"},
        {"key": "HIGH", "label": "⚡ 100% 충만 (골목 탐방)", "sub": "새로운 영감과 문화 탐방"},
    ]

    e_cols = st.columns(4)

    if "selected_energy" not in st.session_state:
        st.session_state.selected_energy = "LOW"

    for i, item in enumerate(energy_items):
        is_selected = (st.session_state.selected_energy == item["key"])
        with e_cols[i]:
            btn_type = "primary" if is_selected else "secondary"
            if st.button(item["label"], key=f"btn_e_{item['key']}", type=btn_type, use_container_width=True):
                st.session_state.selected_energy = item["key"]
                st.rerun()

    return {
        "energy_key": st.session_state.selected_energy,
        "query": user_query,
        "run_clicked": run_curation,
    }
