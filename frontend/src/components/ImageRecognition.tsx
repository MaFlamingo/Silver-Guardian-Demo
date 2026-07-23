"use client";

import React, { useState, useRef } from "react";
import { sendMessage, ChatResponse } from "@/services/api";

// ============================================================
// 拍照识别组件
// ============================================================
export default function ImageRecognition() {
  const [image, setImage] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraOn, setCameraOn] = useState(false);

  // 从文件选择图片
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // 限制文件大小 10MB
    if (file.size > 10 * 1024 * 1024) {
      setError("图片太大了，请选择 10MB 以内的图片");
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      setImage(ev.target?.result as string);
      setResult(null);
      setError("");
    };
    reader.onerror = () => setError("图片读取失败");
    reader.readAsDataURL(file);
  };

  // 打开摄像头
  const startCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" }, // 后置摄像头
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setCameraOn(true);
      }
    } catch (e) {
      setError("无法打开摄像头，请检查权限设置");
    }
  };

  // 拍照
  const takePhoto = () => {
    if (!videoRef.current) return;

    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx?.drawImage(videoRef.current, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
    setImage(dataUrl);
    setResult(null);

    // 关闭摄像头
    const stream = videoRef.current.srcObject as MediaStream;
    stream?.getTracks().forEach((t) => t.stop());
    setCameraOn(false);
  };

  // 停止摄像头
  const stopCamera = () => {
    const stream = videoRef.current?.srcObject as MediaStream;
    stream?.getTracks().forEach((t) => t.stop());
    setCameraOn(false);
  };

  // 识别图片
  const handleRecognize = async () => {
    if (!image) return;

    setLoading(true);
    setError("");

    try {
      const response = await sendMessage({
        message: "请帮我看看这是什么",
        image_url: image,
        user_name: "张叔",
        user_age: 70,
      });
      setResult(response);
    } catch (e: any) {
      setError("识别失败，请再试一次");
    } finally {
      setLoading(false);
    }
  };

  // 重置
  const handleReset = () => {
    setImage(null);
    setResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="card-elder space-y-6">
      <h2 className="text-elder-lg font-bold text-center flex items-center justify-center gap-3">
        <span>📷</span> 拍照识别
      </h2>

      <p className="text-elder-base text-center text-elder-muted">
        拍一拍药盒、说明书或任何文字，小银帮您看懂
      </p>

      {/* 未拍照时：选择入口 */}
      {!image && !cameraOn && (
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="btn-elder-outline flex-1"
          >
            📁 从相册选择
          </button>
          <button onClick={startCamera} className="btn-elder-primary flex-1">
            📸 打开相机
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>
      )}

      {/* 摄像头预览 */}
      {cameraOn && (
        <div className="space-y-4">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full rounded-2xl border-4 border-elder-primary"
          />
          <div className="flex gap-4 justify-center">
            <button onClick={takePhoto} className="btn-elder-primary">
              📸 拍照
            </button>
            <button onClick={stopCamera} className="btn-elder-outline">
              取消
            </button>
          </div>
        </div>
      )}

      {/* 图片预览 */}
      {image && (
        <div className="space-y-4">
          <div className="relative">
            <img
              src={image}
              alt="待识别图片"
              className="w-full max-h-80 object-contain rounded-2xl border-4 border-gray-200"
            />
            <button
              onClick={handleReset}
              className="absolute top-2 right-2 bg-white rounded-full w-10 h-10 
                         flex items-center justify-center shadow-md text-elder-base"
            >
              ✕
            </button>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={handleRecognize}
              disabled={loading}
              className={`btn-elder-primary flex-1 ${loading ? "opacity-60" : ""}`}
            >
              {loading ? "识别中..." : "🔍 帮我看看"}
            </button>
          </div>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-4">
          <div className="voice-wave inline-flex">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
          <p className="text-elder-base text-elder-muted mt-2">小银正在仔细看...</p>
        </div>
      )}

      {/* 识别结果 */}
      {result && (
        <div className="bg-green-50 rounded-2xl p-5 space-y-3">
          <p className="text-elder-sm text-elder-muted">小银看出来了：</p>
          <p className="text-elder-base whitespace-pre-wrap">{result.reply}</p>

          {result.medicine_info && (
            <details className="mt-3">
              <summary className="text-elder-sm text-elder-primary cursor-pointer">
                查看详细信息
              </summary>
              <pre className="mt-2 text-base bg-white rounded-xl p-3 overflow-x-auto">
                {JSON.stringify(result.medicine_info, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      {/* 错误 */}
      {error && (
        <div className="bg-red-50 text-elder-danger rounded-2xl p-4 text-elder-sm">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}
