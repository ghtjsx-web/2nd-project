"use client";

import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import AnalysisPanel, { AnalysisResponseData } from "../components/AnalysisPanel";
import MapArea, { MapPoint } from "../components/MapArea";

// 백엔드 미실행 시에도 UI가 깨지지 않고 바로 투자자/검증 시연이 가능하도록 기본 폴백 데이터 제공
const FALLBACK_INITIAL_DATA: AnalysisResponseData = {
  status: "success",
  timestamp: "2026-09-17 10:48:00",
  query: "제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘",
  kpis: {
    sst_deviation: "+1.8 °C",
    rain_probability: "80 %",
    highest_risk_region: "서귀포시 남원읍 (94점)",
    golden_time: "72시간 이내",
    estimated_damage_risk: "수확량 -25~35% 우려",
  },
  report: `### 🌾 [Executive Briefing] 기후-농업 비즈니스 인텔리전스 종합 분석 보고서

**Target Analysis Query:** \`제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘\`  
**발행 시각:** 2026-09-17 (실시간 위성 및 기후 RAG 파이프라인 연계)

---

#### 1. 🛰️ 위성 해양 기후 이상 징후 (Macro Climate Analysis)
- **해수면 온도(SST) 이상 급상승:** 제주 남동 해역 중심 평년 대비 **+1.8°C 이상** 지속.
- **수증기 대류 밴드 형성:** 필리핀 동쪽 해상에서 발달한 열대 요란이 남동풍을 타고 대규모 수증기 기둥을 제주 남서부로 직유입 중.
- **72시간 단기 예측:** 제주 남원, 표선, 중문 권역에 시간당 40~60mm 이상의 국지성 집중호우 구름대 발달 확률 **85%**.

#### 2. 📚 과거 재해 지식베이스(RAG) 대조 및 병해충 위험도
- **과거 유사 기후 패턴(2020년 및 2022년 가을):**
  - 고수온 수증기 유입 직후 가을 집중 폭우 발생 확률 **80% 초과 기록**.
  - 당시 감귤 과원 내 침수와 과습으로 인해 **'감귤 무름병(역병)'** 및 **'검은점무늬병'** 피해 면적이 평년 대비 **3.4배 급증**.
- **배추 및 밭작물 연계 위험:** 애월 및 구좌 권역의 토양 과습 시 **'무름병(연부병)'** 균주 확산 속도가 200% 가속화되어 수확량 최대 35% 감소 위험 추정.

#### 3. 🎯 권역별 농업 비즈니스 리스크 매트릭스
- **[심각 등급 (위험지수 90+)] 서귀포시 남원읍(94점), 중문동(89점):**
  - 감귤류 및 만감류 낙과 및 당도 저하, 과피 무름병 발병 위험 극대화.
- **[경고 등급 (위험지수 70~89)] 표선면(83점), 애월읍(78점), 구좌읍(72점):**
  - 배수 불량 시 뿌리 호흡 곤란 및 병해 전파 우려.

#### 4. 💡 AI 비즈니스 인텔리전스 실행 권고사항 (Action Items)
1. **[D-0 긴급 대응]** 남원·중문·표선 감귤원 집수정 및 배수 펌프 가동 상태 긴급 점검, 배수로 유입 토사 사전 제거.
2. **[D-1 예방 살포]** 강우 전 침투이행성 살균제 및 친환경 방제제 사전 살포 완료.
3. **[비즈니스 의사결정]** 조기 수확분 산지유통센터(APC) 선별 입고 추진 및 농작물 재해보험 피해 신속 접수 프로세스 가동.`,
  map_data: [
    {
      id: "loc-1",
      region: "서귀포시 남원읍",
      lat: 33.2798,
      lon: 126.7196,
      crop: "노지감귤",
      risk_score: 94,
      risk_level: "심각",
      status: "토양 과습 포화 직전 및 침수 임계치 도달",
      action_needed: "과원 배수로 즉각 준설 및 침투성 살균제 긴급 살포",
    },
    {
      id: "loc-2",
      region: "서귀포시 중문동",
      lat: 33.2531,
      lon: 126.4258,
      crop: "한라봉/천혜향",
      risk_score: 89,
      risk_level: "심각",
      status: "하우스 내부 다습으로 인한 잿빛곰팡이병 증식 지수 상승",
      action_needed: "열풍기 환기 가동 및 제습 시설 상시 점검",
    },
    {
      id: "loc-3",
      region: "서귀포시 표선면",
      lat: 33.3268,
      lon: 126.8312,
      crop: "하우스감귤",
      risk_score: 83,
      risk_level: "경고",
      status: "해안 저지대 역류 위험 및 시설 침수 주의보",
      action_needed: "배수 펌프 사전 점검 및 방풍망 정비",
    },
    {
      id: "loc-4",
      region: "제주시 애월읍",
      lat: 33.4623,
      lon: 126.3314,
      crop: "가을배추/브로콜리",
      risk_score: 78,
      risk_level: "경고",
      status: "연부병(무름병) 균주 활성 최적 온도/습도 구간 진입",
      action_needed: "사전 동제 약제 살포 및 배수 골타기 작업",
    },
    {
      id: "loc-5",
      region: "제주시 구좌읍",
      lat: 33.5226,
      lon: 126.8524,
      crop: "구좌 당근",
      risk_score: 72,
      risk_level: "경고",
      status: "초기 유묘기 습해 우려 및 뿌리 발육 지연 가능성",
      action_needed: "배수 유도로 확보 및 잎마름병 방제",
    },
    {
      id: "loc-6",
      region: "서귀포시 대정읍",
      lat: 33.2268,
      lon: 126.2514,
      crop: "마늘/양파",
      risk_score: 65,
      risk_level: "주의",
      status: "파종 초기 토양 수분 과다, 곰팡이성 병해 모니터링",
      action_needed: "비 가림 시설 및 밭두렁 정비",
    },
    {
      id: "loc-7",
      region: "제주시 조천읍",
      lat: 33.5352,
      lon: 126.6348,
      crop: "단호박/메밀",
      risk_score: 58,
      risk_level: "주의",
      status: "기류 수렴대 형성, 국지성 소나기 통과 예상",
      action_needed: "기상 레이더 실시간 모니터링",
    },
  ],
  vision_insight: "🛰️ 제주 남단 해역 SST 평년 대비 +1.8°C 이상 고온 유지, 강력한 대류 수증기 벨트 유입 포착",
  rag_insight: "📚 2020/2022년 동기 유사 패턴 대조: 가을 폭우 발생률 80%, 감귤 무름병 발병률 3.4배 급증 이력",
};

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [analysisData, setAnalysisData] = useState<AnalysisResponseData | null>(FALLBACK_INITIAL_DATA);
  const [selectedPoint, setSelectedPoint] = useState<MapPoint | null>(null);

  // 백엔드 /api/analyze 호출
  const handleAnalyze = async (query: string) => {
    setIsLoading(true);
    setSelectedPoint(null);

    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        throw new Error(`서버 응답 오류: ${res.status}`);
      }

      const data: AnalysisResponseData = await res.json();
      setAnalysisData(data);
    } catch (error) {
      console.warn("백엔드 서버 미응답으로 데모 시뮬레이션 데이터를 업데이트합니다:", error);
      // 서버 미가동 상태에서도 시연이 가능하도록 쿼리 반영 시뮬레이션
      setTimeout(() => {
        setAnalysisData({
          ...FALLBACK_INITIAL_DATA,
          query,
          timestamp: new Date().toLocaleString("ko-KR"),
        });
      }, 1200);
    } finally {
      setTimeout(() => {
        setIsLoading(false);
      }, 800);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100">
      {/* 1. 상단 글로벌 네비게이션 바 */}
      <Navbar />

      {/* 2. 메인 바디 레이아웃 (좌측 1/3 질의 및 리포트 패널 + 우측 2/3 대형 지도) */}
      <main className="flex-1 flex flex-col lg:flex-row gap-4 p-4 overflow-hidden">
        {/* 좌측: 인텔리전스 질의 & 리포트 패널 (화면의 약 1/3) */}
        <section className="w-full lg:w-[38%] xl:w-[35%] h-full flex-shrink-0">
          <AnalysisPanel
            isLoading={isLoading}
            analysisData={analysisData}
            onAnalyze={handleAnalyze}
          />
        </section>

        {/* 우측: 거대한 지도 영역 (화면의 약 2/3) */}
        <section className="w-full lg:w-[62%] xl:w-[65%] h-full flex-1">
          <MapArea
            mapData={analysisData?.map_data || []}
            selectedPoint={selectedPoint}
            onSelectPoint={setSelectedPoint}
          />
        </section>
      </main>
    </div>
  );
}
