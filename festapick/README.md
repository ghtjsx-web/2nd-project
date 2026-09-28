# ⭐ 페스타픽 (FestaPick) - 메인 프로젝트

**체력 맞춤형 축제 여행 큐레이션 웹 애플리케이션**

사용자 본 프로젝트의 핵심 소스 코드가 포함된 디렉터리입니다.

---

## 📂 파일 구성
- `app.py`: 페스타픽 Streamlit 메인 대시보드 및 상세 코스 뷰
- `data.py`: 전국 4대 데이터(축제 1,320건, 착한가격업소 9,563건, 웰니스 694건, 카페 13건) 엔지니어링 & ChromaDB 벡터 RAG 검색
- `prompt.py`: AI 감성 스토리텔링 및 프롬프트 생성/폴백 모듈
- `collect_wellness.py`: 한국관광공사 TourAPI 웰니스 관광지 전수 수집 스크립트
- `DATA_PIPELINE_BRIEFING.md`: 4대 데이터 파이프라인 아키텍처 브리핑 문서
- `data/`: 실제 공공데이터 원천 및 전처리 CSV 파일
- `chromadb_store/`: ChromaDB 임베딩 인덱스 저장소

## 🚀 실행 방법
루트 디렉터리에서:
```bash
streamlit run festapick/app.py
```
또는 루트 디렉터리의 `run_festapick.bat` 실행
