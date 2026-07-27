"use client";

import { useState, useEffect } from "react";
import { listDiaries, writeDiary, readDiary, deleteDiary, DiaryEntry } from "@/services/api";

export default function DiaryPage() {
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [content, setContent] = useState("");
  const [viewing, setViewing] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const userId = "default";

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    try {
      const data = await listDiaries(userId);
      setEntries(data.entries || []);
    } catch (e) {
      console.error("加载日记失败:", e);
    }
  };

  const handleWrite = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const data = await writeDiary({ user_id: userId, content });
      setMessage(data.success ? "日记已保存 ✅" : "保存失败");
      setContent("");
      loadEntries();
    } catch (e) {
      setMessage("网络错误");
    }
    setLoading(false);
  };

  const handleRead = async (date: string) => {
    try {
      const data = await readDiary(userId, date);
      setViewing(data.success ? data.data : { content: data.message });
    } catch (e) {
      setViewing({ content: "读取失败" });
    }
  };

  const handleDelete = async (date: string) => {
    try {
      await deleteDiary(userId, date);
      setMessage("已删除");
      loadEntries();
    } catch (e) {
      setMessage("删除失败");
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui" }}>
      {/* 标题 */}
      <h1 style={{ fontSize: 32, fontWeight: "bold", marginBottom: 8 }}>📔 我的日记</h1>
      <p style={{ color: "#666", fontSize: 18, marginBottom: 24 }}>
        用说话或打字记录每一天，小银帮您保管
      </p>

      {/* 写日记 */}
      <div style={{ marginBottom: 32 }}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="今天想写点什么呢？"
          style={{
            width: "100%",
            minHeight: 160,
            padding: 16,
            fontSize: 20,
            borderRadius: 12,
            border: "2px solid #e0e0e0",
            resize: "vertical",
            fontFamily: "inherit",
          }}
        />
        <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={handleWrite}
            disabled={loading || !content.trim()}
            style={{
              fontSize: 20,
              padding: "10px 28px",
              borderRadius: 10,
              background: loading ? "#ccc" : "#4f46e5",
              color: "white",
              border: "none",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "保存中..." : "保存日记 ✍️"}
          </button>
          {message && <span style={{ fontSize: 18, color: "#4f46e5" }}>{message}</span>}
        </div>
      </div>

      {/* 日记列表 */}
      <h2 style={{ fontSize: 24, fontWeight: "bold", marginBottom: 16 }}>📋 最近日记</h2>
      {entries.length === 0 ? (
        <p style={{ fontSize: 18, color: "#999" }}>还没有写过日记呢，写一篇吧～</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {entries.map((entry) => (
            <div
              key={entry.date}
              onClick={() => handleRead(entry.date)}
              style={{
                padding: "14px 18px",
                borderRadius: 10,
                border: "1px solid #e5e7eb",
                cursor: "pointer",
                background: viewing?.date === entry.date ? "#f0f0ff" : "white",
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f9fafb")}
              onMouseLeave={(e) => (e.currentTarget.style.background = viewing?.date === entry.date ? "#f0f0ff" : "white")}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <span style={{ fontSize: 20, fontWeight: 600 }}>{entry.date}</span>
                  {entry.mood && (
                    <span style={{ marginLeft: 10, fontSize: 18, color: "#6b7280" }}>
                      {entry.mood}
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(entry.date); }}
                  style={{
                    fontSize: 16,
                    padding: "4px 10px",
                    borderRadius: 6,
                    border: "1px solid #fca5a5",
                    background: "white",
                    color: "#ef4444",
                    cursor: "pointer",
                  }}
                >
                  删除
                </button>
              </div>
              <p style={{ fontSize: 18, color: "#6b7280", marginTop: 6, marginBottom: 0 }}>
                {entry.preview}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* 查看日记详情 */}
      {viewing && (
        <div style={{
          marginTop: 24,
          padding: 20,
          borderRadius: 12,
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ fontSize: 22, fontWeight: "bold", margin: 0 }}>
              {viewing.date} 的日记
            </h3>
            <button
              onClick={() => setViewing(null)}
              style={{ fontSize: 18, background: "none", border: "none", cursor: "pointer", color: "#666" }}
            >
              ✕
            </button>
          </div>
          <p style={{ fontSize: 20, lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
            {typeof viewing === "string" ? viewing : viewing.content || "(空日记)"}
          </p>
        </div>
      )}
    </div>
  );
}
