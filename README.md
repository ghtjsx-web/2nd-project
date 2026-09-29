# 🌿 페스타픽 (FestaPick) - 체력 맞춤형 축제 여행 큐레이션

전국 1,264건 지자체 대표 문화축제와 행정안전부 착한가격업소, 전국 공영주차장, 한국관광공사 웰니스 관광지를 지능적으로 융합한 **체력 & 동행 맞춤형 힐링 여행 큐레이션 웹 애플리케이션**입니다.

---

## 📁 프로젝트 구조 (Directory Structure)

```text
2nd-project/
├── 📄 DATA_DICTIONARY.md          # 4대 공공데이터셋 상세 명세서
├── 📄 validate_datasets.py        # 데이터셋 무결성 자동 검증 스크립트
├── 📄 README.md                   # 프로젝트 종합 안내 문서
├── 📄 requirements.txt            # 필수 파이썬 라이브러리 목록
├── 📄 run_festapick.bat           # 원클릭 실행 배치 파일
│
└── 📁 festapick/                  # 페스타픽(FestaPick) 핵심 3대 실행 파일 체제
    ├── 🐍 app.py                  # Streamlit 메인 웹 대시보드
    ├── 🐍 data.py                 # 4대 공공데이터 전처리, ChromaDB RAG, 웰니스 수집 & 좌표 보강
    ├── 🐍 agent.py                # AI 에이전트 추론, 프롬프트 엔지니어링 및 스토리텔링 생성기
    ├── 📄 DATA_PIPELINE_BRIEFING.md # 데이터 파이프라인 아키텍처 브리핑 문서
    │
    └── 📁 data/                   # 전수 정제 완료된 4대 공공데이터 CSV
        ├── 🎪 festivals.csv       # 전국 문화축제 전수 데이터 (1,264건, 실내/야외 태그 완비)
        ├── 🍲 good_price_stores.csv # 행정안전부 착한가격업소 외식/카페 데이터 (9,563건)
        ├── 🅿 parkings.csv        # 전국 공영주차장 데이터 (18,883건)
        └── 🌿 wellness.csv        # 한국관광공사 웰니스 관광지 데이터 (694건)
```

---

## 🚀 애플리케이션 실행 방법 (Getting Started)

### 1단계: 필수 라이브러리 설치
프로젝트 루트 디렉터리에서 의존성 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

### 2단계: 환경 변수(.env) 설정 가이드
프로젝트 루트 또는 `festapick/` 디렉터리에 `.env` 파일을 생성하고 아래와 같이 필요한 키를 설정합니다.
```env
# 필수: 한국관광공사 TourAPI 서비스키 (웰니스 데이터 수집용)
TOUR_API_KEY=your_tour_api_key

# 선택: 실시간 AI 에디터 맞춤형 스토리텔링 생성용 (미입력 시 룰 기반 고품질 에세이로 자동 폴백)
OPENROUTER_API_KEY=your_openrouter_key  # (선택: 실시간 AI 에디터 스토리텔링용)
OPENAI_API_KEY=your_openai_key          # (선택: 2차 폴백용)
```

### 3단계: 애플리케이션 실행
- **방법 1 (터미널 명령어)**:
  ```bash
  streamlit run festapick/app.py
  ```
- **방법 2 (윈도우 탐색기 원클릭)**:
  `run_festapick.bat` 배치 파일을 더블클릭하면 로컬 서버와 웹 브라우저가 자동 실행됩니다.

> [!TIP]
> **전체 1,264건 축제 전수 데이터 로드 안내 (`IS_DEV_MODE`)**  
> 현재 개발 및 테스트 속도 최적화를 위해 `IS_DEV_MODE = True`로 설정되어 있습니다.  
> **전체 1,264건 축제 전수 데이터를 로드하려면 `app.py` 및 `data.py`의 `IS_DEV_MODE = False`로 변경하세요.**

---

## 🌟 페스타픽(FestaPick) 주요 핵심 기능
1. **🎉 전국 지자체 대표 문화축제 전수 DB & RAG 파이프라인** (1,264건 전수 DB 기반 무중단 0초 조회, 실내/야외 태깅)
2. **🍽️ 행정안전부 착한가격업소 실시간 연계** (비외식업 100% 필터링, 정수형 가격 포맷 규격화)
3. **📸 축제 맞춤 인생샷 포토스팟** (지형 기반 사실 기반 매칭 및 할루시네이션 원천 차단)
4. **🌲 문체부 인증 웰니스 힐링지 & 인근 공영주차장 연계** (체력 배터리별 4단계 최적 동선 패키징)
5. **📊 데이터셋 품질 자동 검증 체계** (`python validate_datasets.py` 무결성 100% 검증 지원)
