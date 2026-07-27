"use client";

import { useState } from "react";
import { searchKB, KBSearchResult } from "@/services/api";

export default function KBPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KBSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await searchKB(query, 10);
      setResults(data.results || []);
      setSearched(true);
    } catch (err) {
      setError("搜索失败，请检查后端服务是否启动");
      setResults([]);
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 32, fontWeight: "bold", marginBottom: 8 }}>📚 个人知识库</h1>
      <p style={{ color: "#666", fontSize: 18, marginBottom: 24 }}>
        搜索你的 Obsidian 笔记、日记和项目文档（BM25 语义检索）
      </p>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入关键词搜索你的笔记..."
          style={{
            flex: 1,
            padding: "14px 18px",
            fontSize: 20,
            borderRadius: 12,
            border: "2px solid #e0e0e0",
            fontFamily: "inherit",
          }}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          style={{
            fontSize: 20,
            padding: "14px 28px",
            borderRadius: 12,
            background: loading ? "#ccc" : "#4f46e5",
            color: "white",
            border: "none",
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: 600,
          }}
        >
          {loading ? "搜索中..." : "搜索 🔍"}
        </button>
      </form>

      {error && (
        <div style={{ padding: 14, borderRadius: 10, background: "#fef2f2", color: "#dc2626", fontSize: 18, marginBottom: 20 }}>
          ⚠️ {error}
        </div>
      )}

      {/* 搜索结果 */}
      {searched && !loading && (
        <>
          <p style={{ fontSize: 18, color: "#666", marginBottom: 16 }}>
            找到 <strong>{results.length}</strong> 条结果
          </p>
          {results.length === 0 ? (
            <div style={{
              padding: 40,
              textAlign: "center",
              borderRadius: 12,
              background: "#f9fafb",
              border: "1px solid #e5e7eb",
            }}>
              <p style={{ fontSize: 20, color: "#999" }}>没有找到相关内容</p>
              <p style={{ fontSize: 16, color: "#bbb", marginTop: 8 }}>
                试试换一个关键词？
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {results.map((r, i) => (
                <div
                  key={i}
                  style={{
                    padding: "16px 20px",
                    borderRadius: 12,
                    border: "1px solid #e5e7eb",
                    background: "white",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div>
                      <span style={{ fontSize: 18, fontWeight: 700 }}>{r.title}</span>
                      <span style={{
                        marginLeft: 10,
                        fontSize: 14,
                        padding: "2px 8px",
                        borderRadius: 6,
                        background: "#e0e7ff",
                        color: "#4f46e5",
                        fontWeight: 600,
                      }}>
                        {r.score.toFixed(2)}
                      </span>
                    </div>
                    <span style={{ fontSize: 14, color: "#9ca3af" }}>{r.file}</span>
                  </div>
                  <p style={{ fontSize: 17, color: "#374151", lineHeight: 1.6, margin: 0 }}>
                    {r.snippet}
                  </p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* 初始状态 */}
      {!searched && !loading && (
        <div style={{
          padding: 40,
          textAlign: "center",
          borderRadius: 12,
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📖</div>
          <p style={{ fontSize: 20, color: "#666" }}>输入关键词，搜索你的知识库</p>
          <p style={{ fontSize: 16, color: "#999", marginTop: 8 }}>
            知识库已索引 brain/ 下的所有 Markdown 笔记
          </p>
        </div>
      )}
    </div>
  );
}
