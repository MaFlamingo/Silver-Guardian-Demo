"""
银发守护 v2 — 语音心情分析模块
=================================
来自 my-wiki 的 voice_mood.py，适配 FastAPI 后端。

分析录音的声学特征辅助判断情绪：
  - energy_rms: 能量（RMS），反映音量/力度
  - energy_std: 能量波动，反映情绪稳定性
  - pitch_zcr:  过零率，近似音高
  - pitch_std:  过零率波动，反映语调变化
  - speech_rate: 有效语音段密度，近似语速
"""
import math
import array
import wave
from typing import Optional


def analyze_voice_acoustics(wav_path: str) -> Optional[dict]:
    """分析录音的声学特征，辅助判断情绪"""
    try:
        with wave.open(wav_path, "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw = wf.readframes(n_frames)

        if not raw or n_frames == 0:
            return None
        if sample_width != 2:
            return None

        samples = array.array("h")
        samples.frombytes(raw)
        if n_channels > 1:
            samples = array.array("h", samples[::n_channels])

        n = len(samples)
        if n == 0:
            return None

        duration = n / float(framerate)

        # 按帧分析（30ms 帧，20ms 步长）
        frame_size = int(0.030 * framerate)
        hop_size = int(0.020 * framerate)
        frame_size = max(frame_size, 2)
        hop_size = max(hop_size, 1)

        frame_energies = []
        frame_zcrs = []
        voiced_frames = 0

        for i in range(0, n - frame_size, hop_size):
            frame = samples[i:i + frame_size]
            sum_sq = sum(s * s for s in frame)
            rms = math.sqrt(sum_sq / len(frame))
            frame_energies.append(rms)
            zc = sum(1 for j in range(1, len(frame)) if (frame[j - 1] >= 0) != (frame[j] >= 0))
            frame_zcrs.append(zc / len(frame))
            if rms > 300:
                voiced_frames += 1

        if not frame_energies:
            return None

        energy_rms = sum(frame_energies) / len(frame_energies)
        energy_std = (
            math.sqrt(sum((e - energy_rms) ** 2 for e in frame_energies) / len(frame_energies))
            if len(frame_energies) > 1 else 0
        )
        pitch_zcr = sum(frame_zcrs) / len(frame_zcrs)
        pitch_std = (
            math.sqrt(sum((z - pitch_zcr) ** 2 for z in frame_zcrs) / len(frame_zcrs))
            if len(frame_zcrs) > 1 else 0
        )
        speech_rate = voiced_frames / duration if duration > 0 else 0

        return {
            "energy_rms": round(energy_rms, 1),
            "energy_std": round(energy_std, 1),
            "pitch_zcr": round(pitch_zcr, 4),
            "pitch_std": round(pitch_std, 4),
            "speech_rate": round(speech_rate, 2),
            "duration": round(duration, 1),
            "voiced_frames": voiced_frames,
            "total_frames": len(frame_energies),
        }
    except Exception:
        return None


def acoustics_to_mood(features: Optional[dict]) -> tuple:
    """将声学特征映射为情绪倾向"""
    if not features:
        return None, 0, "无有效的声学数据"

    e = features["energy_rms"]
    e_std = features["energy_std"]
    zcr = features["pitch_zcr"]
    zcr_std = features["pitch_std"]
    rate = features["speech_rate"]
    voiced = features["voiced_frames"]

    if voiced < 3:
        return "平静", 0.1, "声音太短，无法分析声学特征"

    scores = {"开心": 0, "平静": 0, "低落": 0, "兴奋": 0, "焦虑": 0}
    details = []

    # 能量分析
    if e > 5000:
        scores["兴奋"] += 2; scores["开心"] += 1; details.append("音量较高")
    elif e > 2000:
        scores["开心"] += 1; scores["焦虑"] += 1; details.append("音量适中")
    elif e > 500:
        scores["平静"] += 1; details.append("音量较低")
    else:
        scores["低落"] += 2; details.append("声音很轻")

    # 能量波动
    if e_std > 3000:
        scores["兴奋"] += 1; scores["焦虑"] += 1; details.append("音量波动大")
    elif e_std < 500:
        scores["平静"] += 1; scores["低落"] += 1; details.append("音量稳定")

    # 过零率（音高）
    if zcr > 0.15:
        scores["兴奋"] += 1; scores["焦虑"] += 1; details.append("音调偏高")
    elif zcr < 0.06:
        scores["低落"] += 1; scores["平静"] += 1; details.append("音调偏低")
    else:
        scores["开心"] += 1; details.append("音调适中")

    # 过零率波动（语调）
    if zcr_std > 0.05:
        scores["兴奋"] += 1; scores["开心"] += 1; details.append("语调起伏丰富")
    elif zcr_std < 0.01:
        scores["平静"] += 1; scores["低落"] += 1; details.append("语调平缓")

    # 语速
    if rate > 8:
        scores["焦虑"] += 1; scores["兴奋"] += 1; details.append("语速较快")
    elif rate < 2:
        scores["低落"] += 1; scores["平静"] += 1; details.append("语速较慢")

    best = max(scores.items(), key=lambda x: x[1])
    if best[1] == 0:
        return "平静", 0.1, "声学特征不明显"

    conf = min(best[1] / 6.0, 0.5)
    return best[0], round(conf, 2), "、".join(details)


# --- 情绪算法（基于文本 + 声学融合）---
MOOD_KEYWORDS = {
    "开心": ["哈哈", "开心", "高兴", "快乐", "好开心", "太好了", "真高兴", "😊", "😄", "棒", "赞"],
    "低落": ["不开心", "难过", "伤心", "难过", "郁闷", "烦躁", "无聊", "累", "好累", "😢", "😞"],
    "焦虑": ["紧张", "担心", "害怕", "怕", "焦虑", "不安", "怎么办", "万一", "😰", "😨"],
    "平静": ["还好", "一般", "还行", "平淡", "安静", "放空", "发呆"],
    "兴奋": ["激动", "太棒了", "哇", "天哪", "必须", "一定要", "!!", "🔥", "🎉"],
    "感激": ["谢谢", "感恩", "真好", "感动", "感谢", "太感谢"],
}


def analyze_text_mood(text: str) -> dict:
    """基于关键词 + 简单规则分析文本情绪"""
    text_lower = text.lower()
    scores = {mood: 0 for mood in MOOD_KEYWORDS}
    matches = []

    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[mood] += 1
                matches.append(kw)

    best = max(scores.items(), key=lambda x: x[1])
    if best[1] == 0:
        return {"mood": "平静", "confidence": 0.2, "detail": "情绪不明显", "matched_keywords": []}

    conf = min(best[1] / len(matches) if matches else 0.3, 0.8)
    return {
        "mood": best[0],
        "confidence": round(conf, 2),
        "detail": f"匹配到关键词: {', '.join(matches[:5])}",
        "matched_keywords": matches,
    }


def fuse_mood(text_mood: dict, acoustic_features: dict) -> dict:
    """融合文本情绪 + 声学特征，给出综合心情判定"""
    if acoustic_features:
        acoustic_mood, acoustic_conf, acoustic_detail = acoustics_to_mood(acoustic_features)
    else:
        acoustic_mood, acoustic_conf, acoustic_detail = None, 0, ""

    result = {
        "text_mood": text_mood["mood"],
        "text_confidence": text_mood["confidence"],
    }

    if acoustic_mood:
        # 简单加权融合
        if text_mood["mood"] == acoustic_mood:
            result["fused_mood"] = text_mood["mood"]
            result["fused_confidence"] = round(min(text_mood["confidence"] + acoustic_conf, 0.95), 2)
        else:
            result["fused_mood"] = text_mood["mood"]
            result["fused_confidence"] = text_mood["confidence"]
        result["acoustic_mood"] = acoustic_mood
        result["acoustic_confidence"] = acoustic_conf
        result["acoustic_detail"] = acoustic_detail
    else:
        result["fused_mood"] = text_mood["mood"]
        result["fused_confidence"] = text_mood["confidence"]

    return result
