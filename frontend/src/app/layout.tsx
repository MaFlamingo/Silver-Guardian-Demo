import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "银发守护 — 适老化智能助手",
  description: "基于 AI Agent 的适老化智能生活助手，用说话和拍照就能完成数字生活中的所有事",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-elder-bg">
        <header className="bg-elder-primary text-white py-5 px-6 shadow-lg">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <h1 className="text-elder-lg font-bold flex items-center gap-3">
              <span className="text-4xl">🛡️</span>
              银发守护
            </h1>
            <span className="text-elder-sm opacity-80">AI 智能助手</span>
          </div>
        </header>

        {/* 导航栏 */}
        <NavBar />

        <main className="max-w-4xl mx-auto p-4 md:p-6">
          {children}
        </main>
        <footer className="text-center py-6 text-elder-muted text-elder-sm">
          <p>🛡️ 银发守护 · 让科技更有温度</p>
        </footer>
      </body>
    </html>
  );
}
