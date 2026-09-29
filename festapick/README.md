# ⭐ 페스타픽 (FestaPick) - 메인 프로젝트

**체력 맞춤형 축제 여행 큐레이션 웹 애플리케이션**

사용자 본 프로젝트의 핵심 소스 코드가 포함된 디렉터리입니다.

---

## 📂 핵심 3대 실행 파일 구성
- `app.py`: 페스타픽 Streamlit 메인 대시보드 및 체력 맞춤형 4단계 코스 상세 뷰
- `data.py`: 전국 4대 데이터 엔지니어링, ChromaDB 벡터 RAG 검색, 웰니스 수집 및 결측 좌표 자동 보강
- `agent.py`: AI 감성 스토리텔링 큐레이터 에이전트, 프롬프트 엔지니어링 및 무중단 폴백 엔진
- `DATA_PIPELINE_BRIEFING.md`: 4대 데이터 파이프라인 아키텍처 브리핑 문서
- `data/`: 실제 공공데이터 원천 및 전처리 CSV 파일
- `chromadb_store/`: ChromaDB 임베딩 인덱스 저장소

## 🚀 실행 방법 (Getting Started)

### 1단계: 필수 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 2단계: 환경 변수(.env) 설정
```env
TOUR_API_KEY=your_tour_api_key
OPENROUTER_API_KEY=your_openrouter_key  # (선택: 실시간 AI 에디터 스토리텔링용)
OPENAI_API_KEY=your_openai_key          # (선택: 2차 폴백용)
```

### 3단계: 애플리케이션 실행
루트 디렉터리에서:
```bash
streamlit run festapick/app.py
```
또는 루트 디렉터리의 `run_festapick.bat` 더블클릭

> [!TIP]
> **전체 1,264건 축제 전수 데이터를 로드하려면 `app.py` 및 `data.py`의 `IS_DEV_MODE = False`로 변경하세요.**
