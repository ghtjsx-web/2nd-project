import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TERRA-AGRI INTEL | 기후-농업 비즈니스 인텔리전스 대시보드",
  description: "위성 영상 기후 예측과 GIS 공간 위험도 분석 기반 농업 비즈니스 인텔리전스 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark">
      <body className="min-h-screen bg-[#090d16] text-slate-100 antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        {children}
      </body>
    </html>
  );
}
