"""
ui/map_view.py
딥 그린(#056608) 포인트 컬러 & 라이트 클린 지도 시각화 컴포넌트
"""

import streamlit as st
import pandas as pd
import pydeck as pdk


def render_map_view(recommendations: list):
    """
    선명한 라이트 맵과 딥 그린 포인트 핀으로 추천 쉼터 위치를 시각화합니다.
    """
    if not recommendations:
        return

    st.markdown("### 🗺️ 나만의 쉼터 위치 한눈에 보기")
    st.caption("지도 위의 딥그린 마커에 마우스를 올리면 상세 경로와 큐레이터 팁을 확인할 수 있습니다.")

    map_data = []
    # 딥그린 계열 포인트 마커 컬러 (1위: #056608 딥그린, 2위: 에메랄드, 3위: 세이지그린)
    marker_colors = [
        [5, 102, 8, 240],
        [16, 149, 83, 230],
        [67, 160, 71, 220]
    ]

    for i, r in enumerate(recommendations):
        p = r["place"]
        map_data.append({
            "rank": f"#{i+1}",
            "name": p["name"],
            "region": p["region"],
            "theme": p["theme"],
            "lat": p["lat"],
            "lon": p["lon"],
            "transit": p["transit"]["route"],
            "curator_note": p.get("curator_note", ""),
            "color": marker_colors[i % len(marker_colors)],
            "radius": 1800,
        })

    df = pd.DataFrame(map_data)

    avg_lat = df["lat"].mean() if not df.empty else 37.5665
    avg_lon = df["lon"].mean() if not df.empty else 127.3

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="radius",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=avg_lat,
        longitude=avg_lon,
        zoom=7.8,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<div style='font-family: sans-serif; padding: 10px; max-width: 270px; line-height: 1.5;'>"
            "<b style='color:#056608; font-size:1.05rem;'>{rank} {name}</b><br/>"
            "<span style='color:#4b5563; font-size:0.85rem;'>📍 {region} · {theme}</span><br/>"
            "<hr style='margin:6px 0; border-color:#e5e7eb;'/>"
            "<span style='color:#1f2937; font-size:0.85rem;'>🚆 {transit}</span><br/>"
            "<span style='font-size:0.82rem; color:#15803d; display:block; margin-top:4px;'>💬 \"{curator_note}\"</span>"
            "</div>"
        ),
        "style": {
            "backgroundColor": "#ffffff",
            "color": "#111827",
            "borderRadius": "10px",
            "border": "1px solid #d1d5db",
            "boxShadow": "0 8px 24px rgba(0, 0, 0, 0.12)"
        },
    }

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="light",
    )

    st.pydeck_chart(deck, use_container_width=True)
