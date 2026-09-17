# 🌿 Hollo [홀로] - 혼자일 때 더 좋은 것들

> **1집구석(1hows.com) 감성의 1인 뚜벅이 저자극 힐링 여행 & 쉼터 라이프스타일 큐레이션 플랫폼**

소음 가득한 일상에서 벗어나, 혼자일 때 비로소 온전해지는 나만의 쉼표를 골라드립니다.  
에너지 배터리 상태(방전~충전), 대중교통 이동시간 한계, 선호 테마를 종합 분석하여 맞춤 쉼터와 저자극 하루 타임라인 코스를 추천합니다.

---

## 📋 1. Git 커밋 컨벤션 (Commit Convention)

협업 시 커밋 메시지는 다음 형식을 준수하여 작성했습니다.

```text
<type>: <description>
```

| Type | 대상 및 목적 | 커밋 메시지 작성 예시 |
| :---: | :--- | :--- |
| **`feat`** | 새로운 기능 개발 | `feat: 에너지 배터리 4단계 선택 칩 추가` |
| **`fix`** | 버그 및 렌더링 오류 수정 | `fix: 컨트롤 덱 화살표 아이콘 글씨 겹침 현상 수정` |
| **`refactor`**| 코드 구조 개선 및 정리 | `refactor: 사이드바 컴포넌트를 컨트롤 덱으로 일원화` |
| **`test`** | 테스트 코드 추가 및 검증 | `test: 4단계 추천 알고리즘 시뮬레이션 검증` |
| **`docs`** | 문서 작성 및 수정 | `docs: app_specification.md 시퀀스 다이어그램 명세 추가` |
| **`prompt`**| AI 프롬프트 튜닝 | `prompt: 저자극 큐레이터 사려 깊은 대화 톤 보강` |
| **`chore`** | 설정 및 패키지 의존성 관리 | `chore: requirements.txt 최소 필수 패키지로 정리` |

---

## ⚡ 2. 환경 설정 및 실행 가이드 (Quick Start)

### 1단계: 가상환경(venv) 활성화
본 프로젝트는 Python 3.10+ 가상환경 사용을 권장합니다.

```bash
# [Windows PowerShell]
.venv\Scripts\Activate.ps1

# [Windows CMD]
.venv\Scripts\activate.bat

# [Mac / Linux]
source .venv/bin/activate
```

### 2단계: 필수 패키지 설치
`hollo_test` 폴더 내에 최적화된 [requirements.txt]를 설치합니다.

```bash
# hollo_test 폴더 내부 또는 루트에서 실행
pip install -r hollo_test/requirements.txt
```

### 3단계: 애플리케이션 실행
메인 실행 파일 위치: **`hollo_test/app.py`**

```bash
# 루트 디렉터리(work2team) 기준 실행:
streamlit run hollo_test/app.py

# 또는 hollo_test 디렉터리로 이동 후 실행:
streamlit run app.py
```
실행 후 터미널에 안내되는 로컬 URL(`http://localhost:8501`)로 웹 브라우저에서 접속합니다.

---

## 🛠️ 3. 기술 스택 구현 현황 (`app.py` 기준)

프로젝트 기획 및 바이브코딩 과정에서 검토된 기술들을 **[✅ 실제 적용된 기술]**과 **[❌ 미사용 및 차기 확장 기술]**로 명확히 분리하여 정리했습니다.

### 3.1. ✅ 현재 `app.py`에 적용된 핵심 기술

| 구분 | 적용 기술 / 라이브러리 | app.py 내 적용 내용 |
| :--- | :--- | :--- |
| **LLM 생성** | OpenAI `gpt-4o-mini` | 사용자 맞춤형 감성 브리핑 노트 생성 (`core/curator.py`) |
| **프롬프트** | `langchain-core`, `langchain-openai` | 자연어 질의 슬롯 추출 및 페르소나 제어 (`core/extractor.py`) |
| **지도 시각화** | `pydeck` | 1~3위 쉼터 좌표 기반 순위별 컬러 핀 렌더링 (`ui/map_view.py`) |
| **데이터 가공** | `pandas` | 쉼터 JSON 데이터를 지도 좌표 데이터프레임으로 변환 (`ui/map_view.py`) |
| **시퀀스 순서도** | `Mermaid.js` | 전체 아키텍처 및 3대 인터랙션 다이어그램 명세 (`app_specification.md`) |
| **형상 관리** | `Git` / `GitHub` | 7대 커밋 컨벤션 기반 형상 관리 및 협업 (Repository) |

<br>

### 3.2. ❌ 미사용 및 차기 로드맵 기술 (사유 & 대체 구현)
>>> 진행 확정 시 추가. 테스트 파일에서는 간단하게만 구현함

| 미사용 기술 | 미사용 사유 | app.py 내 대체 구현 방식 |
| **LCEL / RAG** | 단순 비정형 검색보다 10대 지표 정밀 필터링 우선 | 자체 JSON DB + 동적 가중치 랭킹 알고리즘 |
| **LangGraph** | 복잡한 순환 분기 없이 선형 파이프라인으로 충분 | 단일 오케스트레이터 (`hollo_curator`) 순차 실행 |
| **AI Agent** | 도구 자율 호출 시 발생하는 불필요한 지연 방지 | 4단계 확정적 추천 엔진 (`recommender_engine`) |
| **NumPy** | 별도 수치 행렬 연산 없이 기본 연산으로 충분 | Python 표준 수식 및 Pandas 연산 활용 |
| **공공데이터 API** | 1인 뚜벅이/저자극 특화 지표(한적함 등) 데이터 부재 | 에디터 직접 실측 10대 Feature 자체 데이터셋 구축 |
| **DB 시각화 툴** | 무거운 RDBMS 대시보드 대신 가벼운 UI 집중 | 16:10 매거진 카드 쇼케이스 + Pydeck 지도 |
| **모델 튜닝/양자화** | 클라우드 API 호출로 인프라 비용 및 메모리 최적화 | 경량화 클라우드 LLM (`gpt-4o-mini`) 활용 |

---

## 📂 4. 프로젝트 폴더 구조

```text
hollo_test/
├── .streamlit/
│   └── config.toml           # 1집구석 라이트 테마 & 서버 설정
├── core/                     # 핵심 AI 및 추천 알고리즘 엔진
│   ├── curator.py            # AI 큐레이터 총괄 오케스트레이터
│   ├── extractor.py          # 사용자 자연어 질의 슬롯 추출기 (LLM + Rule-based)
│   ├── prompts.py            # 큐레이터 페르소나 및 브리핑 프롬프트
│   └── recommender.py        # 4단계 동적 가중치 랭킹 & 코스 압축 추천기
├── data/
│   └── places.json           # 12대 대표 힐링 쉼터 데이터셋 (10대 Feature 점수)
├── services/
│   └── place_service.py      # 장소 데이터 조회 및 1차 하드 필터 서비스
├── ui/                       # 화면 UI 컴포넌트 & 스타일
│   ├── control_deck.py       # 플로팅 미니멀 세부 필터 덱 (아코디언)
│   ├── energy_input.py       # Hero 섹션, 감성 캡슐 칩, 검색창, 4단 배터리
│   ├── map_view.py           # Pydeck 인터랙티브 카토 라이트 지도
│   ├── recommendation_card.py# 16:10 매거진 카드 3열 그리드 & 찜하기
│   └── style.css             # 딥 그린(#056608) Pretendard 전역 스타일시트
├── app.py                    # 메인 Streamlit 실행 애플리케이션
├── app_specification.md      # 초보 개발자/디자이너를 위한 아키텍처 & 시퀀스 다이어그램 명세표
├── config.py                 # 서비스 전역 설정 (4단계 배터리 가중치 & 5대 페르소나 정의)
├── README.md                 # 본 프로젝트 안내서
└── requirements.txt          # 프로젝트 최소 필수 의존성 라이브러리 목록
```

---

## 🎨 5. 디자인 시스템 가이드
- **메인 포인트 컬러:** 딥 그린 (`#056608`)
- **서브 포인트 컬러:** 세이지 틴트 (`#eaf5ea`)
- **배경:** 오프 화이트 (`#fafbfa`) & 순백색 카드 (`#ffffff`)
- **타이포그래피:** Pretendard (가독성 100% 보장)
- **컴포넌트:** 둥근 알약 캡슐(Pill Button), 16:10 카드 비율 고정, `st.html` 기반 안전한 마크다운 분리 스타일링