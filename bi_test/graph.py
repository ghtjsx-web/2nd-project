"""
graph.py
LangGraph 기반 기후-농업 BI 파이프라인 오케스트레이터
- State 정의: 사용자 쿼리 및 분석 중간/최종 데이터 저장
- 노드 구성: START -> manager_agent -> END
"""

from typing import TypedDict, Optional, Any
import pandas as pd
from langgraph.graph import StateGraph, START, END
from bi_test.agents import run_manager_agent


# 1. 워크플로우 상태(State) 정의
class ClimateAgriState(TypedDict):
    query: str
    vision_data: Optional[str]
    rag_data: Optional[str]
    map_data: Optional[Any]  # pd.DataFrame
    final_report: Optional[str]


# 2. StateGraph 생성 및 노드/엣지 연결
def build_climate_agri_graph():
    """
    기후-농업 BI 워크플로우 그래프 빌더
    """
    workflow = StateGraph(ClimateAgriState)

    # Manager Agent 노드 등록
    workflow.add_node("manager_agent", run_manager_agent)

    # 파이프라인 흐름: 시작(START) -> manager_agent -> 종료(END)
    workflow.add_edge(START, "manager_agent")
    workflow.add_edge("manager_agent", END)

    # 그래프 컴파일
    return workflow.compile()


# 싱글톤 그래프 인스턴스
climate_agri_app = build_climate_agri_graph()


def run_pipeline(query: str) -> dict:
    """
    외부(Streamlit 등)에서 호출하기 편하도록 감싼 파이프라인 실행 헬퍼 함수
    """
    initial_state: ClimateAgriState = {
        "query": query,
        "vision_data": None,
        "rag_data": None,
        "map_data": None,
        "final_report": None,
    }
    result = climate_agri_app.invoke(initial_state)
    return result
