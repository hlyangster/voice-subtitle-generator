# modules/__init__.py
# 空文件，使modules成為一個包
# modules/__init__.py

"""
語音生成與字幕系統模組包
包含文本預處理、多音字替換、TTS生成等功能模組
"""

# API 相關配置
HAILUO_GROUP_ID = "1886392350196895842"

# TTS 相關配置
TTS_VOICES = {
    "訓練長": "moss_audio_068dd108-edd2-11ef-b15b-7285e0393d3d",
    "游博士": "moss_audio_e5cf2e83-eaa3-11ef-a9a5-6aa74a18d091",
    "FIFI": "moss_audio_78886d55-17a5-11f0-8444-ae62a3be7263"

}

TTS_EMOTIONS = ["happy", "sad", "angry", "fearful", "disgusted", "surprised", "neutral"]

DEFAULT_PRONUNCIATION_DICT = {
    "tone": ["曝/(pu4)","ReAct/react","調整/(tiao2)(zheng3)","行為/(xing2)(wei2)","SHAP/shape","LIME/lime","COVID-19/covid nineteen","垃圾/(le4)(se4)","癌/(ai2)"]
}

# 音訊格式設定
AUDIO_SETTINGS = {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3",
    "channel": 2
}