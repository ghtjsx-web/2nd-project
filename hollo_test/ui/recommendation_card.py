"""
ui/recommendation_card.py
1집구석(1hows.com) 스타일의 고품격 에디토리얼 매거진 카드 그리드
- 16:10 비율 이미지 쇼케이스
- 젯블랙(#111111) 볼드 타이틀 & 딥그린(#056608) 시그니처 뱃지
- 찜하기 인터랙션 & 맞춤 하루 코스 아코디언
- st.html을 사용하여 순수 HTML 완벽 렌더링
"""

import streamlit as st


def render_recommendation_cards(recommendations: list):
    """
    1hows 스타일의 3열 라이프스타일 큐레이션 매거진 카드를 렌더링합니다.
    """
    if not recommendations:
        st.info("조건에 맞는 여행지가 없습니다. 조건을 조금 더 여유롭게 조정해 보세요.")
        return

    st.html(
        """
        <div style="margin-top: 28px; margin-bottom: 16px; display:flex; justify-content:space-between; align-items:flex-end;">
            <div>
                <span style="font-size: 0.8rem; font-weight: 800; color: #056608; letter-spacing: 1.5px; text-transform: uppercase;">TODAY'S CURATION</span>
                <h2 style="margin: 4px 0 0 0; font-size: 1.6rem; font-weight: 900; color: #111111; letter-spacing: -0.5px;">
                    혼자일 때 더 좋은 곳
                </h2>
            </div>
            <span style="font-size: 0.88rem; color: #555555; font-weight: 600;">
                오늘의 배터리 & 기분에 맞춘 <b>3곳</b>의 쉼표
            </span>
        </div>
        """
    )

    # 찜한 장소 세션 상태
    if "liked_places" not in st.session_state:
        st.session_state.liked_places = set()

    card_cols = st.columns(3)

    for i, r in enumerate(recommendations):
        place = r["place"]
        itinerary = r["adapted_itinerary"]
        place_id = place.get("id", f"place-{i}")
        is_liked = place_id in st.session_state.liked_places
        
        with card_cols[i]:
            # 1. 1hows 매거진 카드 컨테이너 (st.html 사용)
            img_url = place.get("image_url", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80")
            quiet_score = place.get("scores", {}).get("quietness", 4.5)
            short_name = place['name'].split('&')[0].strip()
            theme_name = place.get('theme', '쉼')

            st.html(
                f"""
                <div style="background: #ffffff; border: 1.5px solid #e7ece7; border-radius: 18px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 12px;">
                    <!-- 16:10 비율 왜곡 없는 이미지 쇼케이스 -->
                    <div style="width: 100%; aspect-ratio: 16/10; border-radius: 12px; overflow: hidden; margin-bottom: 14px; background: #f0f0f0;">
                        <img src="{img_url}" alt="{place['name']}" style="width: 100%; height: 100%; object-fit: cover; display: block;" />
                    </div>
                    <!-- 카테고리 태그 & 한적함 별점 배지 -->
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                        <span style="font-size: 0.8rem; font-weight: 800; color: #056608; letter-spacing: 0.5px;">
                            쉼 · {theme_name}
                        </span>
                        <span style="background: #eaf5ea; color: #056608; font-size: 0.78rem; font-weight: 800; padding: 3px 9px; border-radius: 9999px; border: 1px solid #d2e6d2;">
                            한적함 ★ {quiet_score}
                        </span>
                    </div>
                    <!-- 선명한 젯블랙 타이틀 (#111111) -->
                    <h3 style="margin: 0 0 8px 0; font-size: 1.25rem; font-weight: 900; color: #111111; letter-spacing: -0.4px; line-height: 1.35;">
                        {short_name}
                    </h3>
                    <!-- 감성 한 줄 요약 (#333333, 고대비) -->
                    <p style="margin: 0 0 12px 0; font-size: 0.9rem; color: #374151; line-height: 1.55; height: 44px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; font-weight: 500;">
                        {place.get('summary')}
                    </p>
                    <!-- 뚜벅이 핵심 정보 배지 -->
                    <div style="display:flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px;">
                        <span style="background:#f3f4f6; color:#1f2937; padding:4px 9px; border-radius:8px; font-size:0.78rem; font-weight:700;">
                            🚆 편도 {place['transit']['total_minutes']}분
                        </span>
                        <span style="background:#f3f4f6; color:#1f2937; padding:4px 9px; border-radius:8px; font-size:0.78rem; font-weight:700;">
                            환승 {place['transit']['transfers']}회
                        </span>
                        <span style="background:#f3f4f6; color:#1f2937; padding:4px 9px; border-radius:8px; font-size:0.78rem; font-weight:700;">
                            {place['region'].split()[0]}
                        </span>
                    </div>
                    <!-- 큐레이터 감성 노트 -->
                    <div style="background: #f7faf7; border-left: 3.5px solid #056608; padding: 10px 12px; border-radius: 6px; font-size: 0.84rem; color: #1f2937; line-height: 1.55; font-weight: 500;">
                        “{place.get('curator_note')}”
                    </div>
                </div>
                """
            )

            # 2. 찜하기 버튼 & 코스 토글
            c_btn1, c_btn2 = st.columns([1.1, 1.9])
            with c_btn1:
                heart_label = "❤️ 찜함" if is_liked else "🤍 찜하기"
                btn_kind = "primary" if is_liked else "secondary"
                if st.button(heart_label, key=f"btn_like_{place_id}", type=btn_kind, use_container_width=True):
                    if is_liked:
                        st.session_state.liked_places.remove(place_id)
                    else:
                        st.session_state.liked_places.add(place_id)
                    st.rerun()

            with st.expander("⏱️ 나만의 하루 코스"):
                for s in itinerary:
                    st.html(
                        f"""
                        <div style="padding: 6px 0; border-bottom: 1px dashed #e2e8e0; font-size: 0.85rem;">
                            <span style="color:#056608; font-weight:800;">[{s.get('time')}]</span> 
                            <b style="color:#111111; font-weight:800; margin-left:4px;">{s.get('spot')}</b><br/>
                            <span style="color:#4a5568; font-size:0.8rem; font-weight:500;">🍃 {s.get('vibe')}</span>
                        </div>
                        """
                    )
                st.html(
                    f"""
                    <div style="margin-top:8px; font-size:0.78rem; color:#2d3748; font-weight:600; background:#f4f8f4; padding:6px 10px; border-radius:6px;">
                        🚆 {place['transit']['route']}
                    </div>
                    """
                )

    st.html("<br/>")
