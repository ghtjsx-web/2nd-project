# 2nd-project

이 저장소는 **직접 개발 중인 메인 프로젝트(`festapick/`)**와 **참고용 데모 프로젝트(`latest_demo/`)**로 완전히 분리되어 관리됩니다.

---

## 📁 디렉터리 구조 및 가이드

```text
2차프로젝트/
├── 📂 festapick/                 ⭐ [내가 만든 메인 프로젝트: 페스타픽 (FestaPick)]
│   ├── app.py                   # Streamlit 메인 웹 애플리케이션
│   ├── data.py                  # 4대 공공데이터 전처리 및 ChromaDB 벡터 RAG 파이프라인
│   ├── prompt.py                # AI 맞춤형 스토리텔링 프롬프트 및 폴백 생성 모듈
│   ├── collect_wellness.py      # 한국관광공사 TourAPI 웰니스 공공데이터 수집 스크립트
│   ├── DATA_PIPELINE_BRIEFING.md# 데이터 파이프라인 아키텍처 브리핑 문서
│   ├── 📂 data/                 # 축제, 착한가격업소, 웰니스, 카페 공공데이터 CSV
│   └── 📂 chromadb_store/       # ChromaDB 임베딩 벡터 저장소
│
├── 📂 latest_demo/              📌 [참고용 데모 프로젝트: Fest & Rest (LangGraph)]
│   ├── app.py                   # 데모용 Streamlit UI
│   ├── agent.py                 # LangGraph 기반 오케스트레이터 파이프라인
│   ├── data.py                  # 데모용 공공데이터 모듈
│   └── 📂 data/                 # 데모 데이터
│
├── 📂 backup_my_work/           🛡️ [작업물 자동 안전 백업 저장소]
│   └── festapick/               # 실시간 동기화되는 백업본
│
├── 📄 run_festapick.bat         🚀 페스타픽 바로 실행 (더블클릭)
├── 📄 run_demo.bat              🔍 데모 바로 실행 (더블클릭)
└── 📄 README.md                 # 본 안내 문서
```

---

## 🚀 애플리케이션 실행 방법

### 1. 내가 만든 메인 프로젝트 (페스타픽) 실행
```bash
# 방법 1: 터미널에서 실행
streamlit run festapick/app.py

# 방법 2: 배치 파일 더블클릭
run_festapick.bat
```

### 2. 참고용 데모 프로젝트 실행
```bash
# 방법 1: 터미널에서 실행
cd latest_demo
streamlit run app.py

# 방법 2: 배치 파일 더블클릭
run_demo.bat
```

---

## 🌟 페스타픽(FestaPick) 주요 핵심 기능
1. **🎉 전국 지자체 대표 문화축제 전수 DB & RAG 파이프라인** (1,320건 전수 DB 기반 무중단 0초 조회)
2. **🍽️ 행정안전부 착한가격업소 실시간 연계** (비식품 정밀 필터링 및 동일 시/군/구 착한 맛집 매칭)
3. **📸 축제 맞춤 인생샷 포토스팟** (지형 기반 사실 기반 매칭 및 할루시네이션 원천 차단)
4. **🌲 문체부 인증 웰니스 힐링지 & 인근 공영주차장 연계** (체력 배터리별 4단계 최적 동선 패키징)
