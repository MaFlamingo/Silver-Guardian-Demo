"use client";

import { useState, useEffect } from "react";
import { getMoodHistory, recordMood, MoodRecord } from "@/services/api";

export default function MoodPage() {
  const [records, setRecords] = useState<MoodRecord[]>([]);
  const [distribution, setDistribution] = useState<Record<string, number>>({});
  const [trend, setTrend] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [activeTab, setActiveTab] = useState<"history" | "record">("history");

  const userId = "default";

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getMoodHistory(userId, 7);
      setRecords(data.records || []);
      setDistribution(data.mood_distribution || {});
      setTrend(data.trend || "");
    } catch (e) {
      console.error("加载心情失败:", e);
    }
  };

  const handleRecord = async (mood: string) => {
    setLoading(true);
    try {
      await recordMood(userId, mood, note);
      setMessage(`心情「${mood}」已记录 ✅`);
      setNote("");
      loadHistory();
    } catch (e) {
      setMessage("记录失败");
    }
    setLoading(false);
  };

  const moods = ["开心", "平静", "低落", "兴奋", "焦虑", "感激"];

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui" }}>
      {/* 标题 */}
      <h1 style={{ fontSize: 32, fontWeight: "bold", marginBottom: 8 }}>💝 心情记录</h1>
      <p style={{ color: "#666", fontSize: 18, marginBottom: 24 }}>
        记录每天的心情，小银帮您关注情绪变化
      </p>

      {/* 选项卡 */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {(["history", "record"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              fontSize: 20,
              padding: "8px 20px",
              borderRadius: 8,
              border: activeTab === tab ? "2px solid #4f46e5" : "1px solid #e5e7eb",
              background: activeTab === tab ? "#4f46e5" : "white",
              color: activeTab === tab ? "white" : "#333",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {tab === "history" ? "📊 心情趋势" : "✍️ 记录心情"}
          </button>
        ))}
      </div>

      {/* 记录心情 */}
      {activeTab === "record" && (
        <>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 20 }}>
            {moods.map((mood) => (
              <button
                key={mood}
                onClick={() => handleRecord(mood)}
                disabled={loading}
                style={{
                  fontSize: 22,
                  padding: "12px 24px",
                  borderRadius: 12,
                  border: "2px solid #e5e7eb",
                  background: "white",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: 600,
                  transition: "all 0.2s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#4f46e5")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#e5e7eb")}
              >
                {mood}
              </button>
            ))}
          </div>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="想多说说此刻的感受吗？（可选）"
            style={{
              width: "100%",
              minHeight: 80,
              padding: 14,
              fontSize: 18,
              borderRadius: 10,
              border: "2px solid #e0e0e0",
              resize: "vertical",
              fontFamily: "inherit",
            }}
          />
          {message && (
            <p style={{ fontSize: 18, color: "#4f46e5", marginTop: 12 }}>{message}</p>
          )}
        </>
      )}

      {/* 心情趋势 */}
      {activeTab === "history" && (
        <>
          {/* 趋势概览 */}
          <div style={{
            padding: 20,
            borderRadius: 12,
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            marginBottom: 24,
          }}>
            <h3 style={{ fontSize: 22, fontWeight: "bold", marginBottom: 12 }}>📊 7 天心情趋势</h3>
            <p style={{ fontSize: 20, color: "#4f46e5", fontWeight: 600 }}>{trend}</p>

            {/* 分布条 */}
            {Object.keys(distribution).length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
                {Object.entries(distribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([mood, count]) => {
                    const maxCount = Math.max(...Object.values(distribution));
                    const pct = Math.round((count / maxCount) * 100);
                    return (
                      <div key={mood} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 18, fontWeight: 600, minWidth: 60 }}>{mood}</span>
                        <div style={{
                          flex: 1,
                          height: 24,
                          borderRadius: 12,
                          background: "#e0e7ff",
                          overflow: "hidden",
                        }}>
                          <div style={{
                            height: "100%",
                            width: `${pct}%`,
                            borderRadius: 12,
                            background: "linear-gradient(90deg, #6366f1, #8b5cf6)",
                            transition: "width 0.5s",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "flex-end",
                            paddingRight: 10,
                          }}>
                            <span style={{ fontSize: 14, color: "white", fontWeight: 600 }}>
                              {count}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>

          {/* 历史记录 */}
          <h3 style={{ fontSize: 22, fontWeight: "bold", marginBottom: 12 }}>📝 历史记录</h3>
          {records.length === 0 ? (
            <p style={{ fontSize: 18, color: "#999" }}>还没有心情记录，点「记录心情」开始吧～</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {records.map((r, i) => (
                <div
                  key={i}
                  style={{
                    padding: "12px 16px",
                    borderRadius: 10,
                    border: "1px solid #e5e7eb",
                    background: "white",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <span style={{ fontSize: 20, fontWeight: 600 }}>{r.mood}</span>
                    {r.note && (
                      <span style={{ fontSize: 16, color: "#6b7280", marginLeft: 10 }}>
                        — {r.note.slice(0, 40)}{r.note.length > 40 ? "..." : ""}
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: 14, color: "#9ca3af" }}>
                    {r.date} {r.timestamp?.slice(11, 16)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
