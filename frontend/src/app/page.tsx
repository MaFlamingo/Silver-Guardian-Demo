"use client";

import React, { useState, useEffect } from "react";
import VoiceInterface from "@/components/VoiceInterface";
import ImageRecognition from "@/components/ImageRecognition";
import { healthCheck, HealthStatus } from "@/services/api";

type Tab = "voice" | "photo";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("voice");
  const [status, setStatus] = useState<HealthStatus | null>(null);

  // 检查后端健康状态
  useEffect(() => {
    healthCheck()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  return (
    <div className="space-y-6">
      {/* 欢迎卡片 */}
      <div className="card-elder text-center space-y-3">
        <div className="text-5xl">🛡️</div>
        <h2 className="text-elder-xl font-bold">
          您好，我是小银
        </h2>
        <p className="text-elder-base text-elder-muted">
          您的智能生活助手。说话或拍照，我来帮您
        </p>
        {status && (
          <p className="text-elder-sm text-green-600">
            ✅ 服务已就绪（{status.llm_provider}）
          </p>
        )}
        {!status && (
          <p className="text-elder-sm text-elder-warning">
            ⚠️ 正在连接服务...
          </p>
        )}
      </div>

      {/* Tab 切换 */}
      <div className="flex gap-3 justify-center">
        <button
          onClick={() => setActiveTab("voice")}
          className={`
            px-8 py-4 text-elder-base font-bold rounded-2xl transition-all
            ${activeTab === "voice"
              ? "bg-elder-primary text-white shadow-lg"
              : "bg-white text-elder-muted border-4 border-gray-200 hover:border-elder-primary"
            }
          `}
        >
          🎤 语音交流
        </button>
        <button
          onClick={() => setActiveTab("photo")}
          className={`
            px-8 py-4 text-elder-base font-bold rounded-2xl transition-all
            ${activeTab === "photo"
              ? "bg-elder-primary text-white shadow-lg"
              : "bg-white text-elder-muted border-4 border-gray-200 hover:border-elder-primary"
            }
          `}
        >
          📷 拍照识别
        </button>
      </div>

      {/* 功能区域 */}
      {activeTab === "voice" ? <VoiceInterface /> : <ImageRecognition />}

      {/* 紧急求助按钮 */}
      <div className="text-center pt-2 pb-6">
        <button
          className="btn-elder-danger text-elder-lg px-12 py-5 rounded-full emergency-pulse"
          onClick={() => {
            // 模拟紧急求助
            alert("紧急求助已触发！\n\n系统将立即通知您的紧急联系人。\n\n如果情况紧急，请同时拨打 120。");
          }}
        >
          🆘 紧急求助
        </button>
        <p className="text-elder-sm text-elder-muted mt-2">
          身体不适时，点击此按钮立即通知家人
        </p>
      </div>
    </div>
  );
}
