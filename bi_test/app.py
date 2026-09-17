"""
app.py
기후-농업 비즈니스 인텔리전스(Climate-Agri BI) 대시보드
- Streamlit 기반 인터랙티브 UI
- tools.py의 지리공간 위험도 데이터를 st.map()으로 시각화
- graph.py의 LangGraph 워크플로우를 실행하여 최종 리포트 출력
"""

import streamlit as st
import pandas as pd
from tools import get_dummy_map_data
from graph import run_pipeline

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="기후-농업 비즈니스 인텔리전스",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 스타일 적용 (모던 대시보드 카드 스타일)
st.markdown(
    """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 16px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .report-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }
    .risk-badge-severe {
        color: #d32f2f;
        font-weight: bold;
    }
    .risk-badge-warn {
        color: #f57c00;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 2. 사이드바 구성 (사용자 입력 & 제어판)
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=600&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("🌾 Agri-Climate BI")
    st.caption("제주 권역 실증 프로토타입 v0.1")
    st.markdown("---")

    st.subheader("🔍 분석 질의 입력")
    
    # 추천 질의 샘플 버튼
    st.markdown("**💡 추천 질의 선택:**")
    col_q1, col_q2 = st.columns(2)
    sample_query = ""
    with col_q1:
        if st.button("🍊 감귤 위험도", use_container_width=True):
            sample_query = "제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘"
    with col_q2:
        if st.button("🥬 가을배추 폭우", use_container_width=True):
            sample_query = "가을철 해수면 온도 상승과 배추 무름병 발병 영향 분석"

    # 질문 입력창
    default_prompt = sample_query if sample_query else "제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘"
    user_query = st.text_area(
        "분석할 질문을 입력하세요:",
        value=default_prompt,
        height=100,
        placeholder="예: 제주도 남부 기후 변화 및 작물 침수 위험도 분석",
    )

    # 분석 실행 버튼
    run_btn = st.button("🚀 인텔리전스 분석 실행", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🛠️ 시스템 아키텍처 (3인 협업)")
    st.info(
        """
        - **`tools.py`**: 데이터 분석가 & 도구 (Vision AI, RAG, Map)
        - **`agents.py`**: Manager Agent 리포트 합성 로직
        - **`graph.py`**: LangGraph State 워크플로우 오케스트레이션
        - **`app.py`**: Streamlit 통합 대시보드
        """
    )

# 3. 메인 화면 상단: 헤더 및 KPI 메트릭
st.title("🌱 기후-농업 비즈니스 인텔리전스 대시보드")
st.markdown("위성 영상 기반 해양 기후 패턴, 지식베이스 RAG, 공간 위험도 매핑을 융합한 농가 의사결정 지원 시스템입니다.")

# KPI 요약 메트릭 카드 4종
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric(label="해수면 수온 편차 (SST)", value="+1.8 °C", delta="이상 고온 지속", delta_color="inverse")
with m2:
    st.metric(label="가을 폭우 발생 확률", value="80 %", delta="과거 유사 패턴 대조", delta_color="inverse")
with m3:
    st.metric(label="최고 위험 지역", value="서귀포시 남원읍", delta="위험지수 92점", delta_color="inverse")
with m4:
    st.metric(label="방제 대응 골든타임", value="72시간 이내", delta="비 오기 전 선제방제")

st.markdown("---")

# 4. 메인 화면 상단 영역: 공간 위험도 지도 및 세부 데이터
st.subheader("🗺️ 제주도 지역별 농업 재해 위험도 공간 분석")

# tools.py에서 더미 맵 데이터 로드
map_df = get_dummy_map_data()

map_col, table_col = st.columns([3, 2])

with map_col:
    st.markdown("##### 📍 위성/기상 관측 기반 지역별 재해 위험 분포도")
    # st.map을 활용한 위경도 렌더링
    st.map(
        map_df,
        latitude="lat",
        longitude="lon",
        size="risk_score",
        zoom=9,
        use_container_width=True,
    )

with table_col:
    st.markdown("##### 📊 권역별 작물 및 위험 단계 현황")
    # 보기 쉬운 포맷으로 표 표시
    styled_df = map_df[["region", "crop", "risk_score", "risk_level"]].rename(
        columns={
            "region": "관측 지역",
            "crop": "주요 작물",
            "risk_score": "위험도(0~100)",
            "risk_level": "경보 단계",
        }
    )
    st.dataframe(styled_df, use_container_width=True, height=280)

st.markdown("---")

# 5. 메인 화면 하단 영역: LangGraph 실행 및 최종 리포트 렌더링
st.subheader("📑 Manager Agent 종합 비즈니스 인텔리전스 리포트")

# 세션 상태 초기화
if "report_result" not in st.session_state:
    st.session_state.report_result = None

# 사용자가 실행 버튼을 눌렀거나 기존 결과가 없을 때 초기 실행
if run_btn or st.session_state.report_result is None:
    with st.spinner("🤖 LangGraph 오케스트레이터가 도구들을 호출하여 종합 리포트를 생성 중입니다..."):
        result = run_pipeline(user_query)
        st.session_state.report_result = result

result = st.session_state.report_result

# 결과 렌더링
if result and result.get("final_report"):
    st.markdown(
        f"""
        <div class="report-container">
        {result["final_report"]}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 하단 탭: 각 도구별 상세 데이터 검증 (데이터 분석가 / 개발자 협업 확인용)
    st.markdown("#### 🔬 세부 도구 호출 데이터 (Tools Output Verification)")
    tab1, tab2, tab3 = st.tabs(["🛰️ Vision AI 분석", "📚 RAG 검색 결과", "🔄 LangGraph State"])

    with tab1:
        st.code(result.get("vision_data", "데이터 없음"), language="markdown")
    with tab2:
        st.code(result.get("rag_data", "데이터 없음"), language="markdown")
    with tab3:
        st.json({
            "query": result.get("query"),
            "has_vision_data": bool(result.get("vision_data")),
            "has_rag_data": bool(result.get("rag_data")),
            "has_map_data": bool(result.get("map_data") is not None),
            "report_length": len(result.get("final_report", "")),
        })
