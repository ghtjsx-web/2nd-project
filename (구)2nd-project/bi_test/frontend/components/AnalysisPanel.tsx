"use client";

import React, { useState } from "react";
import {
  Send,
  Sparkles,
  Bot,
  FileText,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  CloudRain,
  Thermometer,
  ShieldAlert,
  Loader2,
  Copy,
  Check,
} from "lucide-react";
import { MapPoint } from "./MapArea";

export interface KpiMetrics {
  sst_deviation: string;
  rain_probability: string;
  highest_risk_region: string;
  golden_time: string;
  estimated_damage_risk: string;
}

export interface AnalysisResponseData {
  status: string;
  timestamp: string;
  query: string;
  kpis: KpiMetrics;
  report: string;
  map_data: MapPoint[];
  vision_insight: string;
  rag_insight: string;
}

interface AnalysisPanelProps {
  isLoading: boolean;
  analysisData: AnalysisResponseData | null;
  onAnalyze: (query: string) => void;
}

export default function AnalysisPanel({
  isLoading,
  analysisData,
  onAnalyze,
}: AnalysisPanelProps) {
  const [inputQuery, setInputQuery] = useState(
    "제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘"
  );
  const [copied, setCopied] = useState(false);

  const samplePrompts = [
    { title: "🍊 감귤 과원 위험도", query: "제주도 기후 변화에 따른 감귤 농장 위험도 분석해 줘" },
    { title: "🥬 가을배추 폭우 침수", query: "가을철 해수면 온도 상승과 배추 무름병 발병 영향 분석" },
    { title: "⚡ 72시간 긴급 방제", query: "제주 남단 고수온 수증기 유입에 따른 긴급 방제 권고안" },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;
    onAnalyze(inputQuery.trim());
  };

  const handleCopyReport = () => {
    if (!analysisData?.report) return;
    navigator.clipboard.writeText(analysisData.report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full h-full flex flex-col bg-slate-950/70 border border-slate-800/80 rounded-2xl backdrop-blur-xl overflow-hidden shadow-2xl">
      {/* 1. 패널 헤더 */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-900/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-slate-100 flex items-center gap-2">
              AI 비즈니스 인텔리전스 패널
              <span className="text-[10px] bg-emerald-400/10 text-emerald-300 font-mono px-2 py-0.5 rounded-full border border-emerald-500/20">
                LIVE AGENT
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              위성 관측 및 기후-병해충 RAG 오케스트레이션
            </p>
          </div>
        </div>
      </div>

      {/* 2. 스크롤 가능한 본문 영역 (질의 입력 및 결과 리포트) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* 질문 입력 및 샘플 프롬프트 섹션 */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-medium flex items-center gap-1.5 text-slate-300">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              추천 전략 질의
            </span>
          </div>

          {/* 추천 프롬프트 칩 */}
          <div className="flex flex-wrap gap-1.5">
            {samplePrompts.map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setInputQuery(item.query)}
                className="text-xs px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 transition leading-snug"
              >
                {item.title}
              </button>
            ))}
          </div>

          {/* 입력창 & 전송 버튼 */}
          <div className="relative">
            <textarea
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="예: 제주도 남부 기후 변화 및 작물 침수 위험도 분석..."
              rows={3}
              className="w-full bg-slate-900/90 text-slate-100 placeholder-slate-500 text-xs rounded-xl p-3 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition resize-none pr-12"
            />
            <button
              type="submit"
              disabled={isLoading || !inputQuery.trim()}
              className="absolute right-2.5 bottom-3 p-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition shadow-lg shadow-emerald-500/20"
              title="분석 실행"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </form>

        {/* 3. 분석 진행 상태 애니메이션 (로딩 스피너) */}
        {isLoading && (
          <div className="p-6 rounded-xl bg-slate-900/90 border border-emerald-500/30 flex flex-col items-center justify-center text-center space-y-3 animate-pulse">
            <div className="relative w-12 h-12 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-2 border-emerald-500/20 border-t-emerald-400 animate-spin" />
              <Bot className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-200">
                멀티모달 인텔리전스 파이프라인 가동 중...
              </p>
              <div className="text-[11px] text-emerald-400 font-mono mt-1 space-y-0.5">
                <p>1. 천리안-2A 위성 해양 온도 수신 완료</p>
                <p>2. 과거 10개년 기후-병해충 RAG 지식 대조 중</p>
                <p>3. 제주 권역별 GIS 위험 지수 매핑 합성 중</p>
              </div>
            </div>
          </div>
        )}

        {/* 4. 분석 결과 표시 (투자자 맞춤형 고품질 리포트) */}
        {!isLoading && analysisData && (
          <div className="space-y-4 animate-in fade-in duration-300">
            {/* KPI 요약 그리드 */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                  <Thermometer className="w-3 h-3 text-rose-400" />
                  해수면 온도(SST)
                </span>
                <span className="text-sm font-bold text-rose-400 font-mono">
                  {analysisData.kpis.sst_deviation}
                </span>
                <span className="text-[9px] text-slate-500 block">이상 고온 지속</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                  <CloudRain className="w-3 h-3 text-cyan-400" />
                  가을 폭우 확률
                </span>
                <span className="text-sm font-bold text-cyan-400 font-mono">
                  {analysisData.kpis.rain_probability}
                </span>
                <span className="text-[9px] text-slate-500 block">과거 패턴 대조</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3 text-amber-400" />
                  최고 위험 지역
                </span>
                <span className="text-xs font-bold text-amber-300 block truncate">
                  {analysisData.kpis.highest_risk_region}
                </span>
                <span className="text-[9px] text-slate-500 block">과원 침수 주의보</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 block flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  방제 골든타임
                </span>
                <span className="text-xs font-bold text-emerald-400 block">
                  {analysisData.kpis.golden_time}
                </span>
                <span className="text-[9px] text-slate-500 block">선제 살포 권고</span>
              </div>
            </div>

            {/* 메인 브리핑 리포트 */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800/90 text-xs text-slate-300 relative group">
              <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-800">
                <span className="font-bold text-slate-200 flex items-center gap-1.5 text-xs">
                  <FileText className="w-3.5 h-3.5 text-emerald-400" />
                  종합 인텔리전스 브리핑 리포트
                </span>
                <button
                  onClick={handleCopyReport}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2 py-1 rounded bg-slate-800/60 hover:bg-slate-800 transition"
                  title="리포트 복사"
                >
                  {copied ? (
                    <>
                      <Check className="w-3 h-3 text-emerald-400" />
                      <span className="text-emerald-400">복사됨</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>복사</span>
                    </>
                  )}
                </button>
              </div>

              {/* 리포트 텍스트 (마크다운 포맷팅 렌더) */}
              <div className="whitespace-pre-line leading-relaxed text-slate-300 font-sans text-xs space-y-2">
                {analysisData.report}
              </div>
            </div>

            {/* 도구별 AI 데이터 투명성 카드 (Sub-Agent Outputs) */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-[11px] space-y-2">
              <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                원천 관측 데이터 신뢰도
              </div>
              <div className="p-2 rounded bg-slate-950/60 border border-slate-850 text-slate-300">
                <span className="text-emerald-400 font-semibold block mb-0.5">
                  🛰️ Satellite Vision AI:
                </span>
                {analysisData.vision_insight}
              </div>
              <div className="p-2 rounded bg-slate-950/60 border border-slate-850 text-slate-300">
                <span className="text-cyan-400 font-semibold block mb-0.5">
                  📚 Historical Disaster RAG:
                </span>
                {analysisData.rag_insight}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
