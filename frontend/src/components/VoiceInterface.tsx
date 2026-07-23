"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { sendMessage, ChatResponse } from "@/services/api";

// ============================================================
// 语音交互组件
// ============================================================
export default function VoiceInterface() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const synthRef = useRef<SpeechSynthesisUtterance | null>(null);

  // 初始化语音识别
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("您的浏览器不支持语音识别，请使用 Chrome 浏览器");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "zh-CN";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const text = event.results[0][0].transcript;
      setTranscript(text);
      setIsListening(false);
      // 自动发送
      handleSend(text);
    };

    recognition.onerror = (event: any) => {
      console.error("[Voice] 识别错误:", event.error);
      setError(event.error === "no-speech" ? "没听到您说话，请再试一次" : "语音识别出了点问题");
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
  }, []);

  // 开始监听
  const startListening = useCallback(() => {
    setError("");
    setTranscript("");
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        console.error("[Voice] 启动失败:", e);
        setError("语音识别启动失败，请刷新页面");
      }
    }
  }, []);

  // 停止监听
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  // TTS 播报
  const speak = useCallback((text: string) => {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 0.8;  // 适老化：慢语速
    utterance.volume = 1.2; // 大音量
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, []);

  // 发送消息
  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    setLoading(true);
    setError("");

    try {
      const response: ChatResponse = await sendMessage({
        message: text,
        user_name: "张叔",
        user_age: 70,
      });

      setReply(response.reply);
      // 自动播报回复
      speak(response.tts_text || response.reply);
    } catch (e: any) {
      setError("网络出了问题，请再试一次");
      console.error("[Voice] 发送失败:", e);
    } finally {
      setLoading(false);
    }
  };

  // 手动输入
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const input = (e.target as HTMLFormElement).querySelector("input") as HTMLInputElement;
    if (input?.value) {
      setTranscript(input.value);
      handleSend(input.value);
      input.value = "";
    }
  };

  return (
    <div className="card-elder space-y-6">
      <h2 className="text-elder-lg font-bold text-center flex items-center justify-center gap-3">
        <span>🎤</span> 语音交流
      </h2>

      {/* 语音按钮 */}
      <div className="flex justify-center">
        <button
          onClick={isListening ? stopListening : startListening}
          disabled={loading}
          className={`
            w-32 h-32 rounded-full text-4xl font-bold
            transition-all duration-300
            flex items-center justify-center
            ${isListening
              ? "bg-elder-danger text-white emergency-pulse scale-110"
              : "bg-elder-primary text-white hover:bg-blue-700 shadow-xl hover:shadow-2xl"
            }
            ${loading ? "opacity-60 cursor-wait" : ""}
          `}
          aria-label={isListening ? "停止说话" : "开始说话"}
        >
          {loading ? (
            <div className="voice-wave">
              <span></span><span></span><span></span><span></span><span></span>
            </div>
          ) : isListening ? (
            "🔴"
          ) : (
            "🎙️"
          )}
        </button>
      </div>

      <p className="text-center text-elder-base text-elder-muted">
        {isListening
          ? "正在听您说话..."
          : loading
          ? "小银正在思考..."
          : isSpeaking
          ? "小银正在说话..."
          : "点击麦克风，开始说话"}
      </p>

      {/* 识别文本 */}
      {transcript && (
        <div className="bg-blue-50 rounded-2xl p-4">
          <p className="text-elder-sm text-elder-muted mb-1">您说的：</p>
          <p className="text-elder-base font-medium">{transcript}</p>
        </div>
      )}

      {/* AI 回复 */}
      {reply && (
        <div className="bg-green-50 rounded-2xl p-4">
          <p className="text-elder-sm text-elder-muted mb-1">小银回复：</p>
          <p className="text-elder-base">{reply}</p>
          <button
            onClick={() => speak(reply)}
            className="mt-3 text-elder-sm text-elder-primary underline"
          >
            🔊 再听一遍
          </button>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 text-elder-danger rounded-2xl p-4 text-elder-sm">
          ⚠️ {error}
        </div>
      )}

      {/* 手动输入区 */}
      <form onSubmit={handleTextSubmit} className="flex gap-3">
        <input
          type="text"
          placeholder="或者在这里打字..."
          className="flex-1 px-6 py-4 text-elder-base rounded-2xl border-4 border-gray-200 
                     focus:border-elder-primary focus:outline-none"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="btn-elder-primary px-8"
        >
          发送
        </button>
      </form>
    </div>
  );
}
