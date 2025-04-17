# tests/test_hailuo_api.py
"""
這是一個簡單的測試腳本，用於測試 Hailuo API 的調用。
"""

import os
import sys
import requests
import json
from pathlib import Path

# 確保可以導入專案模組
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))

# 嘗試導入 HAILUO_GROUP_ID，如果失敗則使用默認值
try:
    from modules import HAILUO_GROUP_ID
except ImportError:
    HAILUO_GROUP_ID = "1886392350196895842"

def test_hailuo_api():
    """測試 Hailuo API 調用"""
    # 直接設置 API 密鑰
    api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJIb3dsaW4gWWFuZyIsIlVzZXJOYW1lIjoiSG93bGluIFlhbmciLCJBY2NvdW50IjoiIiwiU3ViamVjdElEIjoiMTg4NjM5MjM1MDIwMTA5MDE0NiIsIlBob25lIjoiIiwiR3JvdXBJRCI6IjE4ODYzOTIzNTAxOTY4OTU4NDIiLCJQYWdlTmFtZSI6IiIsIk1haWwiOiJobHlhbmdzdGVyQGdtYWlsLmNvbSIsIkNyZWF0ZVRpbWUiOiIyMDI1LTAyLTA0IDE3OjU2OjQ2IiwiVG9rZW5UeXBlIjoxLCJpc3MiOiJtaW5pbWF4In0.iEz6d2cOfb6X4wglslGInvROwF9JoZoEXUBklD5qFLOPDSJUR37Br_S6ssA5_obpoL7LsaSpLfh62CNO6mMfjIFfGzIi78xze8A_oNxIFIxXZ5mritDWw5W6CKzf7LP2PYXctIi2ru2pFTC5UpmvyFGYo4t0t-qV5xdBKH2x34j5IkY2dJPyzKrY0Jjr81tV2VxPgqd8g_cg-yR6kBLUAuvcgkduAuePW8Wiv8ohU1AUiDP-k01aKP-s6q927zdfCPjBOtC2kyUITjcNXWCp_oxpESkILDP1Y7SO6oU-8E1M0xHUh8VOnuqUDyv-FrUki9qMBfwT2JtLrmyW-_Zljw"
    
    # API 參數
    group_id = HAILUO_GROUP_ID
    voice_settings = {
        "voice_id": "moss_audio_068dd108-edd2-11ef-b15b-7285e0393d3d",  # 訓練長
        "speed": 1.0,
        "emotion": "neutral",
        "vol": 1.0,
        "pitch": 0,
    }
    audio_settings = {
        "sample_rate": 32000,
        "bitrate": 128000,
        "format": "mp3",
        "channel": 2
    }
    pronunciation_dict = {
        "tone": ["曝/(pu4)","調整/(tiao2)(zheng3)"]
    }
    
    # 準備請求
    url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={group_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "speech-01-hd",
        "text": "這是一個API測試，用於確認海螺API是否能正確調用。",
        "stream": False,
        "voice_setting": voice_settings,
        "audio_setting": audio_settings,
        "pronunciation_dict": pronunciation_dict
    }
    
    try:
        print("正在調用 Hailuo API...")
        json_data = json.dumps(data, ensure_ascii=False)
        response = requests.post(url, headers=headers, data=json_data, stream=True)
        response.raise_for_status()
        
        response_data = response.json()
        
        if "data" in response_data and "audio" in response_data["data"]:
            hex_audio = response_data["data"]["audio"]
            audio_data = bytes.fromhex(hex_audio)  # 解碼 hex 音訊資料
            
            # 保存音頻文件
            output_file = Path.cwd() / "test_output.mp3"
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            
            print(f"API 調用成功！音頻文件已保存至: {output_file}")
            return True
        else:
            print(f"API 回應缺少音訊資料: {response_data}")
            return False
    
    except Exception as e:
        print(f"API 調用失敗: {e}")
        return False

if __name__ == "__main__":
    test_hailuo_api()