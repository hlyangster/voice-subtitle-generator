# modules/tts_generator.py

import os
import json
import requests
import zipfile
import tempfile
from pathlib import Path
import time
import shutil
import logging

# 導入全局配置
from modules import HAILUO_GROUP_ID, TTS_VOICES, TTS_EMOTIONS, DEFAULT_PRONUNCIATION_DICT, AUDIO_SETTINGS
logging.basicConfig(
    filename='tts_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        """生成語音"""
        # 首先測試 API 連接
        print("開始 API 連接測試...")
        if not self.test_api_connection():
            raise TTSGenerationError("無法連接到 Hailuo API，請檢查網絡和 API 密鑰")
        
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
        
        # 清理輸出目錄中的舊文件
        for file in self.output_dir.glob("*.mp3"):
            os.remove(file)
        
        # 分割文本
        segments = text.split("---")
        segments = [seg.strip() for seg in segments if seg.strip()]
        
        # 輸出段落資訊以便調試
        print(f"文本被分割為 {len(segments)} 個段落")
        for i, segment in enumerate(segments):
            print(f"段落 {i+1} ({len(segment)} 字符): {segment[:50]}...")
        
        # 生成每個段落的語音
        mp3_files = []
        zip_path = self.output_dir / "audio_files.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, segment in enumerate(segments):
                    if progress_callback:
                        progress = int((i / len(segments)) * 100)
                        progress_callback(progress)
                    
                    print(f"\n開始處理段落 {i+1}/{len(segments)}")
                    
                    # 生成MP3文件名
                    mp3_filename = self.output_dir / f"{str(i+1).zfill(2)}.mp3"
                    
                    # 調用API生成語音
                    print(f"呼叫 API 生成語音...")
                    success = self.call_tts_api(
                        segment, 
                        voice_settings, 
                        self.DEFAULT_AUDIO_SETTINGS, 
                        {}, # 空字典，已停用發音字典功能
                        mp3_filename
                    )
                    
                    if success:
                        print(f"段落 {i+1} 語音生成成功")
                        mp3_files.append(mp3_filename)
                        zipf.write(mp3_filename, mp3_filename.name)
                    else:
                        # 嘗試使用更簡短的文本
                        if len(segment) > 100:
                            short_segment = segment[:100] + "..."
                            print(f"嘗試使用縮短的段落文本...")
                            success = self.call_tts_api(
                                short_segment,
                                voice_settings,
                                self.DEFAULT_AUDIO_SETTINGS,
                                {},
                                mp3_filename
                            )
                            if success:
                                print(f"使用縮短文本成功生成語音")
                                mp3_files.append(mp3_filename)
                                zipf.write(mp3_filename, mp3_filename.name)
                                continue
                        
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
    
    def call_tts_api(self, text, voice_settings, audio_settings, pronunciation_dict, output_filename):
        """調用 Hailuo API 進行文本到語音的轉換"""
        url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.api_key}"
        }
    
        # 準備請求數據（已停用發音字典）
        data = {
        "model": "speech-01-hd",
        "text": text,
        "stream": False,
        "voice_setting": voice_settings,
        "audio_setting": audio_settings
        }
    
        # 輸出詳細請求資訊以供調試
        print(f"請求 URL: {url}")
        print(f"請求標頭: {headers}")
        print(f"請求資料: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
        try:
            # 發送請求
            response = requests.post(url, headers=headers, json=data)
            
            # 詳細記錄響應
            print(f"狀態碼: {response.status_code}")
            print(f"響應標頭: {response.headers}")
            
            # 嘗試獲取並記錄響應內容
            try:
                response_data = response.json()
                print(f"響應資料: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"無法解析 JSON 響應: {response.text}")
            
            # 檢查狀態碼
            response.raise_for_status()
            
            # 確認存在適當的響應結構
            if "data" in response_data and "audio" in response_data["data"]:
                hex_audio = response_data["data"]["audio"]
                audio_data = bytes.fromhex(hex_audio)
                
                with open(output_filename, 'wb') as f:
                    f.write(audio_data)
                return True
            else:
                print(f"API 回應缺少音訊資料: {response_data}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"錯誤響應: {e.response.text}")
            return False
        except Exception as e:
            print(f"文本到語音轉換失敗: {e}")
            import traceback
            print(traceback.format_exc())
            return False    
            
    def test_api_connection(self):
        """測試 API 連接，返回是否可連接"""
        url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 最簡單的測試請求
        data = {
            "model": "speech-01-hd",
            "text": "測試連接",
            "stream": False,
            "voice_setting": self.DEFAULT_VOICE_SETTINGS,
            "audio_setting": self.DEFAULT_AUDIO_SETTINGS
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"測試連接狀態碼: {response.status_code}")
            print(f"測試連接響應: {response.text}")
            
            return response.status_code == 200
        except Exception as e:
            print(f"API 連接測試失敗: {e}")
            return False    
    
    def _text_to_speech(self, text, voice_settings, audio_settings, pronunciation_dict, output_filename):
        """調用 Hailuo API 進行文本到語音的轉換"""
        url = f"https://api.minimaxi.chat/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 創建一個不含發音字典的請求版本進行測試
        basic_data = {
            "model": "speech-01-hd",
            "text": text,
            "stream": False,
            "voice_setting": voice_settings,
            "audio_setting": audio_settings
        }
        
        # 完整版本（包含發音字典）
        full_data = basic_data.copy()
        full_data["pronunciation_dict"] = pronunciation_dict
        
        try:
            # 首先嘗試完整版本
            try:
                json_data = json.dumps(full_data, ensure_ascii=False)
                print(f"完整數據 JSON 長度：{len(json_data)}")
                
                # 測試 JSON 是否有效
                json.loads(json_data)
                
                data_to_use = full_data
                print("使用完整數據（含發音字典）")
            except json.JSONDecodeError as e:
                print(f"完整數據 JSON 序列化錯誤: {e}")
                print(f"嘗試使用不含發音字典的基礎數據")
                
                # 改用不含發音字典的基礎版本
                json_data = json.dumps(basic_data, ensure_ascii=False)
                data_to_use = basic_data
            
            # 使用確認有效的數據發送請求
            final_json = json.dumps(data_to_use, ensure_ascii=False)
            response = requests.post(url, headers=headers, data=final_json, stream=True)
            response.raise_for_status()
            
            response_data = response.json()
            
            if "data" in response_data and "audio" in response_data["data"]:
                hex_audio = response_data["data"]["audio"]
                audio_data = bytes.fromhex(hex_audio)
                
                with open(output_filename, 'wb') as f:
                    f.write(audio_data)
                return True
            else:
                print(f"API 回應缺少音訊資料: {response_data}")
                return False
        
        except requests.exceptions.RequestException as e:
            print(f"請求錯誤: {e}")
            return False
        except Exception as e:
            print(f"文本到語音轉換失敗: {e}")
            return False
    
    
