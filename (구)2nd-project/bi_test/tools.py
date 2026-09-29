"""
tools.py
데이터 분석가 & 지식 탐색기 도구 모음
- Vision AI 위성 영상 분석 (더미)
- 기후-병해충 지식 베이스 RAG 검색 (더미)
- 제주 지역별 위경도 및 위험도 매핑 데이터 (더미)
"""

import pandas as pd


def get_dummy_vision_analysis() -> str:
    """
    위성 영상 및 해양 기상 관측 기반 Vision AI 분석 결과 (더미)
    """
    return (
        "🛰️ [Vision AI 위성 관측 분석]\n"
        "- 관측 영역: 한반도 남해안 및 제주 남단 해역\n"
        "- 감지 현황: 평년 대비 해수면 온도 +1.8°C 이상 상승 패턴 감지\n"
        "- 이상 징후: 대규모 고온 다습 수증기단이 제주 남서부 해안으로 지속 유입 중\n"
        "- 단기 전망: 72시간 이내 국지성 집중호우 구름대 급격 발달 위험도 '높음'"
    )


def get_dummy_rag_search(query: str = "") -> str:
    """
    농업 기후 빅데이터 & 과거 병해충 발병 이력 RAG 검색 (더미)
    """
    return (
        "📚 [과거 기후-병해충 지식베이스 RAG 검색 결과]\n"
        f"- 매칭 쿼리: '{query if query else '가을철 기후 및 병해충 위험도'}'\n"
        "- 과거 유사 패턴 분석(2020, 2022년 동기): 유사 해수면 온도 상승 시 가을 폭우 확률 80%\n"
        "- 작물 영향: 감귤 과습으로 인한 '감귤 무름병(역병)' 및 배추 '연부병' 발병률 3.4배 급증\n"
        "- 권장 대응: 조기 배수로 정비, 배수 불량 과원 침수 방지제 및 살균제 살포 권고"
    )


def get_dummy_map_data() -> pd.DataFrame:
    """
    제주도 주요 농업 지역의 위도/경도 및 재해 위험도 점수 DataFrame (더미)
    Streamlit st.map() 호환 (lat, lon 컬럼 필수 포함)
    """
    data = [
        {"region": "서귀포시 남원읍", "lat": 33.2798, "lon": 126.7196, "crop": "노지감귤", "risk_score": 92, "risk_level": "심각"},
        {"region": "서귀포시 표선면", "lat": 33.3268, "lon": 126.8312, "crop": "하우스감귤", "risk_score": 85, "risk_level": "경고"},
        {"region": "제주시 애월읍", "lat": 33.4623, "lon": 126.3314, "crop": "가을배추/브로콜리", "risk_score": 78, "risk_level": "경고"},
        {"region": "서귀포시 대정읍", "lat": 33.2268, "lon": 126.2514, "crop": "마늘/양파", "risk_score": 64, "risk_level": "주의"},
        {"region": "제주시 구좌읍", "lat": 33.5226, "lon": 126.8524, "crop": "당근", "risk_score": 72, "risk_level": "경고"},
        {"region": "서귀포시 중문동", "lat": 33.2531, "lon": 126.4258, "crop": "한라봉/천혜향", "risk_score": 88, "risk_level": "심각"},
        {"region": "제주시 조천읍", "lat": 33.5352, "lon": 126.6348, "crop": "단호박/메밀", "risk_score": 58, "risk_level": "주의"},
    ]
    return pd.DataFrame(data)
