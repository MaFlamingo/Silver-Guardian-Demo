/**
 * 银发守护 — API 服务层
 * 统一管理后端 API 调用
 */

const API_BASE = "/api/v1";

// ============================================================
// 类型定义
// ============================================================
export interface ChatRequest {
  message: string;
  user_id?: string;
  user_name?: string;
  user_age?: number;
  image_url?: string;
}

export interface ChatResponse {
  reply: string;
  intent: string;
  action: string;
  tts_text?: string;
  need_confirm: boolean;
  medicine_info?: Record<string, unknown>;
  urgency?: string;
}

export interface ReminderResponse {
  success: boolean;
  reminder_id?: string;
  message: string;
}

export interface MedicineInfo {
  found: boolean;
  info?: Record<string, unknown>;
  message: string;
}

export interface HealthStatus {
  status: string;
  llm_provider: string;
  rag_ready: boolean;
}

// ============================================================
// API 函数
// ============================================================

/** 健康检查 */
export async function healthCheck(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

/** 发送对话消息 */
export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

/** 设置提醒 */
export async function setReminder(content: string, time: string, userId: string = "default"): Promise<ReminderResponse> {
  const res = await fetch(`${API_BASE}/reminder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, time, user_id: userId }),
  });
  if (!res.ok) throw new Error(`Reminder failed: ${res.status}`);
  return res.json();
}

/** 查询药品信息 */
export async function queryMedicine(name: string): Promise<MedicineInfo> {
  const res = await fetch(`${API_BASE}/medicine/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ medicine_name: name }),
  });
  if (!res.ok) throw new Error(`Medicine query failed: ${res.status}`);
  return res.json();
}

/** 获取提醒列表 */
export async function getReminders(userId: string = "default") {
  const res = await fetch(`${API_BASE}/reminder/${userId}`);
  if (!res.ok) throw new Error(`Get reminders failed: ${res.status}`);
  return res.json();
}

// ============================================================
// 日记 API
// ============================================================
export interface DiaryWriteRequest {
  user_id: string;
  content: string;
  mood?: string;
  dt?: string;
}

export interface DiaryEntry {
  date: string;
  mood?: string;
  preview: string;
  content?: string;
}

export async function writeDiary(req: DiaryWriteRequest) {
  const res = await fetch(`${API_BASE}/diary/write`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Write diary failed: ${res.status}`);
  return res.json();
}

export async function readDiary(userId: string, dt: string) {
  const res = await fetch(`${API_BASE}/diary/read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, dt }),
  });
  if (!res.ok) throw new Error(`Read diary failed: ${res.status}`);
  return res.json();
}

export async function listDiaries(userId: string = "default") {
  const res = await fetch(`${API_BASE}/diary/list/${userId}`);
  if (!res.ok) throw new Error(`List diaries failed: ${res.status}`);
  return res.json();
}

export async function deleteDiary(userId: string, dt: string) {
  const res = await fetch(`${API_BASE}/diary/${userId}?dt=${dt}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Delete diary failed: ${res.status}`);
  return res.json();
}

// ============================================================
// 心情 API
// ============================================================
export interface MoodRecord {
  timestamp: string;
  date: string;
  mood: string;
  note?: string;
  acoustic_mood?: string;
  acoustic_confidence?: number;
}

export interface MoodHistoryResponse {
  records: MoodRecord[];
  mood_distribution: Record<string, number>;
  trend: string;
  total: number;
}

export async function recordMood(userId: string, mood: string, note?: string) {
  const res = await fetch(`${API_BASE}/mood/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mood, note, user_id: userId }),
  });
  if (!res.ok) throw new Error(`Record mood failed: ${res.status}`);
  return res.json();
}

export async function getMoodHistory(userId: string, days: number = 7): Promise<MoodHistoryResponse> {
  const res = await fetch(`${API_BASE}/mood/history`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, days }),
  });
  if (!res.ok) throw new Error(`Get mood history failed: ${res.status}`);
  return res.json();
}

export async function analyzeTextMood(text: string) {
  const res = await fetch(`${API_BASE}/mood/analyze-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Analyze mood failed: ${res.status}`);
  return res.json();
}

// ============================================================
// 个人知识库 API
// ============================================================
export interface KBSearchResult {
  file: string;
  title: string;
  score: number;
  snippet: string;
  content: string;
}

export async function searchKB(query: string, topK: number = 5): Promise<{ query: string; results: KBSearchResult[]; count: number }> {
  const res = await fetch(`${API_BASE}/kb/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  if (!res.ok) throw new Error(`KB search failed: ${res.status}`);
  return res.json();
}

export async function getKBSummary() {
  const res = await fetch(`${API_BASE}/kb/summary`);
  if (!res.ok) throw new Error(`KB summary failed: ${res.status}`);
  return res.json();
}

// ============================================================
// WebSocket 连接
// ============================================================
export function createChatWebSocket(
  userId: string,
  onMessage: (data: ChatResponse) => void,
  onError?: (err: Event) => void,
  onClose?: () => void
): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/chat/${userId}`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log("[WS] 已连接:", userId);
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ChatResponse;
      onMessage(data);
    } catch (e) {
      console.error("[WS] 消息解析失败:", e);
    }
  };

  ws.onerror = (err) => {
    console.error("[WS] 连接错误:", err);
    onError?.(err);
  };

  ws.onclose = () => {
    console.log("[WS] 已断开");
    onClose?.();
  };

  return ws;
}
