"""
agents.py
에이전트 로직 정의
- Manager Agent: Vision AI 분석 도구와 과거 지식 RAG 도구를 호출/취합하여
  최종 의사결정용 기후-농업 비즈니스 인텔리전스 종합 리포트를 생성합니다.
"""

from bi_test.tools import get_dummy_vision_analysis, get_dummy_rag_search, get_dummy_map_data


def run_manager_agent(state: dict) -> dict:
    """
    Manager Agent 노드 함수
    - State에서 사용자 질의(query)를 가져옵니다.
    - tools.py의 도구들을 호출하여 기후 영상 분석 데이터와 과거 지식 RAG 데이터를 수집합니다.
    - 수집된 정보를 종합하여 경영진 및 농가 대상의 실행 가능한 맞춤형 브리핑 리포트를 생성합니다.
    """
    query = state.get("query", "제주도 기후 변화 및 작물 위험도 분석")

    # 1. 도구 호출
    vision_result = get_dummy_vision_analysis()
    rag_result = get_dummy_rag_search(query)
    map_df = get_dummy_map_data()

    # 위험도 통계 추출 (더미)
    high_risk_regions = map_df[map_df["risk_score"] >= 80]["region"].tolist()
    high_risk_str = ", ".join(high_risk_regions)

    # 2. 종합 비즈니스 인텔리전스 리포트 생성 (가짜 리포트 포맷팅)
    final_report = f"""### 🌾 [기후-농업 BI 통합 인텔리전스 브리핑]

> **분석 요청 질의:** `{query}`  
> **상태:** 분석 완료 (위성 기상 관측 + 과거 재해 데이터 + 공간 위험도 분석 연계)

---

#### 1. 핵심 기후 이상 징후 종합
- **해수면 온도 이상 고온 현상:** 제주 남단 해역의 평년 대비 +1.8°C 수온 상승으로 고수온 수증기 벨트 형성.
- **국지성 기상 이변:** 72시간 이내 제주 전역에 급격한 집중호우 및 강우 집중 가능성 포착.

#### 2. 농작물 피해 위험 예측 (AI RAG 연계)
- **과거 유사 패턴(2020/2022) 대조:** 가을 폭우 발생 확률 **80%** 수준 도달.
- **주요 타격 예상 품목:** 
  - **감귤(노지/하우스):** 토양 과습 및 침수에 따른 **'감귤 무름병(역병)'** 급증 우려.
  - **월동 배추 및 밭작물:** 침수 시 **'연부병(무름병)'** 및 뿌리 썩음병 발병 위험 극대화.
- **집중 관리 구역:** **{high_risk_str}** (위험 지수 80점 이상 '경고/심각' 단계)

#### 3. Manager Agent 최종 실행 권고안
1. **긴급 배수로 정비:** 남원·중문·표선 등 고위험 감귤원 중심의 배수로 준설 및 토사 유실 방지망 점검.
2. **선제적 예방 방제:** 올가을 예상치 못한 폭우로 배추/감귤 발병 가능성이 매우 높으므로, 비가 시작되기 전 침투이행성 살균제 및 친환경 방제제 사전 살포 권고.
3. **농가 알림 및 비즈니스 조치:** 지자체 농업기술센터와 연계해 고위험군 농가 대상 'SMS 경보' 발송 및 농작물 재해보험 피해 접수 핫라인 사전 가동.
"""

    return {
        "vision_data": vision_result,
        "rag_data": rag_result,
        "map_data": map_df,
        "final_report": final_report,
    }
