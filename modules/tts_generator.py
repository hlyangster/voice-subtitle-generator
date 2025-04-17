# modules/tts_generator.py

import os
import json
import requests
import zipfile
import tempfile
from pathlib import Path
import time
import shutil

# 導入全局配置
from modules import HAILUO_GROUP_ID, TTS_VOICES, TTS_EMOTIONS, DEFAULT_PRONUNCIATION_DICT, AUDIO_SETTINGS

class TTSGenerationError(Exception):
    """TTS 生成過程中的錯誤"""
    pass

class TTSGenerator:
    """語音生成器類，負責處理文本到語音的轉換"""
    
    # 預設語音設定
    DEFAULT_VOICE_SETTINGS = {
        "voice_id": TTS_VOICES["訓練長"],  # 訓練長
        "speed": 1.0,
        "emotion": "neutral",
        "vol": 1.0,
        "pitch": 0,
    }
    
    # 使用全局音訊格式設定
    DEFAULT_AUDIO_SETTINGS = AUDIO_SETTINGS
    
    # 使用全局預設發音字典
    DEFAULT_PRONUNCIATION_DICT = DEFAULT_PRONUNCIATION_DICT
    
    # 使用全局語音ID映射
    VOICE_ID_MAP = TTS_VOICES
    
    # 使用全局情緒列表
    EMOTIONS = TTS_EMOTIONS
    
    def __init__(self, api_key, group_id=HAILUO_GROUP_ID, output_dir=None):
        """初始化TTS生成器
        
        Args:
            api_key: Hailuo API 密鑰
            group_id: Hailuo Group ID，默認為全局配置的 HAILUO_GROUP_ID
            output_dir: 音頻文件輸出目錄，如果為None則使用臨時目錄
        """
        self.api_key = api_key
        self.group_id = group_id
        
        # 設置輸出目錄
        if output_dir:
            self.output_dir = Path(output_dir)
            os.makedirs(self.output_dir, exist_ok=True)
        else:
            # 使用專案根目錄下的temp文件夾
            project_root = Path(__file__).parent.parent
            self.output_dir = project_root / "temp" / "audio"
            os.makedirs(self.output_dir, exist_ok=True)
    
    def merge_pronunciation_dict(self, custom_entries=None):
        """合併用戶自定義發音詞條與預設字典
        
        Args:
            custom_entries: 用戶自定義的發音詞條列表，格式為 ["字詞/(拼音)", ...]
            
        Returns:
            dict: 合併後的發音字典
        """
        pronunciation_dict = self.DEFAULT_PRONUNCIATION_DICT.copy()
        
        if custom_entries and isinstance(custom_entries, str) and custom_entries.strip():
            # 將用戶輸入分割成單獨的條目
            entries = [entry.strip() for entry in custom_entries.split(',')]
            entries = [entry for entry in entries if entry]  # 過濾空條目
            
            # 合併到默認字典
            if entries:
                pronunciation_dict["tone"] = pronunciation_dict["tone"] + entries
        
        return pronunciation_dict
    
    def generate_speech(self, text, voice_name="訓練長", emotion="neutral", 
                       speed=1.0, custom_pronunciation=None, progress_callback=None):
        """生成語音
        
        Args:
            text: 要轉換為語音的文本，使用 "---" 作為分隔符分隔多個段落
            voice_name: 語音名稱，必須是 VOICE_ID_MAP 中的一個
            emotion: 情緒，必須是 EMOTIONS 中的一個
            speed: 語速，範圍 0.5-2.0
            custom_pronunciation: 用戶自定義發音詞條，格式為字符串，多個詞條用逗號分隔
            progress_callback: 進度回調函數，接收完成百分比作為參數
            
        Returns:
            tuple: (生成的MP3文件列表, 壓縮文件路徑)
        """
        # 檢查參數
        if voice_name not in self.VOICE_ID_MAP:
            raise TTSGenerationError(f"無效的語音名稱: {voice_name}")
        
        if emotion not in self.EMOTIONS:
            raise TTSGenerationError(f"無效的情緒設定: {emotion}")
        
        if not 0.5 <= speed <= 2.0:
            raise TTSGenerationError(f"語速必須在 0.5 到 2.0 之間")
        
        # 應用語音設定
        voice_settings = self.DEFAULT_VOICE_SETTINGS.copy()
        voice_settings["voice_id"] = self.VOICE_ID_MAP[voice_name]
        voice_settings["speed"] = speed
        voice_settings["emotion"] = emotion
        
        # 合併用戶自定義發音字典
        pronunciation_dict = self.merge_pronunciation_dict(custom_pronunciation)
        
        # 清理輸出目錄中的舊文件
        for file in self.output_dir.glob("*.mp3"):
            os.remove(file)
        
        # 分割文本
        segments = text.split("---")
        segments = [seg.strip() for seg in segments if seg.strip()]
        
        # 生成每個段落的語音
        mp3_files = []
        zip_path = self.output_dir / "audio_files.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, segment in enumerate(segments):
                    if progress_callback:
                        progress = int((i / len(segments)) * 100)
                        progress_callback(progress)
                    
                    # 生成MP3文件名
                    mp3_filename = self.output_dir / f"{str(i+1).zfill(2)}.mp3"
                    
                    # 調用API生成語音
                    success = self._text_to_speech(
                        segment, 
                        voice_settings, 
                        self.DEFAULT_AUDIO_SETTINGS, 
                        pronunciation_dict, 
                        mp3_filename
                    )
                    
                    if success:
                        mp3_files.append(mp3_filename)
                        zipf.write(mp3_filename, mp3_filename.name)
                    else:
                        raise TTSGenerationError(f"無法生成語音: 段落 {i+1}")
                
                # 完成
                if progress_callback:
                    progress_callback(100)
            
            # 將Path對象轉換為字符串
            mp3_files_str = [str(f) for f in mp3_files]
            return mp3_files_str, str(zip_path)
        
        except Exception as e:
            # 發生錯誤時清理資源
            if zip_path.exists():
                os.remove(zip_path)
            raise TTSGenerationError(f"語音生成失敗: {str(e)}")
    
    def _text_to_speech(self, text, voice_settings, audio_settings, pronunciation_dict, output_filename):
        """調用 Hailuo API 進行文本到語音的轉換
        
        Args:
            text: 要轉換的文本
            voice_settings: 語音設定
            audio_settings: 音頻設定
            pronunciation_dict: 發音字典
            output_filename: 輸出文件名
            
        Returns:
            bool: 是否成功
        """
        url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "speech-01-hd",
            "text": text,
            "stream": False,
            "voice_setting": voice_settings,
            "audio_setting": audio_settings,
            "pronunciation_dict": pronunciation_dict
        }
        
        try:
            # 嘗試最多3次
            for attempt in range(3):
                try:
                    json_data = json.dumps(data, ensure_ascii=False)
                    response = requests.post(url, headers=headers, data=json_data, stream=True)
                    response.raise_for_status()
                    
                    response_data = response.json()
                    
                    if "data" in response_data and "audio" in response_data["data"]:
                        hex_audio = response_data["data"]["audio"]
                        audio_data = bytes.fromhex(hex_audio)  # 解碼 hex 音訊資料
                        
                        with open(output_filename, 'wb') as f:
                            f.write(audio_data)
                        return True
                    else:
                        print(f"API 回應缺少音訊資料: {response_data}")
                        # 如果不是最後一次嘗試，則等待後重試
                        if attempt < 2:
                            time.sleep(1)
                        continue
                
                except requests.exceptions.RequestException as e:
                    print(f"請求錯誤 (嘗試 {attempt+1}/3): {e}")
                    if attempt < 2:
                        time.sleep(1)
                    continue
            
            # 所有嘗試都失敗
            return False
        
        except Exception as e:
            print(f"文本到語音轉換失敗: {e}")
            return False