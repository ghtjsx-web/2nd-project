"use client";

import React, { useState } from "react";
import {
  MapPin,
  Layers,
  ZoomIn,
  ZoomOut,
  Compass,
  AlertTriangle,
  Info,
  Maximize2,
  Filter,
  Eye,
} from "lucide-react";

export interface MapPoint {
  id: string;
  region: string;
  lat: number;
  lon: number;
  crop: string;
  risk_score: number;
  risk_level: string;
  status: string;
  action_needed: string;
}

interface MapAreaProps {
  mapData: MapPoint[];
  selectedPoint: MapPoint | null;
  onSelectPoint: (point: MapPoint | null) => void;
}

export default function MapArea({
  mapData,
  selectedPoint,
  onSelectPoint,
}: MapAreaProps) {
  const [activeLayer, setActiveLayer] = useState<"risk" | "satellite" | "radar">("risk");
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  // 제주도 경계 기준 대략적인 상대 좌표 매핑 계산 (가상 GIS 렌더링용)
  // Lat: 33.15 ~ 33.60, Lon: 126.15 ~ 126.95
  const getRelativePosition = (lat: number, lon: number) => {
    const minLat = 33.15;
    const maxLat = 33.60;
    const minLon = 126.15;
    const maxLon = 126.95;

    const x = ((lon - minLon) / (maxLon - minLon)) * 80 + 10; // 10% ~ 90%
    const y = ((maxLat - lat) / (maxLat - minLat)) * 70 + 15; // 15% ~ 85%
    return { top: `${y}%`, left: `${x}%` };
  };

  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case "심각":
        return "bg-rose-500/20 text-rose-300 border-rose-500/40";
      case "경고":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      default:
        return "bg-blue-500/20 text-blue-300 border-blue-500/40";
    }
  };

  const getPinColor = (score: number) => {
    if (score >= 88) return "text-rose-400 fill-rose-500";
    if (score >= 75) return "text-amber-400 fill-amber-500";
    return "text-cyan-400 fill-cyan-500";
  };

  return (
    <div className="relative w-full h-full min-h-[680px] flex flex-col bg-[#0b101d] rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl">
      {/* 1. 상단 GIS 제어 툴바 */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none">
        {/* 레이어 토글 */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900/90 border border-slate-800 backdrop-blur-md pointer-events-auto shadow-lg">
          <button
            onClick={() => setActiveLayer("risk")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeLayer === "risk"
                ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            농작물 재해 위험도
          </button>
          <button
            onClick={() => setActiveLayer("satellite")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeLayer === "satellite"
                ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            해수면 수온(SST)
          </button>
          <button
            onClick={() => setActiveLayer("radar")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
              activeLayer === "radar"
                ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            기상 강우 레이더
          </button>
        </div>

        {/* GIS 메타정보 및 줌 컨트롤 */}
        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="hidden sm:flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-xl text-[11px] text-slate-300 font-mono backdrop-blur-md">
            <Compass className="w-3.5 h-3.5 text-emerald-400 animate-spin" style={{ animationDuration: "20s" }} />
            <span>JEJU GIS | 33.36°N, 126.53°E</span>
          </div>

          <div className="flex items-center bg-slate-900/90 border border-slate-800 rounded-xl backdrop-blur-md overflow-hidden shadow-lg">
            <button
              onClick={() => setZoomLevel((z) => Math.min(z + 10, 140))}
              className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 transition"
              title="확대"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <span className="text-[11px] text-slate-400 px-1 font-mono">{zoomLevel}%</span>
            <button
              onClick={() => setZoomLevel((z) => Math.max(z - 10, 80))}
              className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 transition"
              title="축소"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 2. 메인 지도 캔버스 영역 (추후 카카오맵 / 구글맵 SDK 교체 포인트) */}
      {/*
        ========================================================================
        🗺️ KAKAO MAP / GOOGLE MAPS 연동 가이드:
        나중에 실제 카카오맵이나 구글맵을 연동할 때는 아래의 
        '가상 인터랙티브 GIS 캔버스' 대신 다음과 같이 교체하시면 됩니다:
        
        <div id="kakao-map" className="w-full h-full" ref={mapContainerRef}>
          {/* Kakao Maps SDK 초기화 코드 실행 및 Marker 렌더링 *\/}
        </div>
        ========================================================================
      */}
      <div className="relative flex-1 w-full h-full overflow-hidden flex items-center justify-center">
        {/* 그리드 배경 & 레이더 스윕 */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle, rgba(16, 185, 129, 0.2) 1px, transparent 1px), linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px)`,
            backgroundSize: "40px 40px, 80px 80px, 80px 80px",
          }}
        />

        {/* 남동 해역 이상 고온 수증기 히트맵 효과 (가상 비주얼) */}
        {activeLayer === "satellite" && (
          <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full bg-rose-500/20 blur-3xl pointer-events-none animate-pulse" />
        )}
        {activeLayer === "radar" && (
          <div className="absolute bottom-20 left-1/3 w-80 h-80 rounded-full bg-cyan-500/15 blur-3xl pointer-events-none" />
        )}

        {/* 제주도 가상 지형 그래픽 (SVG 기반 타겟 비주얼) */}
        <div
          className="relative transition-transform duration-300 ease-out"
          style={{
            transform: `scale(${zoomLevel / 100})`,
            width: "820px",
            height: "540px",
          }}
        >
          {/* 제주도 외곽 섬 지형 실루엣 */}
          <svg
            viewBox="0 0 800 500"
            className="w-full h-full drop-shadow-[0_10px_35px_rgba(16,185,129,0.15)] select-none"
          >
            <defs>
              <linearGradient id="islandGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#131e34" />
                <stop offset="50%" stopColor="#1a2942" />
                <stop offset="100%" stopColor="#0f192b" />
              </linearGradient>
              <linearGradient id="radarSweepGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(16, 185, 129, 0.2)" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>

            {/* 제주 본도 곡선 외곽선 */}
            <path
              d="M 140 280 C 120 250, 160 180, 260 140 C 370 100, 520 110, 640 170 C 720 210, 750 270, 710 320 C 650 390, 480 430, 320 420 C 210 410, 150 350, 140 280 Z"
              fill="url(#islandGrad)"
              stroke="rgba(52, 211, 153, 0.4)"
              strokeWidth="2"
              className="transition-all duration-500"
            />

            {/* 한라산 등고선 중심부 */}
            <ellipse
              cx="430"
              cy="270"
              rx="110"
              ry="75"
              fill="#1e3250"
              stroke="rgba(52, 211, 153, 0.25)"
              strokeWidth="1.5"
              strokeDasharray="4 3"
            />
            <ellipse
              cx="430"
              cy="270"
              rx="40"
              ry="25"
              fill="#243d60"
              stroke="rgba(52, 211, 153, 0.5)"
              strokeWidth="1.5"
            />
            <text
              x="430"
              y="273"
              textAnchor="middle"
              className="fill-emerald-400 text-[11px] font-mono font-bold"
            >
              한라산 (1,947m)
            </text>
          </svg>

          {/* 지점별 핀포인트 인터랙션 마커 */}
          {mapData.map((pt) => {
            const isSelected = selectedPoint?.id === pt.id;
            const pos = getRelativePosition(pt.lat, pt.lon);

            return (
              <div
                key={pt.id}
                style={{ top: pos.top, left: pos.left }}
                onClick={() => onSelectPoint(isSelected ? null : pt)}
                className="absolute -translate-x-1/2 -translate-y-1/2 z-10 cursor-pointer group"
              >
                {/* 펄스 링 (심각/경고 지점) */}
                {pt.risk_score >= 80 && (
                  <div
                    className={`absolute -inset-2 rounded-full animate-ping opacity-60 ${
                      pt.risk_score >= 90 ? "bg-rose-500" : "bg-amber-500"
                    }`}
                  />
                )}

                {/* 마커 본체 */}
                <div
                  className={`relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-full border shadow-xl transition-all duration-300 ${
                    isSelected
                      ? "bg-slate-900 border-emerald-400 scale-110 ring-2 ring-emerald-400/50"
                      : "bg-slate-950/90 border-slate-700 hover:border-slate-500 hover:scale-105"
                  }`}
                >
                  <MapPin className={`w-4 h-4 ${getPinColor(pt.risk_score)}`} />
                  <div className="flex flex-col text-left">
                    <span className="text-[11px] font-bold text-slate-100 whitespace-nowrap leading-tight">
                      {pt.region}
                    </span>
                    <span className="text-[9px] text-slate-400 whitespace-nowrap leading-tight">
                      {pt.crop}
                    </span>
                  </div>

                  {/* 점수 뱃지 */}
                  <span
                    className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-md ${
                      pt.risk_score >= 90
                        ? "bg-rose-500 text-white"
                        : pt.risk_score >= 75
                        ? "bg-amber-500 text-slate-950"
                        : "bg-cyan-500/20 text-cyan-300"
                    }`}
                  >
                    {pt.risk_score}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* 3. 선택된 지점 상세 HUD 팝업 카드 */}
        {selectedPoint && (
          <div className="absolute bottom-6 left-6 max-w-sm w-full p-4 rounded-xl bg-slate-900/95 border border-emerald-500/40 backdrop-blur-xl shadow-2xl z-30 animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div className="flex items-start justify-between border-b border-slate-800 pb-2 mb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-sm text-slate-100">
                    {selectedPoint.region}
                  </h4>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-md font-bold border ${getRiskBadgeColor(
                      selectedPoint.risk_level
                    )}`}
                  >
                    {selectedPoint.risk_level} ({selectedPoint.risk_score}점)
                  </span>
                </div>
                <p className="text-xs text-emerald-400 font-medium mt-0.5">
                  주요 재배 작물: {selectedPoint.crop}
                </p>
              </div>
              <button
                onClick={() => onSelectPoint(null)}
                className="text-slate-400 hover:text-white text-xs p-1 rounded-md hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div>
                <span className="text-slate-400 block mb-0.5 font-medium">현장 상황 감지:</span>
                <p className="text-slate-200 bg-slate-950/70 p-2 rounded-lg border border-slate-800/80">
                  {selectedPoint.status}
                </p>
              </div>

              <div>
                <span className="text-emerald-400 block mb-0.5 font-medium">긴급 조치 사항:</span>
                <p className="text-emerald-200 bg-emerald-950/30 p-2 rounded-lg border border-emerald-900/40">
                  {selectedPoint.action_needed}
                </p>
              </div>

              <div className="pt-1 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>위도: {selectedPoint.lat.toFixed(4)}°</span>
                <span>경도: {selectedPoint.lon.toFixed(4)}°</span>
              </div>
            </div>
          </div>
        )}

        {/* 4. 범례 (Legend) */}
        <div className="absolute bottom-6 right-6 p-3 rounded-xl bg-slate-950/90 border border-slate-800/90 backdrop-blur-md text-xs text-slate-300 shadow-xl z-20 pointer-events-auto">
          <div className="font-bold text-[11px] text-slate-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-emerald-400" />
            재해 위험 등급 지표
          </div>
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500" />
              <span className="font-semibold text-rose-300">심각 (90점 이상)</span>
              <span className="text-slate-500">과원 침수·무름병 경보</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shadow-sm shadow-amber-500" />
              <span className="font-semibold text-amber-300">경고 (70~89점)</span>
              <span className="text-slate-500">사전 예방 약제 살포</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400" />
              <span className="font-semibold text-cyan-300">주의 (50~69점)</span>
              <span className="text-slate-500">기류 모니터링</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
