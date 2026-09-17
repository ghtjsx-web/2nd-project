"use client";

import React, { useState, useEffect } from "react";
import { Satellite, ShieldCheck, Activity, Bell, Sparkles } from "lucide-react";

export default function Navbar() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(
        now.toLocaleDateString("ko-KR", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          weekday: "short",
        }) + " " + now.toLocaleTimeString("ko-KR", { hour12: false })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 flex items-center justify-between z-30 sticky top-0">
      {/* Brand & Platform Identity */}
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-500/20 ring-1 ring-emerald-400/30">
          <Satellite className="w-5 h-5 text-white animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-black tracking-wider text-base bg-gradient-to-r from-emerald-300 via-teal-200 to-white bg-clip-text text-transparent">
              TERRA-AGRI INTEL
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              COMMERCIAL v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400">
            기후-농업 비즈니스 인텔리전스 | 제주 권역 실증 센터
          </p>
        </div>
      </div>

      {/* Real-time Status Badges */}
      <div className="hidden md:flex items-center gap-6 text-xs">
        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-slate-300 font-medium">천리안-2A / 위성 SST 피드 정상</span>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">FastAPI 백엔드:</span>
          <span className="text-emerald-400 font-mono font-semibold">ONLINE</span>
        </div>

        <div className="text-slate-400 font-mono bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800/60">
          {time || "2026-09-17 10:48:00"}
        </div>
      </div>

      {/* Quick Action / User Profile */}
      <div className="flex items-center gap-3">
        <button
          title="재해 알림 센터"
          className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500"></span>
        </button>

        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-emerald-400">
            AG
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-semibold text-slate-200 leading-tight">지능화 농업 본부</p>
            <p className="text-[10px] text-slate-400 leading-tight">Chief Analyst</p>
          </div>
        </div>
      </div>
    </header>
  );
}
