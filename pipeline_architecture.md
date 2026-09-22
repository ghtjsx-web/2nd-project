# 🎪 Fest & Rest AI 파이프라인 아키텍처 (LangGraph)

본 문서는 `agent.py`에 구현된 **초개인화 로컬 축제 & 쉼터 큐레이션 (Fest & Rest)** 백엔드 AI 파이프라인의 구조 및 데이터 흐름을 시각화한 Mermaid 다이어그램입니다.

---

## 1. 전체 파이프라인 워크플로우 (Pipeline Workflow)

```mermaid
graph TD
    %% 노드 정의 및 스타일링
    START([🏁 START]):::boundary
    END_NODE([🎯 END]):::boundary

    subgraph Inputs ["📥 프론트엔드 & 외부 API 입력"]
        UI["👤 user_inputs<br/>(stamina, companion, region,<br/>selected_festival, extra_details)"]:::input
        API["🌐 api_data<br/>(parking_lots, model_restaurants,<br/>tourist_spots)"]:::input
    end

    subgraph LangGraph ["⚡ LangGraph StateGraph (PipelineState)"]
        N1["<b>1. analyze</b><br/>analyze_stamina_and_intent<br/>- 체력 3단계 분할 (Low/Mod/High)<br/>- LLM 의도 및 제약사항 추출"]:::node
        N2["<b>2. classify</b><br/>classify_events_node<br/>- 예약 필수 vs 자유 참여 이벤트 분류<br/>- booking_tip 가공 보존"]:::node
        N3["<b>3. editor</b><br/>generate_magazine_article_node<br/>- 4대 제약조건 준수 매거진 기사 생성<br/>- 사용자 의도 100% 반영 LLM 에디터"]:::node
        N4["<b>4. format_pins</b><br/>format_folium_pins_node<br/>- Folium 팝업/마커 메타데이터 정제<br/>- (위/경도 유효성 및 팝업 타이틀)"]:::node
    end

    subgraph Outputs ["📤 최종 출력 (run_processing_pipeline)"]
        OUT["📦 Result Dictionary<br/>- article_content (매거진 마크다운 기사)<br/>- event_info (예약 필수/자유 이벤트 리스트)<br/>- map_markers (Folium 핀 메타데이터)"]:::output
    end

    %% 연결선
    UI --> N1
    API --> N1
    START --> N1
    N1 -->|상태 전이: guideline, intent_analysis| N2
    N2 -->|상태 전이: event_info| N3
    N3 -->|상태 전이: article_content| N4
    N4 --> END_NODE
    N4 --> OUT

    %% 스타일 클래스
    classDef boundary fill:#4A5568,stroke:#2D3748,stroke-width:2px,color:#FFFFFF,font-weight:bold;
    classDef input fill:#EBF8FF,stroke:#3182CE,stroke-width:2px,color:#2B6CB0;
    classDef node fill:#EDFDFD,stroke:#00A3C4,stroke-width:2px,color:#0987A0;
    classDef output fill:#F0FFF4,stroke:#38A169,stroke-width:2px,color:#276749;
```

---

## 2. 상태 전이 및 데이터 흐름 (State Transition & Data Flow)

```mermaid
sequenceDiagram
    autonumber
    actor User as 프론트엔드 (app.py)
    participant Pipe as run_processing_pipeline
    participant N1 as [Node 1] analyze
    participant N2 as [Node 2] classify
    participant N3 as [Node 3] editor
    participant N4 as [Node 4] format_pins
    participant LLM as OpenAI GPT-4o-mini

    User->>Pipe: user_inputs + api_data 전달
    Note over Pipe: stamina 정규화, 축제 데이터 정제,<br/>초기 PipelineState 조립
    
    Pipe->>N1: State 전달
    N1->>LLM: INTENT_ANALYSIS_PROMPT (체력, 동반자, extra_details)
    LLM-->>N1: JSON (core_needs, mobility_constraint, parking_focus)
    Note over N1: activity_level, movement_radius,<br/>activity_ratio, strategy_guideline 도출

    N1->>N2: 업데이트된 State 전달
    Note over N2: 프로그램 & 명소 텍스트 키워드 스캔<br/>(예약 필수 / 자유 참여 분류)

    N2->>N3: 업데이트된 State 전달
    Note over N3: 주차장 총 주차면수 정렬,<br/>모범식당 리스트 및 이벤트 정보 포맷팅
    N3->>LLM: MAGAZINE_EDITOR_SYSTEM_PROMPT<br/>(4대 제약 조건 + 초개인화 사용자 요구사항)
    LLM-->>N3: 트렌디 매거진 기사 마크다운 (article_content)

    N3->>N4: 업데이트된 State 전달
    Note over N4: Folium 지도 핀 정제<br/>(좌표 무결성 검증, popup_title, desc, menu, fee)

    N4-->>User: 최종 반환 {article_content, event_info, map_markers}
```

---

## 3. 핵심 4대 제약 조건 반영 구조

```mermaid
mindmap
  root((Fest & Rest<br/>4대 핵심 제약 조건))
    공영주차장 데이터 제한
      실시간 잔여 대수 언급 금지
      고정 데이터인 총 주차면수 기준 정렬
    실시간 혼잡도 추적 제외
      특정 시간대를 골든타임으로 단정 금지
      체력 기반의 정적 관람 및 분산 꿀팁 제공
    모범식당 데이터 전용
      외부 임의 식당 생성 금지 할루시네이션 방지
      공인 착한가격업소/모범식당 명단 내에서만 추천
    Folium 지도 핀 최적화
      가짜 핀 생성 금지 실제 위경도만 표시
      팝업 카드 전용 메타데이터 제공
```
